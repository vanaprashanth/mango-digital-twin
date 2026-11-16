"""
Medium-class improvement EXPERIMENT for the surrogate-label irrigation-priority Random Forest.
(RESEARCH ONLY. Not used by the dashboard, the pipeline or the GCS job.)

QUESTION
  Why is Medium recall 0% on the held-out window, and does any cheap change (class weights, or removing
  the growth-stage feature) recover it without sacrificing High-priority recall?

WHAT IS ISOLATED
  * Production code is imported READ-ONLY (feature exclusions, preprocessing pipeline, chronological split,
    expanding-fold helper). Nothing in src/ml/train_irrigation_priority_model.py is modified.
  * Results go to data/experiments/medium_class/ only. Production metrics, the model binary and the feature
    importances are never read for writing, and ``write_results`` refuses production output locations.

PROTOCOL (no test-set selection, no time leakage)
  1. The production chronological 80/20 split is reproduced. The test window is not touched until step 4.
  2. Candidate configurations (feature set x class-weight scheme) are scored ONLY by expanding-window
     validation folds inside the training window: every validation block is strictly later than its training
     rows. No random CV, no resampling across time.
  3. Selection rule (fixed in advance, see ``select``):
       - score = pooled out-of-fold macro-F1 over the classes present in the pooled validation rows;
       - a candidate must keep pooled validation High recall >= baseline's - HIGH_RECALL_TOLERANCE;
       - it must beat the baseline by at least MIN_IMPROVEMENT, otherwise the baseline stays.
     Missing classes in each fold's training and validation rows are detected and reported.
  4. The frozen selection is evaluated ONCE on the test window and reported next to the baseline.

LABELS ARE SURROGATE (FAO-56 rules), not field observations. Nothing here is field validation.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.utils.class_weight import compute_class_weight

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ml.backtest_irrigation_priority_model import make_expanding_folds  # noqa: E402
from src.ml.train_irrigation_priority_model import (  # noqa: E402
    EXCLUDED_COLUMNS,
    TARGET,
    build_pipeline,
    chronological_split,
    split_features_target,
)
from src.utils.config import get_config  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

log = get_logger(__name__)

CLASSES = ["Low", "Medium", "High"]
SEED = 42
N_FOLDS = 4
INITIAL_TRAIN_FRACTION = 0.5
HIGH_RECALL_TOLERANCE = 0.05
MIN_IMPROVEMENT = 0.01

EXPERIMENT_DIR = PROJECT_ROOT / "data" / "experiments" / "medium_class"
RESULTS_JSON = "medium_class_experiment_results.json"
VALIDATION_CSV = "medium_class_validation_scores.csv"
FOLDS_CSV = "medium_class_validation_folds.csv"

LABEL_WARNING = ("Surrogate labels from FAO-56/rule-based logic, not field observations. Experimental results; "
                 "not field validation and not adopted by the dashboard.")

# Columns removed IN ADDITION to the production exclusions.
FEATURE_SETS: dict[str, tuple[str, ...]] = {
    "all_production_features": (),
    "no_mango_stage": ("mango_stage",),
    # Diagnostic: stage_kc / interpolated_kc / kc are close functions of the stage calendar, so dropping only
    # the label can leave the stage information in through them.
    "no_stage_family_diagnostic": ("mango_stage", "stage_kc", "interpolated_kc", "kc"),
}
WEIGHT_SCHEMES = ("balanced", "none", "balanced_subsample", "balanced_medium_x2", "balanced_medium_x4")
BASELINE = ("all_production_features", "balanced")      # exactly what production trains
ARMS = {
    "baseline": None,                                    # fixed: BASELINE
    "class_weights": "all_production_features",
    "no_mango_stage": "no_mango_stage",
    "no_stage_family_diagnostic": "no_stage_family_diagnostic",
}


# ---------------------------------------------------------------------------
# Data, features, models
# ---------------------------------------------------------------------------

def sorted_labelled(df: pd.DataFrame) -> pd.DataFrame:
    out = df.dropna(subset=[TARGET]).copy()
    out["_d"] = pd.to_datetime(out["date"])
    return out.sort_values("_d", kind="stable").drop(columns="_d").reset_index(drop=True)


def feature_frame(train_df: pd.DataFrame, feature_set: str) -> tuple[pd.DataFrame, pd.Series]:
    """Production feature selection (leakage exclusions) followed by the experiment's extra drops."""
    X, y = split_features_target(train_df)
    return X.drop(columns=[c for c in FEATURE_SETS[feature_set] if c in X.columns]), y


def class_weight_for(scheme: str, y: pd.Series):
    if scheme == "none":
        return None
    if scheme in ("balanced", "balanced_subsample"):
        return scheme
    if scheme.startswith("balanced_medium_x"):
        factor = float(scheme.rsplit("x", 1)[1])
        classes = np.array(sorted(y.unique()))
        weights = dict(zip(classes, compute_class_weight("balanced", classes=classes, y=y)))
        if "Medium" in weights:
            weights["Medium"] *= factor
        return {k: float(v) for k, v in weights.items()}
    raise ValueError(f"unknown weight scheme {scheme!r}")


def fit_configuration(train_df: pd.DataFrame, feature_set: str, scheme: str):
    """Fit one configuration on ``train_df`` only. Returns (pipeline, feature_columns)."""
    X, y = feature_frame(train_df, feature_set)
    pipe = build_pipeline(X)
    pipe.set_params(model__class_weight=class_weight_for(scheme, y), model__random_state=SEED, model__n_jobs=1)
    pipe.fit(X, y)
    return pipe, list(X.columns)


# ---------------------------------------------------------------------------
# Metrics (explicit about undefined values)
# ---------------------------------------------------------------------------

def confusion(y_true, y_pred, classes=CLASSES) -> list[list[int]]:
    idx = {c: i for i, c in enumerate(classes)}
    m = np.zeros((len(classes), len(classes)), dtype=int)
    for t, p in zip(y_true, y_pred):
        if t in idx and p in idx:
            m[idx[t], idx[p]] += 1
    return m.tolist()


def score(y_true, y_pred, classes=CLASSES) -> dict:
    """Confusion matrix (rows=actual, cols=predicted), class-wise P/R/F1, balanced accuracy, macro F1.

    Precision is None when a class was never predicted; recall/F1 are None when it never occurs.
    Balanced accuracy and ``f1_macro_present`` average over classes that occur in ``y_true``.
    """
    y_true, y_pred = np.asarray(y_true, dtype=object), np.asarray(y_pred, dtype=object)
    cm = np.array(confusion(y_true, y_pred, classes))
    per = {}
    for i, c in enumerate(classes):
        support, predicted, tp = int(cm[i].sum()), int(cm[:, i].sum()), int(cm[i, i])
        precision = tp / predicted if predicted else None
        recall = tp / support if support else None
        if support == 0:
            f1 = None
        else:
            f1 = 0.0 if not precision or not recall else 2 * precision * recall / (precision + recall)
        per[c] = {"support": support, "predicted": predicted, "true_positive": tp,
                  "precision": precision, "recall": recall, "f1": f1}
    present = [c for c in classes if per[c]["support"] > 0]
    n = int(cm.sum())
    return {
        "rows": n,
        "confusion_matrix": {"labels": list(classes), "rows_are": "actual", "matrix": cm.tolist()},
        "per_class": per,
        "classes_present": present,
        "classes_missing": [c for c in classes if per[c]["support"] == 0],
        "accuracy": float(np.trace(cm) / n) if n else None,
        "balanced_accuracy": float(np.mean([per[c]["recall"] for c in present])) if present else None,
        "f1_macro_present": float(np.mean([per[c]["f1"] for c in present])) if present else None,
        "f1_macro_fixed": float(np.mean([per[c]["f1"] or 0.0 for c in classes])),
        "high_recall": per["High"]["recall"],
        "medium_recall": per["Medium"]["recall"],
    }


# ---------------------------------------------------------------------------
# Chronological validation inside the training window
# ---------------------------------------------------------------------------

def class_counts(series: pd.Series) -> dict[str, int]:
    vc = series.value_counts()
    return {c: int(vc.get(c, 0)) for c in CLASSES}


def validation_folds(train_df: pd.DataFrame, n_folds: int = N_FOLDS,
                     initial_fraction: float = INITIAL_TRAIN_FRACTION) -> list[dict]:
    """Expanding-window folds over the date-sorted TRAINING window, with class presence reported."""
    ordered = sorted_labelled(train_df)
    out = []
    for k, (tr_idx, va_idx) in enumerate(make_expanding_folds(len(ordered), n_folds, initial_fraction), start=1):
        tr, va = ordered.iloc[tr_idx], ordered.iloc[va_idx]
        ct, cv = class_counts(tr[TARGET]), class_counts(va[TARGET])
        out.append({
            "fold": k, "train": tr, "validation": va,
            "train_rows": len(tr), "validation_rows": len(va),
            "train_end": str(tr["date"].iloc[-1]), "validation_start": str(va["date"].iloc[0]),
            "validation_end": str(va["date"].iloc[-1]),
            "train_class_counts": ct, "validation_class_counts": cv,
            "classes_missing_in_train": [c for c in CLASSES if ct[c] == 0],
            "classes_missing_in_validation": [c for c in CLASSES if cv[c] == 0],
        })
    return out


def fold_report(f: dict) -> dict:
    return {k: v for k, v in f.items() if k not in ("train", "validation")}


def validate_configuration(folds: list[dict], feature_set: str, scheme: str) -> dict:
    """Pooled out-of-fold scores for one configuration (every prediction comes from a model that never saw it)."""
    ys, preds, per_fold = [], [], []
    for f in folds:
        tr, va = f["train"], f["validation"]
        if tr[TARGET].nunique() < 2:
            per_fold.append({"fold": f["fold"], "skipped": "training rows contain a single class"})
            continue
        pipe, cols = fit_configuration(tr, feature_set, scheme)
        pred = pipe.predict(va[cols])
        ys.append(va[TARGET].to_numpy(dtype=object))
        preds.append(pred.astype(object))
        s = score(ys[-1], preds[-1])
        per_fold.append({"fold": f["fold"], "rows": s["rows"], "classes_missing": s["classes_missing"],
                         "accuracy": s["accuracy"], "balanced_accuracy": s["balanced_accuracy"],
                         "f1_macro_present": s["f1_macro_present"], "high_recall": s["high_recall"],
                         "medium_recall": s["medium_recall"], "medium_support": s["per_class"]["Medium"]["support"]})
    if not ys:
        return {"feature_set": feature_set, "weight_scheme": scheme, "pooled": None, "per_fold": per_fold}
    return {"feature_set": feature_set, "weight_scheme": scheme,
            "pooled": score(np.concatenate(ys), np.concatenate(preds)), "per_fold": per_fold}


def select(candidates: dict[tuple[str, str], dict]) -> dict:
    """Apply the pre-declared rule to validation results only. Takes no test data by construction."""
    base = candidates[BASELINE]["pooled"]
    if base is None:
        return {"selected": list(BASELINE), "reason": "baseline validation unavailable; baseline retained",
                "per_arm": {}}
    floor = (base["high_recall"] or 0.0) - HIGH_RECALL_TOLERANCE if base["high_recall"] is not None else None

    def eligible(pooled) -> bool:
        if pooled is None or pooled["f1_macro_present"] is None:
            return False
        return floor is None or (pooled["high_recall"] is not None and pooled["high_recall"] >= floor)

    def best(keys):
        pool = [k for k in keys if eligible(candidates[k]["pooled"])]
        if not pool:
            return BASELINE
        # highest validation macro-F1; ties keep configuration order (baseline-first, simplest-first)
        top = max(pool, key=lambda k: (round(candidates[k]["pooled"]["f1_macro_present"], 12), -pool.index(k)))
        return top

    order = [BASELINE] + [k for k in candidates if k != BASELINE]
    arm_winner = {"baseline": BASELINE}
    for arm, fs in ARMS.items():
        if fs is not None:
            arm_winner[arm] = best([k for k in order if k[0] == fs])
    overall = best(list(dict.fromkeys(arm_winner.values())))
    gain = candidates[overall]["pooled"]["f1_macro_present"] - base["f1_macro_present"]
    if overall != BASELINE and gain < MIN_IMPROVEMENT:
        reason, overall = (f"best candidate gains {gain:.4f} validation macro-F1 < {MIN_IMPROVEMENT}; baseline retained",
                           BASELINE)
    elif overall == BASELINE:
        reason = "no eligible candidate beat the baseline on validation"
    else:
        reason = f"+{gain:.4f} validation macro-F1 over baseline with High recall within {HIGH_RECALL_TOLERANCE}"
    return {"selected": list(overall), "reason": reason,
            "arm_winners": {a: list(k) for a, k in arm_winner.items()},
            "medium_in_pooled_validation": base["per_class"]["Medium"]["support"] > 0,
            "rule": {"score": "pooled out-of-fold macro-F1 over present classes",
                     "high_recall_floor": floor, "min_improvement": MIN_IMPROVEMENT}}


def run_validation(train_df: pd.DataFrame) -> dict:
    """Everything that may influence selection. The test window is not an argument."""
    folds = validation_folds(train_df)
    if not folds:
        raise ValueError("training window too small for chronological validation folds")
    keys = [BASELINE] + [(fs, w) for fs in FEATURE_SETS for w in WEIGHT_SCHEMES if (fs, w) != BASELINE]
    candidates = {k: validate_configuration(folds, *k) for k in keys}
    return {"folds": [fold_report(f) for f in folds], "candidates": candidates, "selection": select(candidates)}


# ---------------------------------------------------------------------------
# One-shot test evaluation of the FROZEN selection
# ---------------------------------------------------------------------------

def evaluate_test(train_df: pd.DataFrame, test_df: pd.DataFrame, validation: dict) -> dict:
    sel = validation["selection"]
    arms = {"baseline": BASELINE}
    arms.update({a: tuple(k) for a, k in sel.get("arm_winners", {}).items() if a != "baseline"})
    out = {}
    cache: dict[tuple, dict] = {}
    for arm, key in arms.items():
        if key not in cache:
            pipe, cols = fit_configuration(train_df, *key)
            cache[key] = score(test_df[TARGET].to_numpy(dtype=object), pipe.predict(test_df[cols]).astype(object))
        out[arm] = {"feature_set": key[0], "weight_scheme": key[1], **cache[key],
                    "is_overall_selection": list(key) == sel["selected"]}
    return out


def stage_label_table(df: pd.DataFrame) -> dict:
    if "mango_stage" not in df.columns:
        return {}
    ct = pd.crosstab(df["mango_stage"], df[TARGET]).reindex(columns=CLASSES, fill_value=0)
    return {str(s): {c: int(ct.loc[s, c]) for c in CLASSES} for s in ct.index}


def structural_findings(train_df: pd.DataFrame, test_df: pd.DataFrame) -> list[str]:
    tr, te = stage_label_table(train_df), stage_label_table(test_df)
    notes = []
    for stage, counts in te.items():
        if counts["Medium"] and not tr.get(stage, {}).get("Medium"):
            notes.append(f"Stage '{stage}': {counts['Medium']} Medium label(s) in the test window but "
                         f"{tr.get(stage, {}).get('Medium', 0)} in training ({tr.get(stage)}); a model trained on "
                         "this window cannot have learned Medium for that stage.")
    return notes


def run_experiment(df: pd.DataFrame) -> dict:
    """Full experiment on a labelled dataset. Deterministic for a given input."""
    df = sorted_labelled(df)
    train_df, test_df = chronological_split(df)
    validation = run_validation(train_df)                 # 1. choose, using training rows only
    test = evaluate_test(train_df, test_df, validation)   # 2. then look at the test window once
    return {
        "experiment": "medium_class_improvement",
        "label_type": "surrogate_rule_based",
        "warning": LABEL_WARNING,
        "data": {"rows": len(df), "train_rows": len(train_df), "test_rows": len(test_df),
                 "train_date_range": [str(train_df["date"].iloc[0]), str(train_df["date"].iloc[-1])],
                 "test_date_range": [str(test_df["date"].iloc[0]), str(test_df["date"].iloc[-1])],
                 "train_class_counts": class_counts(train_df[TARGET]),
                 "test_class_counts": class_counts(test_df[TARGET]),
                 "stage_by_label_train": stage_label_table(train_df),
                 "stage_by_label_test": stage_label_table(test_df)},
        "structural_findings": structural_findings(train_df, test_df),
        "protocol": {"seed": SEED, "n_folds": N_FOLDS, "initial_train_fraction": INITIAL_TRAIN_FRACTION,
                     "high_recall_tolerance": HIGH_RECALL_TOLERANCE, "min_improvement": MIN_IMPROVEMENT,
                     "feature_sets": {k: list(v) for k, v in FEATURE_SETS.items()},
                     "production_exclusions_applied": sorted(EXCLUDED_COLUMNS),
                     "weight_schemes": list(WEIGHT_SCHEMES),
                     "test_window_used_for_selection": False},
        "validation": {
            "folds": validation["folds"],
            "candidates": [{"feature_set": k[0], "weight_scheme": k[1], **{kk: vv for kk, vv in v.items()
                            if kk not in ("feature_set", "weight_scheme")}}
                           for k, v in validation["candidates"].items()],
            "selection": validation["selection"],
        },
        "test": test,
    }


# ---------------------------------------------------------------------------
# Output (isolated from production artifacts)
# ---------------------------------------------------------------------------

def _production_dirs() -> set[Path]:
    cfg = get_config()
    keys = ("irrigation_priority_model_path", "ml_model_metrics_json", "ml_feature_importance_csv",
            "ml_training_dataset_csv", "ml_backtest_summary_json", "ml_medium_failure_summary_json")
    dirs = set()
    for k in keys:
        try:
            dirs.add(Path(cfg.path(k)).resolve().parent)
        except KeyError:
            pass
    return dirs


def check_output_dir(out_dir: Path) -> Path:
    """Experiment files live under data/experiments/ (or outside the project, e.g. a temp dir), never beside
    production artifacts."""
    out_dir = Path(out_dir).resolve()
    root, experiments = PROJECT_ROOT.resolve(), (PROJECT_ROOT / "data" / "experiments").resolve()
    inside_project = out_dir == root or root in out_dir.parents
    if inside_project and not (out_dir == experiments or experiments in out_dir.parents):
        raise ValueError(f"Experiment output must go under {experiments}; refusing {out_dir}")
    if out_dir in _production_dirs():
        raise ValueError(f"Refusing to write into a production artifact directory: {out_dir}")
    return out_dir


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return str(o)


def results_digest(results: dict) -> str:
    return hashlib.sha256(json.dumps(results, sort_keys=True, default=_json_default).encode()).hexdigest()


def write_results(results: dict, out_dir: Path = EXPERIMENT_DIR) -> dict[str, Path]:
    out_dir = check_output_dir(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(results, results_digest=results_digest(results),
                   generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    paths = {"json": out_dir / RESULTS_JSON, "validation_csv": out_dir / VALIDATION_CSV, "folds_csv": out_dir / FOLDS_CSV}
    paths["json"].write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")
    rows = []
    for c in results["validation"]["candidates"]:
        p = c["pooled"] or {}
        rows.append({"feature_set": c["feature_set"], "weight_scheme": c["weight_scheme"],
                     "accuracy": p.get("accuracy"), "balanced_accuracy": p.get("balanced_accuracy"),
                     "f1_macro_present": p.get("f1_macro_present"), "high_recall": p.get("high_recall"),
                     "medium_recall": p.get("medium_recall"),
                     "medium_support": (p.get("per_class") or {}).get("Medium", {}).get("support"),
                     "classes_missing_in_pooled_validation": ",".join(p.get("classes_missing", []))})
    pd.DataFrame(rows).to_csv(paths["validation_csv"], index=False)
    fr = [{**{k: v for k, v in f.items() if not k.endswith("counts") and not k.startswith("classes")},
           **{f"train_{c}": f["train_class_counts"][c] for c in CLASSES},
           **{f"validation_{c}": f["validation_class_counts"][c] for c in CLASSES},
           "missing_in_train": ",".join(f["classes_missing_in_train"]),
           "missing_in_validation": ",".join(f["classes_missing_in_validation"])}
          for f in results["validation"]["folds"]]
    pd.DataFrame(fr).to_csv(paths["folds_csv"], index=False)
    return paths


def _fmt(v) -> str:
    return "n/a" if v is None else f"{v:.3f}"


def print_report(results: dict) -> None:
    d = results["data"]
    print("\nMEDIUM-CLASS EXPERIMENT (surrogate labels; research only)")
    print(f"  train {d['train_rows']} rows {d['train_class_counts']}  |  test {d['test_rows']} rows {d['test_class_counts']}")
    for n in results["structural_findings"]:
        print("  - " + n)
    print("  Validation folds (training window only):")
    for f in results["validation"]["folds"]:
        print(f"    fold {f['fold']}: val {f['validation_start']}..{f['validation_end']} {f['validation_class_counts']}"
              f"  missing in validation: {f['classes_missing_in_validation'] or '-'}"
              f"  missing in train: {f['classes_missing_in_train'] or '-'}")
    sel = results["validation"]["selection"]
    print(f"  Selected on validation: {sel['selected']} ({sel['reason']})")
    print("  Test window (reported once, after selection):")
    for arm, t in results["test"].items():
        print(f"    {arm:28s} {t['feature_set']}/{t['weight_scheme']:20s} bal_acc {_fmt(t['balanced_accuracy'])} "
              f"macroF1 {_fmt(t['f1_macro_present'])} Medium recall {_fmt(t['medium_recall'])} "
              f"High recall {_fmt(t['high_recall'])}")
    print(f"  {LABEL_WARNING}")


def main(config=None, out_dir: Path = EXPERIMENT_DIR) -> bool:
    config = config or get_config()
    data_path = config.path("ml_training_dataset_csv")
    if not data_path.exists():
        print(f"Training dataset not found: {data_path}")
        return False
    results = run_experiment(pd.read_csv(data_path))
    paths = write_results(results, out_dir)
    print_report(results)
    for k, p in paths.items():
        print(f">>> {k}: {p}")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
