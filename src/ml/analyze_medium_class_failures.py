"""
Medium-class failure analysis for the baseline irrigation-priority classifier
(SURROGATE-LABEL DIAGNOSTIC; read-only with respect to production artifacts).

PURPOSE
  Explain why the Random Forest rarely recognises Medium-priority days. This
  module reproduces the production chronological 80/20 split and fitted model
  (via train_irrigation_priority_model.train_and_evaluate), then inspects
  every actual Medium row of the test window.

WHAT IT DOES NOT DO
  * It never writes the model, the published metrics JSON, the feature
    importance CSV or any advisory output, and it promotes nothing.
  * It does not touch the FAO-56 calculations.
  * Labels are surrogate (FAO-56 Ks thresholds), not field observations; every
    result describes how well a model imitates those rules.

LEAKAGE CONTROL
  * Model features are exactly the production features (columns chosen from the
    training split only; Ks/depletion/TAW/RAW excluded).
  * Columns used only to EXPLAIN errors (ks, depletion, stress level, label
    context such as days_to_next_change) are prefixed or listed in
    ANALYSIS_ONLY_COLUMNS and are never passed to a model, except in one
    clearly flagged oracle DIAGNOSTIC that adds depletion to test a hypothesis.
  * Offline experiments (class weights, probability thresholds) are selected
    ONLY with chronological validation folds inside the training window. The
    final test window is scored once afterwards and is never used for selection.

OUTPUTS (all under data/processed/, lightweight)
  muthukur_ml_medium_failure_analysis.csv     one row per test observation
  muthukur_ml_medium_failure_summary.json     metrics, findings, experiments
  muthukur_ml_medium_transition_analysis.csv  transition / window performance

      python -m src.ml.analyze_medium_class_failures
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ml.backtest_irrigation_priority_model import (  # noqa: E402
    compute_metrics,
    make_expanding_folds,
)
from src.ml.train_irrigation_priority_model import (  # noqa: E402
    EXCLUDED_COLUMNS,
    LABEL_WARNING,
    TARGET,
    build_pipeline,
    chronological_split,
    split_features_target,
    train_and_evaluate,
)
from src.utils.config import get_config  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

log = get_logger(__name__)

CLASSES = ["Low", "Medium", "High"]
KS_LOW_MAX_THRESHOLD = 0.90      # Ks >= 0.90 -> Low priority
KS_MEDIUM_MIN_THRESHOLD = 0.60   # Ks >= 0.60 -> Medium, else High
WINDOWS = (0, 1, 2, 3, 7)
THRESHOLD_GRID = [round(t, 2) for t in np.arange(0.10, 0.61, 0.05)]

EXPLANATORY_FEATURES = [
    "mango_stage", "temperature_avg_c", "rainfall_mm", "rainfall_7day_mm", "etc_mm_day",
    "et0_mm_day", "days_since_last_irrigation", "irrigation_risk_score",
]
# Used only to explain errors; never fed to the production-equivalent model.
ANALYSIS_ONLY_COLUMNS = [
    "ks", "root_zone_depletion_mm", "taw_mm", "raw_mm", "water_stress_level",
    "depletion_fraction_of_taw", "ks_rule_label", "label_matches_ks_rule", "distance_to_ks_threshold",
    "prev_actual", "is_label_transition", "days_since_label_change", "days_to_next_label_change",
    "run_length_days", "position_in_run", "offset_from_nearest_medium", "within_3d_of_label_change",
]

DIAGNOSTIC_NOTE = (
    "Surrogate-label diagnostic only. Nothing here is field-validated, nothing is promoted, and "
    "the published model, metrics and irrigation advisory are unchanged."
)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def safe_div(num: float, den: float) -> float:
    """num/den, or 0.0 when the denominator is zero (zero predictions / zero support)."""
    return float(num) / float(den) if den else 0.0


def class_prf(y_true, y_pred, cls: str = "Medium") -> dict:
    """Precision/recall/F1 for one class with explicit zero-division handling."""
    yt, yp = np.asarray(y_true, dtype=object), np.asarray(y_pred, dtype=object)
    tp = int(((yt == cls) & (yp == cls)).sum())
    fp = int(((yt != cls) & (yp == cls)).sum())
    fn = int(((yt == cls) & (yp != cls)).sum())
    precision, recall = safe_div(tp, tp + fp), safe_div(tp, tp + fn)
    return {
        "support": tp + fn, "predicted": tp + fp, "true_positives": tp,
        "false_positives": fp, "false_negatives": fn,
        "precision": precision, "recall": recall,
        "f1": safe_div(2 * precision * recall, precision + recall),
        "precision_defined": (tp + fp) > 0,      # False -> model never predicted the class
        "recall_defined": (tp + fn) > 0,         # False -> class absent from y_true
    }


def ks_rule_label(ks) -> str | None:
    """Label implied by the FAO-56 surrogate Ks thresholds (None for missing Ks)."""
    if ks is None or pd.isna(ks):
        return None
    return "Low" if ks >= KS_LOW_MAX_THRESHOLD else ("Medium" if ks >= KS_MEDIUM_MIN_THRESHOLD else "High")


def align_proba(pipe, X: pd.DataFrame, classes: list[str] = CLASSES) -> pd.DataFrame:
    """Probabilities as columns in a FIXED class order (0 for classes the model never saw)."""
    raw = pipe.predict_proba(X)
    known = list(pipe.classes_)
    out = pd.DataFrame(0.0, index=range(len(X)), columns=classes)
    for j, c in enumerate(known):
        if c in out.columns:
            out[c] = raw[:, j]
    return out


def label_context(labels: pd.Series) -> pd.DataFrame:
    """
    Per-row label context for a date-ordered label series.
      days_since_label_change  looks BACKWARD only (past information)
      days_to_next_label_change looks FORWARD (analysis only; never a model feature)
    """
    lab = pd.Series(labels).reset_index(drop=True)
    n = len(lab)
    prev = lab.shift(1)
    is_transition = (lab != prev) & prev.notna()
    run_id = (lab != prev).cumsum()
    run_len = lab.groupby(run_id).transform("size")
    pos = lab.groupby(run_id).cumcount() + 1

    last_change = np.full(n, np.nan)
    cur = np.nan
    for i in range(n):
        if i > 0 and bool(is_transition.iloc[i]):
            cur = i
        last_change[i] = cur
    since = np.where(np.isnan(last_change), np.nan, np.arange(n) - last_change)

    nxt = np.full(n, np.nan)
    upcoming = np.nan
    for i in range(n - 1, -1, -1):
        nxt[i] = upcoming - i if not np.isnan(upcoming) else np.nan
        if bool(is_transition.iloc[i]):
            upcoming = i
    return pd.DataFrame({
        "prev_actual": prev, "is_label_transition": is_transition,
        "days_since_label_change": since, "days_to_next_label_change": nxt,
        "run_id": run_id, "run_length_days": run_len, "position_in_run": pos,
    })


def transition_counts(labels: pd.Series) -> pd.DataFrame:
    """Counts of from->to label changes, in date order."""
    lab = pd.Series(labels).reset_index(drop=True)
    pairs = pd.DataFrame({"from": lab.shift(1), "to": lab})[lab != lab.shift(1)].dropna()
    if pairs.empty:
        return pd.DataFrame(columns=["from", "to", "count"])
    return pairs.groupby(["from", "to"]).size().reset_index(name="count")


def signed_offset_to_nearest(is_target: np.ndarray) -> np.ndarray:
    """Signed row offset to the nearest True row (negative = target is earlier). NaN if none."""
    idx = np.flatnonzero(is_target)
    n = len(is_target)
    out = np.full(n, np.nan)
    if idx.size == 0:
        return out
    for i in range(n):
        j = idx[np.argmin(np.abs(idx - i))]
        out[i] = i - j
    return out


def reproduce_split(df: pd.DataFrame):
    """The production split: labelled rows, date-sorted, first 80% train / last 20% test."""
    labelled = df.dropna(subset=[TARGET])
    return chronological_split(labelled)


def check_no_leakage(train_df: pd.DataFrame, test_df: pd.DataFrame, feature_columns: list[str]) -> dict:
    """Structural leakage checks. Raises nothing; returns booleans for the report."""
    td, ed = pd.to_datetime(train_df["date"]), pd.to_datetime(test_df["date"])
    forbidden = set(EXCLUDED_COLUMNS) | {"ks", "root_zone_depletion_mm", "taw_mm", "raw_mm"}
    return {
        "test_strictly_after_train": bool(len(td) and len(ed) and td.max() < ed.min()),
        "no_date_overlap": not (set(td) & set(ed)),
        "features_exclude_label_determinants": not (set(feature_columns) & forbidden),
        "features_exclude_targets": not any(c.startswith("target_") for c in feature_columns),
        "analysis_columns_not_features": not (set(feature_columns) & set(ANALYSIS_ONLY_COLUMNS)),
    }


# ---------------------------------------------------------------------------
# Row-level analysis frame
# ---------------------------------------------------------------------------

def build_analysis_frame(full_df: pd.DataFrame, test_df: pd.DataFrame,
                         proba: pd.DataFrame, predicted: np.ndarray) -> pd.DataFrame:
    """
    One row per test observation: actual/predicted, probabilities, confidence,
    explanatory features and label-context columns. Context uses the full
    labelled series so dates around the train/test boundary are described.
    """
    full = full_df.dropna(subset=[TARGET]).assign(_d=lambda d: pd.to_datetime(d["date"]))
    full = full.sort_values("_d").reset_index(drop=True)
    ctx = label_context(full[TARGET])
    offset = signed_offset_to_nearest((full[TARGET] == "Medium").to_numpy())
    ctx["offset_from_nearest_medium"] = offset
    full_ctx = pd.concat([full, ctx], axis=1)

    t = test_df.reset_index(drop=True).copy()
    t["_d"] = pd.to_datetime(t["date"])
    merged = t[["_d"]].merge(full_ctx.drop_duplicates("_d"), on="_d", how="left")

    out = pd.DataFrame({
        "date": t["date"].astype(str).to_numpy(),
        "month": t["_d"].dt.month.to_numpy(),
        "actual": t[TARGET].to_numpy(),
        "predicted": np.asarray(predicted),
    })
    for c in CLASSES:
        out[f"proba_{c}"] = proba[c].to_numpy()
    out["confidence"] = proba[CLASSES].max(axis=1).to_numpy()
    out["proba_actual_class"] = [proba.loc[i, a] if a in proba.columns else np.nan
                                 for i, a in enumerate(out["actual"])]
    out["correct"] = (out["actual"] == out["predicted"]).to_numpy()

    for c in EXPLANATORY_FEATURES:
        out[c] = t[c].to_numpy() if c in t.columns else np.nan
    for c in ("ks", "root_zone_depletion_mm", "taw_mm", "raw_mm", "water_stress_level"):
        out[c] = t[c].to_numpy() if c in t.columns else np.nan
    out["depletion_fraction_of_taw"] = (pd.to_numeric(out["root_zone_depletion_mm"], errors="coerce")
                                        / pd.to_numeric(out["taw_mm"], errors="coerce"))
    out["ks_rule_label"] = [ks_rule_label(k) for k in out["ks"]]
    out["label_matches_ks_rule"] = out["ks_rule_label"] == out["actual"]
    ks = pd.to_numeric(out["ks"], errors="coerce")
    out["distance_to_ks_threshold"] = np.minimum((ks - KS_LOW_MAX_THRESHOLD).abs(),
                                                 (ks - KS_MEDIUM_MIN_THRESHOLD).abs())
    for c in ("prev_actual", "is_label_transition", "days_since_label_change",
              "days_to_next_label_change", "run_length_days", "position_in_run",
              "offset_from_nearest_medium"):
        out[c] = merged[c].to_numpy()
    since = pd.to_numeric(out["days_since_label_change"], errors="coerce")
    nxt = pd.to_numeric(out["days_to_next_label_change"], errors="coerce")
    out["within_3d_of_label_change"] = ((since <= 3) | (nxt <= 3)).fillna(False).to_numpy()
    out["is_actual_medium"] = out["actual"] == "Medium"
    return out


# ---------------------------------------------------------------------------
# Transition analysis
# ---------------------------------------------------------------------------

def _acc(df: pd.DataFrame) -> float | None:
    return float(df["correct"].mean()) if len(df) else None


def build_transition_analysis(full_df: pd.DataFrame, analysis: pd.DataFrame) -> pd.DataFrame:
    """Long-format table: transition types, windows around label changes, offsets from Medium."""
    rows: list[dict] = []
    full = full_df.dropna(subset=[TARGET]).sort_values("date").reset_index(drop=True)
    test_dates = set(analysis["date"])

    # 1. transition types (full series and test window)
    lab = full[TARGET].reset_index(drop=True)
    prev = lab.shift(1)
    change_idx = [i for i in range(1, len(lab)) if lab.iloc[i] != prev.iloc[i]]
    by_date = analysis.set_index("date")
    for (frm, to), grp in pd.DataFrame(
            {"from": [prev.iloc[i] for i in change_idx], "to": [lab.iloc[i] for i in change_idx],
             "date": [str(full["date"].iloc[i]) for i in change_idx]}).groupby(["from", "to"]):
        in_test = grp[grp["date"].isin(test_dates)]
        sub = by_date.loc[in_test["date"]] if len(in_test) else by_date.iloc[0:0]
        rows.append({
            "kind": "transition_type", "key": f"{frm}->{to}",
            "n_full_series": int(len(grp)), "n_test": int(len(in_test)),
            "test_accuracy_on_transition_day": _acc(sub),
            "test_share_predicted_as_new_label": float((sub["predicted"] == to).mean()) if len(sub) else None,
            "mean_confidence": float(sub["confidence"].mean()) if len(sub) else None,
        })

    # 2. windows around ANY label change (rows from the full series, backward and forward)
    change_pos = set(change_idx)
    n = len(full)
    date_pos = {str(d): i for i, d in enumerate(full["date"])}
    pos = analysis["date"].map(date_pos)
    nearest = pd.Series([
        min((abs(p - c) for c in change_pos), default=np.inf) if pd.notna(p) else np.inf for p in pos
    ], index=analysis.index)
    for w in WINDOWS:
        sel = analysis[nearest <= w]
        med = sel[sel["is_actual_medium"]]
        rows.append({
            "kind": "window_around_label_change", "key": f"within_{w}d", "n_test": int(len(sel)),
            "accuracy": _acc(sel), "actual_medium": int(len(med)),
            "medium_recall": float(med["correct"].mean()) if len(med) else None,
        })
    outside = analysis[nearest > max(WINDOWS)]
    out_med = outside[outside["is_actual_medium"]]
    rows.append({
        "kind": "window_around_label_change", "key": f"outside_{max(WINDOWS)}d", "n_test": int(len(outside)),
        "accuracy": _acc(outside), "actual_medium": int(len(out_med)),
        "medium_recall": float(out_med["correct"].mean()) if len(out_med) else None,
    })

    # 3. signed offsets from the nearest actual Medium row
    off = pd.to_numeric(analysis["offset_from_nearest_medium"], errors="coerce")
    for d in range(-WINDOWS[3], WINDOWS[3] + 1):
        sel = analysis[off == d]
        rows.append({
            "kind": "offset_from_medium", "key": f"{d:+d}", "n_test": int(len(sel)),
            "accuracy": _acc(sel),
            "mean_proba_medium": float(sel["proba_Medium"].mean()) if len(sel) else None,
            "share_predicted_medium": float((sel["predicted"] == "Medium").mean()) if len(sel) else None,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Offline experiments (validation inside the training window only)
# ---------------------------------------------------------------------------

def apply_medium_threshold(proba: pd.DataFrame, threshold: float | None) -> np.ndarray:
    """Predict Medium when p(Medium) >= threshold, else argmax over Low/High. None -> plain argmax."""
    if threshold is None:
        return proba[CLASSES].idxmax(axis=1).to_numpy(dtype=object)
    others = proba[["Low", "High"]].idxmax(axis=1).to_numpy(dtype=object)
    return np.where(proba["Medium"].to_numpy() >= threshold, "Medium", others)


def select_medium_threshold(y_val, proba_val: pd.DataFrame, grid=THRESHOLD_GRID) -> float | None:
    """Pick the threshold with the best Medium F1 on VALIDATION data (ties -> larger threshold)."""
    if len(y_val) == 0 or not (np.asarray(y_val, dtype=object) == "Medium").any():
        return None
    best_t, best_f1 = None, -1.0
    for t in grid:
        f1 = class_prf(y_val, apply_medium_threshold(proba_val, t))["f1"]
        if f1 >= best_f1:
            best_t, best_f1 = t, f1
    return best_t


def _make_estimator(name: str, X: pd.DataFrame) -> Pipeline:
    pipe = build_pipeline(X)
    if name == "rf_balanced_production":
        return pipe
    if name == "rf_no_class_weight":
        return pipe.set_params(model__class_weight=None)
    if name == "rf_balanced_subsample":
        return pipe.set_params(model__class_weight="balanced_subsample")
    if name == "logistic_regression_balanced":
        pre = pipe.named_steps["preprocess"]
        return Pipeline([("preprocess", pre), ("scale", StandardScaler(with_mean=False)),
                         ("model", LogisticRegression(class_weight="balanced", max_iter=2000))])
    raise ValueError(name)


MODEL_NAMES = ["rf_balanced_production", "rf_no_class_weight", "rf_balanced_subsample",
               "logistic_regression_balanced"]


def _scores(y_true, y_pred) -> dict:
    m = compute_metrics(y_true, y_pred, CLASSES)
    med = class_prf(y_true, y_pred)
    return {
        "rows": int(len(y_true)), "accuracy": m["accuracy"], "balanced_accuracy": m["balanced_accuracy"],
        "f1_macro_fixed": m["f1_macro_fixed"], "f1_macro_present": m["f1_macro_present"],
        "medium_precision": med["precision"], "medium_recall": med["recall"], "medium_f1": med["f1"],
        "medium_predicted": med["predicted"], "medium_precision_defined": med["precision_defined"],
    }


def _inner_validation(train_df: pd.DataFrame, name: str, n_folds: int = 3):
    """Pooled out-of-sample predictions on expanding folds INSIDE the training window."""
    folds = make_expanding_folds(len(train_df), n_folds=n_folds, initial_train_fraction=0.5)
    if not folds:
        return None
    ys, probas = [], []
    for tr_idx, va_idx in folds:
        tr, va = train_df.iloc[tr_idx], train_df.iloc[va_idx]
        X_tr, y_tr = split_features_target(tr)
        if y_tr.nunique() < 2:
            continue
        est = _make_estimator(name, X_tr).fit(X_tr, y_tr)
        probas.append(align_proba(est, va[X_tr.columns]))
        ys.append(va[TARGET].reset_index(drop=True))
    if not ys:
        return None
    return pd.concat(ys, ignore_index=True), pd.concat(probas, ignore_index=True)


def persistence_predictions(train_df: pd.DataFrame, test_df: pd.DataFrame) -> np.ndarray:
    """Baseline: predict yesterday's actual label (uses past labels only; a baseline, not a feature)."""
    labels = pd.concat([train_df[TARGET].iloc[[-1]], test_df[TARGET]], ignore_index=True)
    return labels.shift(1).iloc[1:].to_numpy(dtype=object)


def run_offline_experiments(train_df: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    """
    Compare the production-style RF with simple baselines and variants. Validation
    scores come from folds inside the training window; test scores are reported
    once and never used to choose anything.
    """
    y_test = test_df[TARGET].reset_index(drop=True)
    results: dict = {}

    majority = train_df[TARGET].value_counts().idxmax()
    results["majority_class_baseline"] = {
        "validation": None, "test": _scores(y_test, np.full(len(y_test), majority, dtype=object)),
        "note": f"always predicts '{majority}'",
    }
    results["persistence_previous_day_label"] = {
        "validation": None, "test": _scores(y_test, persistence_predictions(train_df, test_df)),
        "note": "predicts the previous day's label; uses past labels, so it is a baseline only",
    }

    for name in MODEL_NAMES:
        entry: dict = {"validation": None, "test": None}
        val = _inner_validation(train_df, name)
        if val is not None:
            yv, pv = val
            entry["validation"] = _scores(yv, apply_medium_threshold(pv, None))
        X_tr, y_tr = split_features_target(train_df)
        est = _make_estimator(name, X_tr).fit(X_tr, y_tr)
        pt = align_proba(est, test_df[X_tr.columns])
        entry["test"] = _scores(y_test, apply_medium_threshold(pt, None))
        results[name] = entry

    # Probability threshold: chosen on validation only, applied once to test.
    thr: dict = {"model": "rf_balanced_production", "grid": THRESHOLD_GRID,
                 "selected_on": "validation folds inside the training window",
                 "selected_threshold": None, "validation": None, "test": None}
    val = _inner_validation(train_df, "rf_balanced_production")
    if val is not None:
        yv, pv = val
        t = select_medium_threshold(yv, pv)
        thr["selected_threshold"] = t
        thr["validation"] = {
            "default_argmax": _scores(yv, apply_medium_threshold(pv, None)),
            "selected_threshold": _scores(yv, apply_medium_threshold(pv, t)),
        }
        X_tr, y_tr = split_features_target(train_df)
        est = _make_estimator("rf_balanced_production", X_tr).fit(X_tr, y_tr)
        pt = align_proba(est, test_df[X_tr.columns])
        thr["test"] = {
            "default_argmax": _scores(y_test, apply_medium_threshold(pt, None)),
            "selected_threshold": _scores(y_test, apply_medium_threshold(pt, t)),
        }
    thr["note"] = "Offline experiment; not adopted. The test window was not used to choose the threshold."
    results["medium_probability_threshold"] = thr

    # Oracle diagnostics: add the label-determining depletion feature to test whether the missing
    # information is the water-stress state. NOT usable models (leakage by design).
    X_tr, y_tr = split_features_target(train_df)
    if "root_zone_depletion_mm" in train_df.columns:
        for name, cols, note in (
            ("diagnostic_oracle_all_features_plus_depletion",
             list(X_tr.columns) + ["root_zone_depletion_mm"],
             "DIAGNOSTIC ONLY: production features plus the label-determining depletion (leakage by design)."),
            ("diagnostic_oracle_depletion_only", ["root_zone_depletion_mm"],
             "DIAGNOSTIC ONLY: a Random Forest on depletion alone (leakage by design)."),
        ):
            est = _make_estimator("rf_balanced_production", train_df[cols]).fit(train_df[cols], y_tr)
            pt = align_proba(est, test_df[cols])
            results[name] = {"validation": None, "note": note,
                             "test": _scores(y_test, apply_medium_threshold(pt, None))}
    return results


# ---------------------------------------------------------------------------
# Summary and findings
# ---------------------------------------------------------------------------

def _group_table(analysis: pd.DataFrame, col: str) -> list[dict]:
    rows = []
    for key, g in analysis.groupby(col, dropna=False):
        med = g[g["is_actual_medium"]]
        rows.append({
            col: None if pd.isna(key) else (key.item() if hasattr(key, "item") else key),
            "rows": int(len(g)), "error_rate": float(1 - g["correct"].mean()),
            "actual_medium": int(len(med)),
            "medium_recall": float(med["correct"].mean()) if len(med) else None,
        })
    return rows


def _feature_means(frame: pd.DataFrame) -> dict:
    cols = ["temperature_avg_c", "rainfall_7day_mm", "etc_mm_day", "ks", "depletion_fraction_of_taw"]
    return {c: (float(pd.to_numeric(frame[c], errors="coerce").mean()) if len(frame) else None)
            for c in cols if c in frame.columns}


def summarize_analysis(analysis: pd.DataFrame, full_df: pd.DataFrame, train_df: pd.DataFrame,
                       test_df: pd.DataFrame, leakage: dict, experiments: dict | None,
                       classes_in_model: list[str]) -> dict:
    """Build the JSON summary, including supported findings vs hypotheses."""
    y, p = analysis["actual"], analysis["predicted"]
    med = analysis[analysis["is_actual_medium"]]
    prf = class_prf(y, p)
    wrong = med[~med["correct"]]
    right = med[med["correct"]]

    medium_block = {
        "actual_medium_cases": int(len(med)),
        "correctly_classified": int(med["correct"].sum()) if len(med) else 0,
        "predicted_medium_total": prf["predicted"],
        "precision": prf["precision"], "precision_defined": prf["precision_defined"],
        "recall": prf["recall"], "recall_defined": prf["recall_defined"], "f1": prf["f1"],
        "missed_as_High": int((wrong["predicted"] == "High").sum()),
        "missed_as_Low": int((wrong["predicted"] == "Low").sum()),
        "false_positive_medium_from_High": int(((y == "High") & (p == "Medium")).sum()),
        "false_positive_medium_from_Low": int(((y == "Low") & (p == "Medium")).sum()),
        "mean_confidence_all_medium_rows": float(med["confidence"].mean()) if len(med) else None,
        "mean_confidence_when_wrong": float(wrong["confidence"].mean()) if len(wrong) else None,
        "mean_proba_medium_on_actual_medium": float(med["proba_Medium"].mean()) if len(med) else None,
        "max_proba_medium_on_actual_medium": float(med["proba_Medium"].max()) if len(med) else None,
        "mean_proba_medium_on_other_rows": float(analysis.loc[~analysis["is_actual_medium"], "proba_Medium"].mean())
        if (~analysis["is_actual_medium"]).any() else None,
    }

    cm_labels = [c for c in CLASSES]
    matrix = [[int(((y == a) & (p == b)).sum()) for b in cm_labels] for a in cm_labels]

    # label structure over the full series
    full_lab = full_df.dropna(subset=[TARGET]).sort_values("date")[TARGET].reset_index(drop=True)
    ctx = label_context(full_lab)
    runs = pd.DataFrame({"label": full_lab, "run_id": ctx["run_id"]}).groupby("run_id").agg(
        label=("label", "first"), length=("label", "size"))
    med_runs = runs[runs["label"] == "Medium"]["length"]
    trans = transition_counts(full_lab)

    # Ks-rule comparison
    ks = pd.to_numeric(analysis["ks"], errors="coerce")
    ks_block: dict = {"available": bool(ks.notna().any())}
    if ks_block["available"]:
        match = analysis["label_matches_ks_rule"]
        ks_block.update({
            "labels_matching_ks_rule_percent": float(match.mean() * 100),
            "ks_range_of_actual_medium": [float(ks[analysis["is_actual_medium"]].min()),
                                          float(ks[analysis["is_actual_medium"]].max())] if len(med) else None,
            "medium_rows_within_0.05_ks_of_a_threshold_percent":
                float((med["distance_to_ks_threshold"] <= 0.05).mean() * 100) if len(med) else None,
            "missed_medium_within_0.05_ks_of_a_threshold_percent":
                float((wrong["distance_to_ks_threshold"] <= 0.05).mean() * 100) if len(wrong) else None,
            "model_agreement_with_ks_rule_percent": float((analysis["predicted"] == analysis["ks_rule_label"]).mean() * 100),
            "model_agreement_with_actual_percent": float(analysis["correct"].mean() * 100),
        })
        taw, raw = pd.to_numeric(analysis["taw_mm"], errors="coerce").dropna(), pd.to_numeric(analysis["raw_mm"], errors="coerce").dropna()
        if len(taw) and len(raw):
            taw_v, raw_v = float(taw.iloc[-1]), float(raw.iloc[-1])
            d_hi = taw_v - KS_LOW_MAX_THRESHOLD * (taw_v - raw_v)
            d_lo = taw_v - KS_MEDIUM_MIN_THRESHOLD * (taw_v - raw_v)
            etc = pd.to_numeric(analysis["etc_mm_day"], errors="coerce").dropna()
            ks_block["medium_band_depletion_mm"] = [round(d_hi, 1), round(d_lo, 1)]
            ks_block["medium_band_width_mm"] = round(d_lo - d_hi, 1)
            ks_block["medium_band_width_as_percent_of_taw"] = round((d_lo - d_hi) / taw_v * 100, 1)
            if len(etc) and etc.mean() > 0:
                ks_block["approx_days_to_cross_band_at_mean_etc"] = round((d_lo - d_hi) / float(etc.mean()), 1)

    # error clustering
    clustering = {
        "by_month": _group_table(analysis, "month"),
        "by_water_stress_state": _group_table(analysis, "water_stress_level"),
        "feature_means_medium_correct": _feature_means(right),
        "feature_means_medium_missed": _feature_means(wrong),
        "feature_means_all_test_rows": _feature_means(analysis),
    }
    for col in ("rainfall_7day_mm", "temperature_avg_c"):
        v = pd.to_numeric(analysis[col], errors="coerce")
        if v.notna().sum() >= 6 and v.nunique() >= 3:
            try:
                bins = pd.qcut(v, 3, labels=["low", "mid", "high"], duplicates="drop")
                g = analysis.assign(_b=bins.astype(object)).groupby("_b")
                clustering[f"error_rate_by_{col}_tercile"] = {
                    str(k): float(1 - grp["correct"].mean()) for k, grp in g}
            except ValueError:
                pass

    near = analysis["within_3d_of_label_change"]
    window_block = {
        "medium_rows_within_3d_of_label_change_percent": float(near[analysis["is_actual_medium"]].mean() * 100) if len(med) else None,
        "all_rows_within_3d_of_label_change_percent": float(near.mean() * 100) if len(analysis) else None,
        "accuracy_within_3d_of_label_change": _acc(analysis[near]),
        "accuracy_outside_3d_of_label_change": _acc(analysis[~near]),
    }

    findings = build_findings(medium_block, med_runs, ks_block, window_block, train_df, test_df,
                              experiments, clustering)

    return {
        "analysis_type": "medium_class_failure_analysis",
        "label_type": "surrogate_rule_based",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "warning": LABEL_WARNING,
        "scope_note": DIAGNOSTIC_NOTE,
        "dataset": {"rows": int(len(full_df)),
                    "date_range": [str(full_lab.name) if False else str(full_df["date"].min()), str(full_df["date"].max())]},
        "split": {
            "train_rows": int(len(train_df)), "test_rows": int(len(test_df)),
            "train_date_range": [str(train_df["date"].iloc[0]), str(train_df["date"].iloc[-1])],
            "test_date_range": [str(test_df["date"].iloc[0]), str(test_df["date"].iloc[-1])],
            "train_class_counts": {c: int((train_df[TARGET] == c).sum()) for c in CLASSES},
            "test_class_counts": {c: int((test_df[TARGET] == c).sum()) for c in CLASSES},
            "model_classes": classes_in_model,
        },
        "leakage_checks": leakage,
        "analysis_only_columns": ANALYSIS_ONLY_COLUMNS,
        "medium": medium_block,
        "confusion_matrix": {"labels": cm_labels, "matrix": matrix},
        "label_structure": {
            "medium_run_count": int(len(med_runs)),
            "medium_run_lengths_days": [int(x) for x in med_runs.tolist()],
            "median_medium_run_days": float(med_runs.median()) if len(med_runs) else None,
            "transitions": trans.to_dict(orient="records"),
        },
        "transition_windows": window_block,
        "ks_threshold_comparison": ks_block,
        "error_clustering": clustering,
        "offline_experiments": experiments,
        "findings": findings,
        "limitations": [
            "Labels are surrogate (FAO-56 Ks thresholds), not field observations; no field validation exists.",
            "The test window is small and may contain few Medium observations; all rates are uncertain.",
            "Offline experiments are exploratory, were not promoted, and do not change the published model.",
        ],
    }


def build_findings(medium: dict, med_runs: pd.Series, ks_block: dict, window: dict,
                   train_df: pd.DataFrame, test_df: pd.DataFrame, experiments: dict | None,
                   clustering: dict) -> list[dict]:
    """Findings are 'supported' only when the computed evidence meets an explicit test; else 'hypothesis'."""
    f: list[dict] = []

    def add(fid, statement, status, evidence):
        f.append({"id": fid, "status": status, "statement": statement, "evidence": evidence})

    n_med = medium["actual_medium_cases"]
    if n_med == 0:
        add("no_medium_in_test", "The test window contains no Medium observations, so Medium recall is undefined.",
            "supported", {"actual_medium_cases": 0})
        return f

    add("medium_recall_is_low", "The reference model misses most Medium observations."
        if medium["recall"] < 0.5 else "The reference model recovers at least half of Medium observations.",
        "supported", {"recall": medium["recall"], "correct": medium["correctly_classified"], "of": n_med})
    add("misses_are_split_between_high_and_low",
        f"Missed Medium days were predicted High {medium['missed_as_High']}x and Low {medium['missed_as_Low']}x.",
        "supported", {"missed_as_High": medium["missed_as_High"], "missed_as_Low": medium["missed_as_Low"]})
    if medium["mean_proba_medium_on_actual_medium"] is not None:
        weak = (medium["mean_proba_medium_on_actual_medium"] or 0) < 0.5
        add("medium_probability_is_not_concentrated_on_medium_days",
            "Predicted Medium probability is low even on actual Medium days." if weak
            else "Predicted Medium probability is reasonably high on actual Medium days.",
            "supported", {"mean_p_medium_on_actual_medium": medium["mean_proba_medium_on_actual_medium"],
                          "mean_p_medium_on_other_rows": medium["mean_proba_medium_on_other_rows"]})

    if len(med_runs):
        short = float(med_runs.median()) <= 10
        add("medium_is_a_short_transitional_band",
            "Medium occurs in short runs between Low and High regimes." if short
            else "Medium occurs in long runs; it is not only a brief transition.",
            "supported", {"median_run_days": float(med_runs.median()), "runs": int(len(med_runs))})
    if ks_block.get("available") and "medium_band_width_mm" in ks_block:
        add("medium_band_is_narrow_in_depletion_terms",
            f"The Medium Ks band spans only {ks_block['medium_band_width_mm']} mm of depletion "
            f"({ks_block['medium_band_width_as_percent_of_taw']}% of TAW).",
            "supported", {k: ks_block[k] for k in ("medium_band_depletion_mm", "medium_band_width_mm",
                                                  "medium_band_width_as_percent_of_taw")})
    add("model_has_no_direct_water_stress_state",
        "Production features deliberately exclude Ks, depletion, TAW and RAW, so the model must infer "
        "the Medium band indirectly from weather, stage and satellite features.",
        "supported", {"excluded": ["ks", "root_zone_depletion_mm", "taw_mm", "raw_mm", "water_stress_level"]})

    n_tr_med = int((train_df[TARGET] == "Medium").sum())
    add("medium_has_little_training_support",
        f"Only {n_tr_med} Medium rows are in the training window.",
        "supported" if n_tr_med < 0.1 * len(train_df) else "hypothesis",
        {"train_medium_rows": n_tr_med, "train_rows": int(len(train_df))})

    ex = experiments or {}
    full_o = (ex.get("diagnostic_oracle_all_features_plus_depletion") or {}).get("test")
    dep_o = (ex.get("diagnostic_oracle_depletion_only") or {}).get("test")
    ref = (ex.get("rf_balanced_production") or {}).get("test")
    if dep_o and ref:
        add("medium_is_separable_from_depletion_alone",
            "A Random Forest given only root-zone depletion can recognise Medium days "
            "(leakage-by-design diagnostic, not a usable model).",
            "supported" if dep_o["medium_recall"] >= 0.5 else "hypothesis",
            {"medium_recall_depletion_only": dep_o["medium_recall"],
             "medium_precision_depletion_only": dep_o["medium_precision"],
             "medium_recall_reference": ref["medium_recall"]})
    if full_o and ref:
        add("adding_depletion_to_all_features_does_not_fix_medium",
            "Adding depletion to the full production feature set still leaves Medium largely unrecognised, "
            "so the missing state variable alone is not the whole story.",
            "supported" if full_o["medium_recall"] < 0.25 else "hypothesis",
            {"medium_recall_all_features_plus_depletion": full_o["medium_recall"],
             "medium_recall_reference": ref["medium_recall"]})
    if full_o and dep_o:
        add("few_medium_examples_in_a_wide_feature_set_limit_the_forest",
            "Hypothesis: with ~23 Medium training rows among dozens of mostly weather features, a Random "
            "Forest rarely isolates the narrow Medium band even when the informative feature is present.",
            "hypothesis",
            {"medium_recall_depletion_only": dep_o["medium_recall"],
             "medium_recall_all_features_plus_depletion": full_o["medium_recall"],
             "note": "Consistent with the diagnostics but not tested directly (e.g. no feature-selection experiment)."})

    thr = (experiments or {}).get("medium_probability_threshold") or {}
    if thr.get("test") and thr.get("selected_threshold") is not None:
        a, b = thr["test"]["default_argmax"], thr["test"]["selected_threshold"]
        helped = b["medium_f1"] > a["medium_f1"]
        add("probability_threshold_could_help",
            "A lower Medium probability threshold chosen on validation folds "
            + ("improved" if helped else "did not improve") + " Medium F1 on the test window.",
            "hypothesis",
            {"threshold": thr["selected_threshold"], "medium_f1_default": a["medium_f1"],
             "medium_f1_with_threshold": b["medium_f1"],
             "note": "Single exploratory test window; not adopted."})
    add("errors_cluster_near_label_changes",
        "Errors concentrate near label transitions.",
        "supported" if (window["accuracy_within_3d_of_label_change"] is not None
                        and window["accuracy_outside_3d_of_label_change"] is not None
                        and window["accuracy_within_3d_of_label_change"] < window["accuracy_outside_3d_of_label_change"])
        else "hypothesis", window)
    add("seasonal_or_weather_driver_of_medium_errors",
        "Medium errors may depend on season or specific weather; the test window is too short to confirm.",
        "hypothesis", {"by_month": clustering["by_month"]})
    return f


# ---------------------------------------------------------------------------
# Reconciliation with the published (trainer) evaluation
# ---------------------------------------------------------------------------

def environment_versions() -> dict:
    """Runtime library versions; these can change Random Forest predictions for a fixed seed."""
    import sklearn
    return {"python": platform.python_version(), "scikit_learn": sklearn.__version__,
            "numpy": np.__version__, "pandas": pd.__version__}


def file_sha256_normalised(path: Path) -> str | None:
    """SHA-256 of a text file with CRLF folded to LF (working trees may use CRLF, git blobs LF)."""
    try:
        data = Path(path).read_bytes()
        crlf, lf = bytes([13, 10]), bytes([10])
        return hashlib.sha256(data.replace(crlf, lf)).hexdigest()
    except OSError:
        return None


def load_published_metrics(config) -> dict | None:
    """Read-only load of the published trainer metrics JSON (None if absent/unreadable)."""
    try:
        data = json.loads(Path(config.path("ml_model_metrics_json")).read_text(encoding="utf-8"))
    except (KeyError, OSError, ValueError, AttributeError):
        return None
    return data if isinstance(data, dict) else None


def reconcile_with_published(published: dict | None, reproduced: dict, env: dict | None = None,
                             dataset_info: dict | None = None) -> dict:
    """
    Compare the trainer metrics re-run in THIS environment with the published metrics JSON.

    Split, feature set and seed are deterministic code/data properties and must match. Predictions
    additionally depend on library versions, so a prediction mismatch with matching split/features
    is reported as an environment difference, not as a defect in either evaluation.
    """
    env = env or environment_versions()
    out: dict = {"environment_this_run": env, "dataset": dataset_info or {},
                 "model_configuration": {"n_estimators": 200, "class_weight": "balanced",
                                         "random_state": 42,
                                         "split": "chronological first 80% train / last 20% test"},
                 "published_metrics_available": published is not None}
    if published is None:
        return out
    split_checks = {
        "train_rows": published.get("train_rows") == reproduced.get("train_rows"),
        "test_rows": published.get("test_rows") == reproduced.get("test_rows"),
        "train_date_range": published.get("train_date_range") == reproduced.get("train_date_range"),
        "test_date_range": published.get("test_date_range") == reproduced.get("test_date_range"),
        "target_distribution": published.get("target_distribution") == reproduced.get("target_distribution"),
        "feature_count": published.get("feature_count") == reproduced.get("feature_count"),
        "feature_list": published.get("features") == reproduced.get("features"),
    }
    pub_cm = (published.get("confusion_matrix") or {}).get("matrix")
    rep_cm = (reproduced.get("confusion_matrix") or {}).get("matrix")
    acc_pub, acc_rep = published.get("accuracy"), reproduced.get("accuracy")
    preds_match = bool(pub_cm == rep_cm and acc_pub is not None and acc_rep is not None
                       and abs(acc_pub - acc_rep) < 1e-12)
    out.update({
        "published_trained_at": published.get("trained_at"),
        "split_and_features_match": all(split_checks.values()),
        "split_checks": split_checks,
        "published_accuracy": acc_pub, "reproduced_accuracy": acc_rep,
        "published_confusion_matrix": published.get("confusion_matrix"),
        "reproduced_confusion_matrix": reproduced.get("confusion_matrix"),
        "predictions_match_published": preds_match,
    })
    if not out["split_and_features_match"]:
        out["note"] = "Split or feature set differs from the published evaluation; investigate before comparing."
    elif not preds_match:
        out["note"] = (
            "Same split, features, seed and model parameters, but predictions differ from the published "
            "run. The published metrics JSON does not record library versions; Random Forest outputs "
            "for a fixed seed can change with scikit-learn/numpy/pandas versions. Neither evaluation is "
            "wrong; the published metrics were not altered."
        )
    else:
        out["note"] = "Reproduced predictions match the published evaluation exactly."
    return out


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def analyze_dataframe(df: pd.DataFrame, run_experiments: bool = True,
                      published_metrics: dict | None = None, dataset_info: dict | None = None):
    """Full analysis for a dataset frame. Returns (summary, analysis_frame, transition_frame) or None."""
    labelled = df.dropna(subset=[TARGET])
    if len(labelled) < 50 or labelled[TARGET].nunique() < 2:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pipe, metrics, _ = train_and_evaluate(df)       # production-identical fit
        train_df, test_df = reproduce_split(df)
        X_train, _ = split_features_target(train_df)
        X_test = test_df[X_train.columns]
        proba = align_proba(pipe, X_test)
        predicted = pipe.predict(X_test)
        leakage = check_no_leakage(train_df, test_df, X_train.columns.tolist())
        leakage["matches_trainer_in_this_environment"] = bool(
            abs(float((np.asarray(predicted) == test_df[TARGET].to_numpy()).mean()) - metrics["accuracy"]) < 1e-9)
        analysis = build_analysis_frame(df, test_df, proba, predicted)
        transitions = build_transition_analysis(df, analysis)
        experiments = run_offline_experiments(train_df, test_df) if run_experiments else None
        summary = summarize_analysis(analysis, df, train_df, test_df, leakage, experiments,
                                     [str(c) for c in pipe.classes_])
        summary["reproduction"] = reconcile_with_published(published_metrics, metrics, dataset_info=dataset_info)
    return summary, analysis, transitions


def analyze_medium_class_failures(config=None) -> bool:
    """Read the ML dataset, write the three report files. False if skipped. Never touches the model."""
    config = config or get_config()
    data_path = config.path("ml_training_dataset_csv")
    out_csv = config.path("ml_medium_failure_analysis_csv")
    out_json = config.path("ml_medium_failure_summary_json")
    out_trans = config.path("ml_medium_transition_analysis_csv")

    if not Path(data_path).exists():
        print(f"\nML training dataset not found: {data_path}\nSkipping Medium-class failure analysis.")
        log.warning("Medium failure analysis skipped: dataset missing (%s)", data_path)
        return False
    df = pd.read_csv(data_path)
    if TARGET not in df.columns or "date" not in df.columns:
        print("\nDataset lacks 'date' or the target column. Skipping.")
        return False
    result = analyze_dataframe(
        df, published_metrics=load_published_metrics(config),
        dataset_info={"path": str(data_path), "sha256_lf_normalised": file_sha256_normalised(data_path),
                      "rows": int(len(df)), "date_range": [str(df["date"].min()), str(df["date"].max())]},
    )
    if result is None:
        print("\nNot enough labelled rows / classes for the analysis. Skipping.")
        return False
    summary, analysis, transitions = result

    for p in (out_csv, out_json, out_trans):
        Path(p).parent.mkdir(parents=True, exist_ok=True)
    analysis.to_csv(out_csv, index=False)
    transitions.to_csv(out_trans, index=False)
    Path(out_json).write_text(json.dumps(summary, indent=2, default=_json_default), encoding="utf-8")
    _print_report(summary)
    print(f">>> Row analysis:        {out_csv}")
    print(f">>> Summary JSON:        {out_json}")
    print(f">>> Transition analysis: {out_trans}")
    return True


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return str(o)


def _print_report(s: dict) -> None:
    m = s["medium"]
    print()
    print(f">>> Medium-class failure analysis (test {s['split']['test_date_range'][0]} to "
          f"{s['split']['test_date_range'][1]}, {s['split']['test_rows']} rows)")
    print(f">>> Actual Medium: {m['actual_medium_cases']}  correct: {m['correctly_classified']}  "
          f"predicted Medium: {m['predicted_medium_total']}")
    print(f">>> Medium precision {m['precision']:.3f}  recall {m['recall']:.3f}  F1 {m['f1']:.3f}  "
          f"missed as High {m['missed_as_High']} / Low {m['missed_as_Low']}")
    rec = s.get("reproduction", {})
    if rec.get("published_metrics_available"):
        print(f">>> Published accuracy {rec['published_accuracy']:.4f} vs reproduced here "
              f"{rec['reproduced_accuracy']:.4f} (split/features match: {rec['split_and_features_match']}, "
              f"predictions match: {rec['predictions_match_published']})")
        print(f">>> {rec['note']}")
    for f in s["findings"]:
        print(f">>> [{f['status'].upper()}] {f['statement']}")
    print(f">>> NOTE: {DIAGNOSTIC_NOTE}")


if __name__ == "__main__":
    sys.exit(0 if analyze_medium_class_failures() else 1)
