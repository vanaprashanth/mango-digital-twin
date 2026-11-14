"""
Expanding-window chronological backtest for the baseline irrigation-priority
classifier (SURROGATE-LABEL PROTOTYPE).

WHAT THIS EVALUATES
  The same RandomForest pipeline, feature selection and leakage exclusions as
  src/ml/train_irrigation_priority_model.py (they are imported, not copied),
  scored over several chronological test windows instead of a single 80/20
  split. It does not change the trained model artifact or the daily pipeline.

HOW THE FOLDS WORK
  Sort by date. The first `initial_train_fraction` of rows is the initial
  training block; the remaining rows are cut into `n_folds` consecutive,
  non-overlapping test blocks. Fold k trains on EVERYTHING before its test
  block (expanding window) and is scored on that block only. Nothing is
  shuffled. A fresh pipeline is built and fitted per fold, so the imputer
  medians / most-frequent values / one-hot categories and the feature column
  selection are all computed from that fold's training rows only.

HOW TO READ THE RESULTS (important)
  - Labels are SURROGATE labels derived from FAO-56 / rule-based advisory
    logic, NOT field observations. A high score means the model reproduces
    those rules from weather/crop/remote-sensing features. It is NOT
    evidence that the model improves irrigation decisions or agrees with
    what a farmer or sensor would observe.
  - Test blocks often contain only one or two classes. Two kinds of macro
    metrics are therefore reported separately:
      * fixed-class   : averaged over ALL classes in the dataset (a class
                        absent from the test block contributes 0, so these
                        are pessimistic when classes are missing)
      * present-class : averaged only over classes that occur in the test
                        block (optimistic when only one class is present)
    Accuracy and balanced accuracy are reported alongside; the absent
    classes of every fold are listed explicitly.
  - A majority-class baseline (predict the most frequent TRAINING class) is
    scored on identical folds. Beating it is a minimum bar, not a result.

OUTPUTS (generated; not committed by default)
  data/processed/muthukur_ml_backtest_folds.csv        one row per fold
  data/processed/muthukur_ml_backtest_predictions.csv  per-date predictions
  data/processed/muthukur_ml_backtest_summary.json     aggregate + fold detail

      python src/ml/backtest_irrigation_priority_model.py
"""

from __future__ import annotations

import json
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ml.train_irrigation_priority_model import (  # noqa: E402
    LABEL_WARNING,
    TARGET,
    build_pipeline,
    split_features_target,
)
from src.utils.config import get_config  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

log = get_logger(__name__)

DEFAULT_N_FOLDS = 4
DEFAULT_INITIAL_TRAIN_FRACTION = 0.5
MIN_TRAIN_ROWS = 30
MIN_TEST_ROWS = 5

INTERPRETATION_NOTE = (
    "Targets are surrogate labels derived from FAO-56/rule-based logic, not field "
    "observations. These scores measure how well the classifier reproduces those "
    "rules on later dates; they do not demonstrate ML improvement over the rules, "
    "agreement with real irrigation needs, or field validation. Macro metrics are "
    "given both over all classes (fixed-class) and over classes present in each test "
    "block (present-class); compare against the majority-class baseline, and treat "
    "folds whose test block has a single class as weak evidence."
)

_METRIC_KEYS = [
    "accuracy",
    "balanced_accuracy",
    "precision_macro_fixed", "recall_macro_fixed", "f1_macro_fixed",
    "precision_macro_present", "recall_macro_present", "f1_macro_present",
]


# ---------------------------------------------------------------------------
# Fold construction
# ---------------------------------------------------------------------------

def make_expanding_folds(
    n_rows: int,
    n_folds: int = DEFAULT_N_FOLDS,
    initial_train_fraction: float = DEFAULT_INITIAL_TRAIN_FRACTION,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """
    Return (train_idx, test_idx) positional index pairs for a date-sorted frame.
    Test blocks are consecutive and non-overlapping; each train set is every
    row before its test block. Returns [] if the data cannot support the
    requested folds (too few train/test rows).
    """
    initial = int(n_rows * initial_train_fraction)
    remaining = n_rows - initial
    if n_folds < 1 or initial < MIN_TRAIN_ROWS or remaining < n_folds * MIN_TEST_ROWS:
        return []
    bounds = np.linspace(initial, n_rows, n_folds + 1).round().astype(int)
    folds = []
    for k in range(n_folds):
        start, stop = bounds[k], bounds[k + 1]
        if stop - start < MIN_TEST_ROWS:
            return []
        folds.append((np.arange(0, start), np.arange(start, stop)))
    return folds


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_metrics(y_true, y_pred, all_classes: list[str]) -> dict:
    """Accuracy, balanced accuracy, fixed-class and present-class macro metrics."""
    with warnings.catch_warnings():
        # sklearn warns when predictions include classes absent from y_true;
        # that situation is expected and reported explicitly elsewhere.
        warnings.simplefilter("ignore", UserWarning)
        present = sorted(set(y_true))
        out = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            # sklearn balanced accuracy averages recall over classes present in y_true
            "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        }
        for suffix, labels in (("fixed", all_classes), ("present", present)):
            out[f"precision_macro_{suffix}"] = float(
                precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0))
            out[f"recall_macro_{suffix}"] = float(
                recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0))
            out[f"f1_macro_{suffix}"] = float(
                f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0))
    return out


def _counts(series: pd.Series, classes: list[str]) -> dict[str, int]:
    vc = series.value_counts()
    return {c: int(vc.get(c, 0)) for c in classes}


# ---------------------------------------------------------------------------
# One fold
# ---------------------------------------------------------------------------

def evaluate_fold(
    fold_id: int,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    all_classes: list[str],
) -> tuple[dict, pd.DataFrame, Pipeline]:
    """
    Fit a fresh pipeline on train_df only, predict test_df, and score both the
    model and the majority-class baseline. Returns (result, predictions, pipeline).
    """
    X_train, y_train = split_features_target(train_df)  # columns chosen from train only
    X_test, y_test = test_df[X_train.columns], test_df[TARGET]

    pipe = build_pipeline(X_train)
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)

    majority_class = y_train.value_counts().idxmax()
    base_pred = np.full(len(y_test), majority_class, dtype=object)

    model_metrics = compute_metrics(y_test, pred, all_classes)
    base_metrics = compute_metrics(y_test, base_pred, all_classes)

    cm_labels = list(all_classes)
    result = {
        "fold": fold_id,
        "train_start": str(train_df["date"].iloc[0]),
        "train_end": str(train_df["date"].iloc[-1]),
        "test_start": str(test_df["date"].iloc[0]),
        "test_end": str(test_df["date"].iloc[-1]),
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "feature_count": int(X_train.shape[1]),
        "train_class_distribution": _counts(y_train, all_classes),
        "test_class_distribution": _counts(y_test, all_classes),
        "classes_absent_from_test": [c for c in all_classes if c not in set(y_test)],
        "classes_absent_from_train": [c for c in all_classes if c not in set(y_train)],
        "majority_class_baseline_prediction": str(majority_class),
        "model": model_metrics,
        "baseline": base_metrics,
        "confusion_matrix": {
            "labels": cm_labels,
            "matrix": confusion_matrix(y_test, pred, labels=cm_labels).tolist(),
        },
        "baseline_confusion_matrix": {
            "labels": cm_labels,
            "matrix": confusion_matrix(y_test, base_pred, labels=cm_labels).tolist(),
        },
    }
    preds = pd.DataFrame({
        "fold": fold_id,
        "date": test_df["date"].to_numpy(),
        "actual": y_test.to_numpy(),
        "predicted": pred,
        "baseline_predicted": base_pred,
    })
    return result, preds, pipe


# ---------------------------------------------------------------------------
# Whole backtest
# ---------------------------------------------------------------------------

def _mean(values: list[float]) -> float | None:
    return float(np.mean(values)) if values else None


def run_backtest(
    df: pd.DataFrame,
    n_folds: int = DEFAULT_N_FOLDS,
    initial_train_fraction: float = DEFAULT_INITIAL_TRAIN_FRACTION,
) -> tuple[dict, pd.DataFrame] | None:
    """
    Run the expanding-window backtest. Returns (summary, predictions) or None
    if the data cannot support the requested folds.
    """
    if "date" not in df.columns or TARGET not in df.columns:
        return None
    data = df.dropna(subset=[TARGET]).copy()
    data["_d"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["_d"]).sort_values("_d").drop(columns="_d").reset_index(drop=True)

    idx_pairs = make_expanding_folds(len(data), n_folds, initial_train_fraction)
    if not idx_pairs:
        return None

    all_classes = sorted(data[TARGET].unique())
    fold_results, pred_frames = [], []
    for k, (tr, te) in enumerate(idx_pairs, start=1):
        train_df, test_df = data.iloc[tr], data.iloc[te]
        if train_df[TARGET].nunique() < 1 or test_df.empty:
            continue
        result, preds, _ = evaluate_fold(k, train_df, test_df, all_classes)
        fold_results.append(result)
        pred_frames.append(preds)
    if not fold_results:
        return None

    predictions = pd.concat(pred_frames, ignore_index=True)

    def agg(which: str) -> dict:
        return {key: _mean([f[which][key] for f in fold_results]) for key in _METRIC_KEYS}

    pooled_cm = np.sum([np.array(f["confusion_matrix"]["matrix"]) for f in fold_results], axis=0)
    pooled_base_cm = np.sum(
        [np.array(f["baseline_confusion_matrix"]["matrix"]) for f in fold_results], axis=0)
    model_mean, base_mean = agg("model"), agg("baseline")

    summary = {
        "label_type": "surrogate_rule_based",
        "model_type": "RandomForestClassifier",
        "target": TARGET,
        "evaluation": "expanding_window_chronological_backtest",
        "n_folds": len(fold_results),
        "initial_train_fraction": initial_train_fraction,
        "classes": all_classes,
        "total_rows": int(len(data)),
        "date_range": [str(data["date"].iloc[0]), str(data["date"].iloc[-1])],
        "folds_with_absent_test_classes": sum(
            1 for f in fold_results if f["classes_absent_from_test"]),
        "folds_with_single_class_test": sum(
            1 for f in fold_results
            if sum(v > 0 for v in f["test_class_distribution"].values()) == 1),
        "mean_model_metrics": model_mean,
        "mean_baseline_metrics": base_mean,
        "mean_accuracy_minus_baseline": (
            model_mean["accuracy"] - base_mean["accuracy"]
            if model_mean["accuracy"] is not None else None),
        "mean_balanced_accuracy_minus_baseline": (
            model_mean["balanced_accuracy"] - base_mean["balanced_accuracy"]
            if model_mean["balanced_accuracy"] is not None else None),
        "pooled_confusion_matrix": {"labels": all_classes, "matrix": pooled_cm.tolist()},
        "pooled_baseline_confusion_matrix": {
            "labels": all_classes, "matrix": pooled_base_cm.tolist()},
        "folds": fold_results,
        "interpretation_note": INTERPRETATION_NOTE,
        "warning": LABEL_WARNING,
        "run_at": datetime.now().isoformat(timespec="seconds"),
    }
    return summary, predictions


def fold_results_frame(summary: dict) -> pd.DataFrame:
    """Flatten per-fold results into one CSV-friendly row per fold."""
    rows = []
    for f in summary["folds"]:
        row = {
            k: f[k] for k in (
                "fold", "train_start", "train_end", "test_start", "test_end",
                "train_rows", "test_rows", "feature_count",
                "majority_class_baseline_prediction",
            )
        }
        row["train_class_distribution"] = json.dumps(f["train_class_distribution"])
        row["test_class_distribution"] = json.dumps(f["test_class_distribution"])
        row["classes_absent_from_test"] = ";".join(f["classes_absent_from_test"])
        for who in ("model", "baseline"):
            for key in _METRIC_KEYS:
                row[f"{who}_{key}"] = f[who][key]
        rows.append(row)
    return pd.DataFrame(rows)


def backtest_irrigation_priority_model(config=None) -> bool:
    """Run the backtest against the ML dataset and save outputs. False if skipped."""
    config = config or get_config()
    data_path = config.path("ml_training_dataset_csv")
    folds_path = config.path("ml_backtest_folds_csv")
    preds_path = config.path("ml_backtest_predictions_csv")
    summary_path = config.path("ml_backtest_summary_json")

    if not data_path.exists():
        print(f"\nML training dataset not found: {data_path}\nSkipping backtest.")
        log.warning("ML backtest skipped: dataset missing (%s)", data_path)
        return False

    df = pd.read_csv(data_path)
    out = run_backtest(df)
    if out is None:
        print("\nNot enough labelled, dated rows for the expanding-window backtest. Skipping.")
        log.warning("ML backtest skipped: insufficient data (%d rows)", len(df))
        return False
    summary, predictions = out

    for p in (folds_path, preds_path, summary_path):
        p.parent.mkdir(parents=True, exist_ok=True)
    fold_results_frame(summary).to_csv(folds_path, index=False)
    predictions.to_csv(preds_path, index=False)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    log.info("ML backtest: %d folds over %d rows", summary["n_folds"], summary["total_rows"])
    _print_report(summary)
    print(f">>> Fold results:  {folds_path}")
    print(f">>> Predictions:   {preds_path}")
    print(f">>> Summary JSON:  {summary_path}")
    return True


def _print_report(summary: dict) -> None:
    print()
    print(f">>> Expanding-window backtest: {summary['n_folds']} folds, "
          f"{summary['total_rows']} rows, classes={summary['classes']}")
    for f in summary["folds"]:
        m, b = f["model"], f["baseline"]
        print(f">>> Fold {f['fold']}: train {f['train_start']}..{f['train_end']} ({f['train_rows']}) | "
              f"test {f['test_start']}..{f['test_end']} ({f['test_rows']})")
        print(f">>>    test support {f['test_class_distribution']}  absent={f['classes_absent_from_test']}")
        print(f">>>    model acc={m['accuracy']:.3f} bal_acc={m['balanced_accuracy']:.3f} "
              f"F1 fixed={m['f1_macro_fixed']:.3f} present={m['f1_macro_present']:.3f}")
        print(f">>>    baseline('{f['majority_class_baseline_prediction']}') acc={b['accuracy']:.3f} "
              f"bal_acc={b['balanced_accuracy']:.3f} F1 fixed={b['f1_macro_fixed']:.3f} "
              f"present={b['f1_macro_present']:.3f}")
    print(f">>> NOTE: {INTERPRETATION_NOTE}")


if __name__ == "__main__":
    sys.exit(0 if backtest_irrigation_priority_model() else 1)
