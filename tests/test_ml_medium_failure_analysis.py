"""
tests/test_ml_medium_failure_analysis.py

Tests for src.ml.analyze_medium_class_failures (surrogate-label diagnostic).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import src.ml.analyze_medium_class_failures as m  # noqa: E402
from src.ml.train_irrigation_priority_model import TARGET, chronological_split  # noqa: E402


def make_df(n=200, seed=0, with_medium=True):
    """Synthetic dataset: depletion walks through Low -> Medium -> High regimes; labels from Ks."""
    rng = np.random.default_rng(seed)
    taw, raw = 150.0, 75.0
    dep = np.clip(np.concatenate([np.linspace(5, 70, n // 4), np.linspace(70, 150, n // 4),
                                  np.linspace(150, 60, n // 4), np.linspace(60, 150, n - 3 * (n // 4))]), 0, taw)
    ks = np.clip((taw - dep) / (taw - raw), 0, 1)
    labels = np.where(ks >= 0.9, "Low", np.where(ks >= 0.6, "Medium", "High"))
    if not with_medium:
        labels = np.where(labels == "Medium", "High", labels)
    return pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=n).strftime("%Y-%m-%d"),
        "temperature_avg_c": 25 + rng.normal(0, 2, n),
        "rainfall_mm": rng.exponential(1.0, n),
        "rainfall_7day_mm": rng.exponential(6.0, n),
        "etc_mm_day": 3 + rng.normal(0, .3, n),
        "mango_stage": "Flowering",
        "root_zone_depletion_mm": dep, "taw_mm": taw, "raw_mm": raw, "ks": ks,
        "water_stress_level": labels,
        TARGET: labels,
    })


# --- chronological splitting ------------------------------------------------

def test_split_matches_production_and_is_chronological():
    df = make_df().sample(frac=1, random_state=1)           # shuffled input
    tr, te = m.reproduce_split(df)
    ptr, pte = chronological_split(df.dropna(subset=[TARGET]))
    assert tr["date"].tolist() == ptr["date"].tolist() and te["date"].tolist() == pte["date"].tolist()
    assert pd.to_datetime(tr["date"]).max() < pd.to_datetime(te["date"]).min()
    assert len(tr) == 160 and len(te) == 40


def test_unlabelled_rows_dropped_from_split():
    df = make_df()
    df.loc[:9, TARGET] = np.nan
    tr, te = m.reproduce_split(df)
    assert len(tr) + len(te) == 190


# --- probability alignment ----------------------------------------------------

def test_probabilities_aligned_to_fixed_class_order_and_sum_to_one():
    from src.ml.train_irrigation_priority_model import build_pipeline, split_features_target
    tr, te = m.reproduce_split(make_df())
    X, y = split_features_target(tr)
    pipe = build_pipeline(X).fit(X, y)
    pr = m.align_proba(pipe, te[X.columns])
    assert list(pr.columns) == m.CLASSES and len(pr) == len(te)
    assert np.allclose(pr.sum(axis=1), 1.0)
    # column "High" really is the probability of High (not positional leakage from sklearn's order)
    assert pr.idxmax(axis=1).tolist() == pipe.predict(te[X.columns]).tolist()


def test_align_proba_fills_zero_for_class_unseen_in_training():
    from src.ml.train_irrigation_priority_model import build_pipeline, split_features_target
    df = make_df(with_medium=False)
    X, y = split_features_target(df)
    pr = m.align_proba(build_pipeline(X).fit(X, y), X)
    assert (pr["Medium"] == 0).all() and np.allclose(pr.sum(axis=1), 1.0)


# --- class transitions ---------------------------------------------------------

def test_label_context_and_transition_counts():
    lab = pd.Series(["Low", "Low", "Medium", "Medium", "High", "High", "High", "Medium"])
    ctx = m.label_context(lab)
    assert ctx["is_label_transition"].tolist() == [False, False, True, False, True, False, False, True]
    assert ctx["run_length_days"].tolist() == [2, 2, 2, 2, 3, 3, 3, 1]
    assert ctx["position_in_run"].tolist() == [1, 2, 1, 2, 1, 2, 3, 1]
    # backward-looking: first rows have no earlier change
    assert np.isnan(ctx["days_since_label_change"].iloc[0]) and ctx["days_since_label_change"].iloc[3] == 1
    assert ctx["days_to_next_label_change"].iloc[0] == 2 and np.isnan(ctx["days_to_next_label_change"].iloc[7])
    tc = m.transition_counts(lab).set_index(["from", "to"])["count"].to_dict()
    assert tc == {("Low", "Medium"): 1, ("Medium", "High"): 1, ("High", "Medium"): 1}


def test_signed_offset_to_nearest():
    off = m.signed_offset_to_nearest(np.array([False, True, False, False, False, True]))
    assert off.tolist() == [-1, 0, 1, 2, -1, 0] or off.tolist() == [-1, 0, 1, -2, -1, 0]
    assert np.isnan(m.signed_offset_to_nearest(np.zeros(3, bool))).all()


def test_ks_rule_label():
    assert [m.ks_rule_label(k) for k in (1.0, 0.9, 0.89, 0.6, 0.59, 0)] == ["Low", "Low", "Medium", "Medium", "High", "High"]
    assert m.ks_rule_label(np.nan) is None and m.ks_rule_label(None) is None


# --- zero division / empty Medium ---------------------------------------------

def test_class_prf_zero_predictions_is_safe():
    r = m.class_prf(["Medium", "Medium", "High"], ["High", "High", "High"])
    assert r["precision"] == 0.0 and r["precision_defined"] is False
    assert r["recall"] == 0.0 and r["f1"] == 0.0 and r["support"] == 2


def test_class_prf_no_medium_in_truth():
    r = m.class_prf(["High", "Low"], ["High", "Medium"])
    assert r["recall_defined"] is False and r["recall"] == 0.0
    assert r["precision"] == 0.0 and r["false_positives"] == 1
    assert m.safe_div(1, 0) == 0.0


def test_class_prf_perfect_and_mixed():
    assert m.class_prf(["Medium"] * 4, ["Medium"] * 4)["f1"] == 1.0
    r = m.class_prf(["Medium", "Medium", "Low", "Low"], ["Medium", "Low", "Medium", "Low"])
    assert (r["precision"], r["recall"], r["f1"]) == (0.5, 0.5, 0.5)


def test_analysis_runs_when_test_window_has_no_medium():
    df = make_df(with_medium=False)
    out = m.analyze_dataframe(df, run_experiments=False)
    summary, analysis, transitions = out
    assert summary["medium"]["actual_medium_cases"] == 0
    assert summary["findings"][0]["id"] == "no_medium_in_test"
    assert not analysis["is_actual_medium"].any() and len(transitions) > 0


def test_threshold_helpers():
    pr = pd.DataFrame({"Low": [.6, .2, .1], "Medium": [.1, .3, .2], "High": [.3, .5, .7]})
    assert m.apply_medium_threshold(pr, None).tolist() == ["Low", "High", "High"]
    assert m.apply_medium_threshold(pr, 0.25).tolist() == ["Low", "Medium", "High"]
    assert m.select_medium_threshold(["Low", "High", "High"], pr) is None      # no Medium in validation
    assert m.select_medium_threshold(["Low", "Medium", "High"], pr) is not None


# --- output schemas -------------------------------------------------------------

def _cfg(tmp_path, df):
    data = tmp_path / "ds.csv"
    if df is not None:
        df.to_csv(data, index=False)
    paths = {
        "ml_training_dataset_csv": data,
        "ml_medium_failure_analysis_csv": tmp_path / "out" / "a.csv",
        "ml_medium_failure_summary_json": tmp_path / "out" / "s.json",
        "ml_medium_transition_analysis_csv": tmp_path / "out" / "t.csv",
    }
    return SimpleNamespace(path=lambda k: paths[k]), paths


@pytest.fixture(scope="module")
def full_run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("mf")
    cfg, paths = _cfg(tmp, make_df(240))
    assert m.analyze_medium_class_failures(cfg) is True
    return paths


def test_row_csv_schema(full_run):
    a = pd.read_csv(full_run["ml_medium_failure_analysis_csv"])
    for col in ("date", "actual", "predicted", "proba_Low", "proba_Medium", "proba_High", "confidence",
                "correct", "is_actual_medium", "ks", "ks_rule_label", "label_matches_ks_rule",
                "water_stress_level", "month", "days_since_label_change", "temperature_avg_c"):
        assert col in a.columns
    assert len(a) == 48 and np.allclose(a[["proba_Low", "proba_Medium", "proba_High"]].sum(axis=1), 1.0)
    assert (a["confidence"] == a[["proba_Low", "proba_Medium", "proba_High"]].max(axis=1)).all()


def test_summary_json_schema(full_run):
    s = json.loads(full_run["ml_medium_failure_summary_json"].read_text())
    assert s["label_type"] == "surrogate_rule_based" and "field" in s["warning"].lower()
    for key in ("split", "leakage_checks", "medium", "confusion_matrix", "label_structure",
                "transition_windows", "ks_threshold_comparison", "error_clustering",
                "offline_experiments", "findings", "limitations"):
        assert key in s
    for key in ("actual_medium_cases", "correctly_classified", "precision", "recall", "f1",
                "missed_as_High", "missed_as_Low", "mean_confidence_all_medium_rows"):
        assert key in s["medium"]
    assert {f["status"] for f in s["findings"]} <= {"supported", "hypothesis"}
    assert any(f["status"] == "hypothesis" for f in s["findings"])
    assert all("evidence" in f and "statement" in f for f in s["findings"])
    assert all(v is True for v in s["leakage_checks"].values())


def test_transition_csv_schema(full_run):
    t = pd.read_csv(full_run["ml_medium_transition_analysis_csv"])
    assert {"kind", "key"} <= set(t.columns)
    assert {"transition_type", "window_around_label_change", "offset_from_medium"} <= set(t["kind"])


def test_experiments_present_and_flagged_offline(full_run):
    ex = json.loads(full_run["ml_medium_failure_summary_json"].read_text())["offline_experiments"]
    for name in ("majority_class_baseline", "persistence_previous_day_label", "rf_balanced_production",
                 "rf_no_class_weight", "rf_balanced_subsample", "logistic_regression_balanced",
                 "medium_probability_threshold"):
        assert name in ex
    assert "not adopted" in ex["medium_probability_threshold"]["note"].lower()
    for name, e in ex.items():
        if name.startswith("diagnostic_"):
            assert "DIAGNOSTIC ONLY" in e["note"]


def test_skips_when_dataset_missing_or_tiny(tmp_path):
    cfg, paths = _cfg(tmp_path, None)
    assert m.analyze_medium_class_failures(cfg) is False
    cfg2, _ = _cfg(tmp_path, make_df(30))
    assert m.analyze_medium_class_failures(cfg2) is False
    assert not paths["ml_medium_failure_summary_json"].exists()


# --- leakage prevention ------------------------------------------------------------

def test_leakage_checks_detect_problems():
    df = make_df()
    tr, te = m.reproduce_split(df)
    ok = m.check_no_leakage(tr, te, ["temperature_avg_c"])
    assert all(ok.values())
    bad = m.check_no_leakage(tr, te, ["temperature_avg_c", "ks", "target_water_stress_level"])
    assert not bad["features_exclude_label_determinants"] and not bad["features_exclude_targets"]
    overlap = m.check_no_leakage(tr, pd.concat([te, tr.iloc[[-1]]]), ["temperature_avg_c"])
    assert not overlap["no_date_overlap"] and not overlap["test_strictly_after_train"]


def test_model_features_exclude_analysis_columns():
    from src.ml.train_irrigation_priority_model import split_features_target
    tr, _ = m.reproduce_split(make_df())
    X, _ = split_features_target(tr)
    assert not (set(X.columns) & set(m.ANALYSIS_ONLY_COLUMNS))
    assert not (set(X.columns) & {"ks", "root_zone_depletion_mm", "taw_mm", "raw_mm", "water_stress_level"})


def test_future_labels_do_not_change_predictions():
    """Predictions for the test window must not depend on test labels (only on features)."""
    df = make_df(240)
    s1, a1, _ = m.analyze_dataframe(df, run_experiments=False)
    df2 = df.copy()
    n = len(df2)
    df2.loc[int(n * .8):, TARGET] = "High"           # scramble test labels only
    _, a2, _ = m.analyze_dataframe(df2, run_experiments=False)
    assert a1["predicted"].tolist() == a2["predicted"].tolist()
    assert np.allclose(a1["proba_Medium"], a2["proba_Medium"])


def test_threshold_selected_without_test_data():
    """Changing test-window labels must not change the validation-selected threshold."""
    df = make_df(240)
    tr, te = m.reproduce_split(df)
    base = m.run_offline_experiments(tr, te)["medium_probability_threshold"]["selected_threshold"]
    te2 = te.copy()
    te2[TARGET] = "High"
    again = m.run_offline_experiments(tr, te2)["medium_probability_threshold"]["selected_threshold"]
    assert base == again


def test_does_not_write_production_artifacts(tmp_path):
    cfg, paths = _cfg(tmp_path, make_df(240))
    m.analyze_medium_class_failures(cfg)
    written = {p.name for p in tmp_path.rglob("*") if p.is_file()}
    assert written == {"ds.csv", "a.csv", "s.json", "t.csv"}          # no model / metrics / importance
    src = (PROJECT_ROOT / "src" / "ml" / "analyze_medium_class_failures.py").read_text(encoding="utf-8")
    assert "joblib.dump" not in src
    # the published metrics path may only be READ (load_published_metrics), never written
    for line in src.splitlines():
        if "ml_model_metrics_json" in line:
            assert "read_text" in line and "write" not in line


# --- reproducibility / reconciliation with the trainer ------------------------------

def test_predictions_reproduce_trainer_exactly_in_same_environment():
    """The analysis must use the trainer's fitted pipeline: same split, features, seed, predictions."""
    from src.ml.train_irrigation_priority_model import split_features_target, train_and_evaluate
    df = make_df(240)
    pipe, metrics, _ = train_and_evaluate(df)
    summary, analysis, _ = m.analyze_dataframe(df, run_experiments=False)
    _, te = m.reproduce_split(df)
    X_train, _ = split_features_target(m.reproduce_split(df)[0])
    assert analysis["predicted"].tolist() == pipe.predict(te[X_train.columns]).tolist()
    assert analysis["actual"].tolist() == te[TARGET].tolist()
    labels = metrics["confusion_matrix"]["labels"]
    cm = [[int(((analysis["actual"] == a) & (analysis["predicted"] == b)).sum()) for b in labels] for a in labels]
    assert cm == metrics["confusion_matrix"]["matrix"]
    assert abs(analysis["correct"].mean() - metrics["accuracy"]) < 1e-12
    assert summary["leakage_checks"]["matches_trainer_in_this_environment"] is True


def test_analysis_is_deterministic_across_runs():
    df = make_df(240)
    _, a1, _ = m.analyze_dataframe(df, run_experiments=False)
    _, a2, _ = m.analyze_dataframe(df, run_experiments=False)
    assert a1["predicted"].tolist() == a2["predicted"].tolist()
    assert np.array_equal(a1[["proba_Low", "proba_Medium", "proba_High"]].to_numpy(),
                          a2[["proba_Low", "proba_Medium", "proba_High"]].to_numpy())


def _published_from(df):
    from src.ml.train_irrigation_priority_model import train_and_evaluate
    _, metrics, _ = train_and_evaluate(df)
    return json.loads(json.dumps(metrics, default=str))


def test_reconcile_reports_exact_match():
    df = make_df(240)
    rec = m.analyze_dataframe(df, run_experiments=False, published_metrics=_published_from(df))[0]["reproduction"]
    assert rec["split_and_features_match"] and rec["predictions_match_published"]
    assert "exactly" in rec["note"]
    assert set(rec["environment_this_run"]) == {"python", "scikit_learn", "numpy", "pandas"}
    assert rec["model_configuration"]["random_state"] == 42


def test_reconcile_flags_prediction_difference_as_environment_not_split():
    df = make_df(240)
    pub = _published_from(df)
    pub["accuracy"] -= 0.0147                              # simulate a different library version
    pub["confusion_matrix"]["matrix"][0][0] -= 1
    rec = m.analyze_dataframe(df, run_experiments=False, published_metrics=pub)[0]["reproduction"]
    assert rec["split_and_features_match"] is True and rec["predictions_match_published"] is False
    assert "library versions" in rec["note"]


def test_reconcile_flags_split_or_feature_mismatch():
    df = make_df(240)
    pub = _published_from(df)
    pub["test_date_range"] = ["1999-01-01", "1999-02-01"]
    rec = m.analyze_dataframe(df, run_experiments=False, published_metrics=pub)[0]["reproduction"]
    assert rec["split_and_features_match"] is False and rec["split_checks"]["test_date_range"] is False
    pub2 = _published_from(df)
    pub2["features"] = pub2["features"][:-1]
    rec2 = m.analyze_dataframe(df, run_experiments=False, published_metrics=pub2)[0]["reproduction"]
    assert rec2["split_checks"]["feature_list"] is False


def test_reconcile_without_published_metrics():
    rec = m.reconcile_with_published(None, {})
    assert rec["published_metrics_available"] is False


def test_published_metrics_are_read_only(tmp_path):
    pub = tmp_path / "metrics.json"
    pub.write_text(json.dumps({"accuracy": 0.5}))
    before = pub.read_bytes()
    cfg = SimpleNamespace(path=lambda k: pub if k == "ml_model_metrics_json" else tmp_path / k)
    assert m.load_published_metrics(cfg) == {"accuracy": 0.5}
    assert pub.read_bytes() == before
    assert m.load_published_metrics(SimpleNamespace(path=lambda k: tmp_path / "nope.json")) is None


def test_file_hash_ignores_line_endings(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    a.write_bytes(b"x,y\n1,2\n")
    b.write_bytes(b"x,y\r\n1,2\r\n")
    assert m.file_sha256_normalised(a) == m.file_sha256_normalised(b)
    assert m.file_sha256_normalised(tmp_path / "missing") is None


PUBLISHED = PROJECT_ROOT / "data" / "processed" / "muthukur_ml_model_metrics.json"
DATASET = PROJECT_ROOT / "data" / "processed" / "muthukur_ml_training_dataset.csv"


@pytest.mark.skipif(not (PUBLISHED.exists() and DATASET.exists()), reason="real artifacts not available")
def test_real_split_and_features_match_published_metrics():
    """Environment-independent facts must match the published evaluation (accuracy may differ
    across scikit-learn versions, so it is deliberately not asserted here)."""
    pub = json.loads(PUBLISHED.read_text(encoding="utf-8"))
    df = pd.read_csv(DATASET)
    if pub.get("train_rows") != int(len(df.dropna(subset=[TARGET])) * 0.8):
        pytest.skip("published metrics were produced from a different dataset snapshot")
    rec = m.analyze_dataframe(df, run_experiments=False, published_metrics=pub)[0]["reproduction"]
    assert rec["split_and_features_match"], rec["split_checks"]


def test_config_paths_for_new_outputs():
    from src.utils.config import get_config
    cfg = get_config()
    expected = {
        "ml_medium_failure_analysis_csv": "muthukur_ml_medium_failure_analysis.csv",
        "ml_medium_failure_summary_json": "muthukur_ml_medium_failure_summary.json",
        "ml_medium_transition_analysis_csv": "muthukur_ml_medium_transition_analysis.csv",
    }
    for key, name in expected.items():
        p = Path(cfg.path(key))
        assert p.name == name and p.parent.name == "processed", key
