"""
Train a baseline irrigation-priority classifier (SURROGATE-LABEL PROTOTYPE).

IMPORTANT — READ BEFORE USING THE OUTPUT
  The target labels come from the FAO-56 water balance and rule-based
  advisory logic, NOT from field observations. This model can at best learn
  to imitate those rules from weather/crop/remote-sensing features. It is
  not a field-validated AI model and must not be presented as one.

LEAKAGE CONTROL
  target_irrigation_priority is a deterministic function of the FAO-56
  water_stress_level, which is a threshold on Ks, which is computed from
  root-zone depletion. Those columns (and TAW/RAW, which define the
  thresholds) are therefore excluded so the model has to predict from
  weather, crop stage/Kc, ET, irrigation history and remote-sensing
  features instead of reading the answer.

INPUT   data/processed/muthukur_ml_training_dataset.csv
OUTPUTS models/irrigation_priority_model.joblib
        data/processed/muthukur_ml_model_metrics.json
        data/processed/muthukur_ml_feature_importance.csv

      python src/ml/train_irrigation_priority_model.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_config  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

log = get_logger(__name__)

TARGET = "target_irrigation_priority"
MIN_ROWS = 50
TRAIN_FRACTION = 0.8

LABEL_WARNING = (
    "Labels are surrogate labels derived from FAO-56/rule-based advisory logic, "
    "NOT field-validated observations. This is a surrogate-label ML prototype, "
    "not a validated AI model."
)

EXCLUDED_COLUMNS = {
    "date",
    # targets
    "target_irrigation_priority",
    "target_water_stress_level",
    "target_irrigation_needed_binary",
    # direct determinants of the label (leakage)
    "water_stress_level", "ks", "root_zone_depletion_mm", "taw_mm", "raw_mm",
    # advisory outputs / free text / raw observation dates, if ever present
    "advisory_action", "advisory_priority", "advisory_reason", "advisory_limitations",
    "data_source", "sentinel2_date", "sentinel1_date",
    "notes", "source", "method",
}


def split_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return (X, y). X drops targets, leakage columns, dates and empty columns."""
    cols = [
        c for c in df.columns
        if c not in EXCLUDED_COLUMNS
        and not c.startswith("target_")
        and not c.endswith("_date")
        and df[c].notna().any()
    ]
    return df[cols].copy(), df[TARGET].copy()


def chronological_split(df: pd.DataFrame, train_fraction: float = TRAIN_FRACTION):
    """Sort by date and split first train_fraction / last remainder (no shuffling)."""
    ordered = df.assign(_d=pd.to_datetime(df["date"])).sort_values("_d").drop(columns="_d")
    ordered = ordered.reset_index(drop=True)
    cut = int(len(ordered) * train_fraction)
    return ordered.iloc[:cut].copy(), ordered.iloc[cut:].copy()


def build_pipeline(X: pd.DataFrame) -> Pipeline:
    numeric = X.select_dtypes(include="number").columns.tolist()
    categorical = [c for c in X.columns if c not in numeric]
    pre = ColumnTransformer(
        [
            ("num", SimpleImputer(strategy="median"), numeric),
            (
                "cat",
                Pipeline([
                    ("impute", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore")),
                ]),
                categorical,
            ),
        ],
        verbose_feature_names_out=False,
    )
    clf = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)
    return Pipeline([("preprocess", pre), ("model", clf)])


def feature_importance_frame(pipeline: Pipeline) -> pd.DataFrame:
    names = pipeline.named_steps["preprocess"].get_feature_names_out()
    imp = pipeline.named_steps["model"].feature_importances_
    return (
        pd.DataFrame({"feature": names, "importance": imp})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def train_and_evaluate(df: pd.DataFrame) -> tuple[Pipeline, dict, pd.DataFrame]:
    """Train on the first 80% (chronological), evaluate on the last 20%."""
    df = df.dropna(subset=[TARGET])
    train_df, test_df = chronological_split(df)
    X_train, y_train = split_features_target(train_df)
    X_test, y_test = test_df[X_train.columns], test_df[TARGET]

    pipe = build_pipeline(X_train)
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)

    labels = sorted(set(y_train) | set(y_test))
    # Macro averages only cover classes that actually occur in the test window;
    # absent classes would otherwise score 0 and distort the macro metrics.
    present = sorted(set(y_test))
    metrics = {
        "model_type": "RandomForestClassifier",
        "label_type": "surrogate_rule_based",
        "target": TARGET,
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_date_range": [str(train_df["date"].iloc[0]), str(train_df["date"].iloc[-1])],
        "test_date_range": [str(test_df["date"].iloc[0]), str(test_df["date"].iloc[-1])],
        "feature_count": int(X_train.shape[1]),
        "features": X_train.columns.tolist(),
        "target_distribution": {
            "train": y_train.value_counts().to_dict(),
            "test": y_test.value_counts().to_dict(),
        },
        "accuracy": float(accuracy_score(y_test, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, pred)),
        "precision_macro": float(precision_score(y_test, pred, labels=present, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_test, pred, labels=present, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_test, pred, labels=present, average="macro", zero_division=0)),
        "classification_report": classification_report(
            y_test, pred, labels=labels, output_dict=True, zero_division=0
        ),
        "confusion_matrix": {
            "labels": labels,
            "matrix": confusion_matrix(y_test, pred, labels=labels).tolist(),
        },
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "macro_average_classes": present,
        "warning": LABEL_WARNING,
    }
    if len(present) < len(labels):
        metrics["test_set_note"] = (
            f"Test window contains only {present}; metrics describe that window "
            "only and say little about the other classes."
        )
    return pipe, metrics, feature_importance_frame(pipe)


def train_irrigation_priority_model(config=None) -> bool:
    """Train and save artifacts. Returns False (without raising) if skipped."""
    config = config or get_config()
    data_path = config.path("ml_training_dataset_csv")
    model_path = config.path("irrigation_priority_model_path")
    metrics_path = config.path("ml_model_metrics_json")
    importance_path = config.path("ml_feature_importance_csv")

    if not data_path.exists():
        print(f"\nML training dataset not found: {data_path}\nSkipping model training.")
        log.warning("ML model training skipped: dataset missing (%s)", data_path)
        return False

    df = pd.read_csv(data_path)
    if TARGET not in df.columns or "date" not in df.columns:
        print(f"\nML training dataset is missing 'date' or '{TARGET}'. Skipping model training.")
        log.warning("ML model training skipped: required columns missing")
        return False

    labelled = int(df[TARGET].notna().sum())
    if labelled < MIN_ROWS:
        print(f"\nOnly {labelled} labelled rows (need at least {MIN_ROWS}). Skipping model training.")
        log.warning("ML model training skipped: %d labelled rows < %d", labelled, MIN_ROWS)
        return False
    if df[TARGET].nunique() < 2:
        print("\nTarget has a single class; skipping model training.")
        log.warning("ML model training skipped: single-class target")
        return False

    pipe, metrics, importance = train_and_evaluate(df)

    for p in (model_path, metrics_path, importance_path):
        p.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2, default=_json_default), encoding="utf-8")
    importance.to_csv(importance_path, index=False)

    log.info(
        "Trained surrogate-label priority model: train=%d test=%d acc=%.3f bal_acc=%.3f",
        metrics["train_rows"], metrics["test_rows"],
        metrics["accuracy"], metrics["balanced_accuracy"],
    )
    print()
    print(f">>> Model saved to:        {model_path}")
    print(f">>> Metrics saved to:      {metrics_path}")
    print(f">>> Importances saved to:  {importance_path}")
    print(f">>> Train/test rows: {metrics['train_rows']}/{metrics['test_rows']}   "
          f"features: {metrics['feature_count']}")
    print(f">>> Accuracy {metrics['accuracy']:.3f}   balanced accuracy "
          f"{metrics['balanced_accuracy']:.3f}   macro F1 {metrics['f1_macro']:.3f}")
    print(f">>> WARNING: {LABEL_WARNING}")
    return True


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return str(o)


if __name__ == "__main__":
    sys.exit(0 if train_irrigation_priority_model() else 1)
