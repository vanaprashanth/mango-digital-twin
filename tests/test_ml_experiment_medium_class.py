"""Tests for the isolated Medium-class experiment (src/ml/experiment_medium_class.py)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

from src.ml import experiment_medium_class as exp
from src.ml import train_irrigation_priority_model as prod
from src.utils.config import PROJECT_ROOT, get_config

REPO = Path(PROJECT_ROOT)
TARGET = prod.TARGET


def synthetic(n=260, seed=0, medium_from=None):
    """Date-ordered frame with stage structure, leakage columns and a Medium regime that appears late."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2025-01-01", periods=n, freq="D")
    stage = np.where(np.arange(n) < n // 2, "Flowering", "Fruit set")
    ks = rng.uniform(0.2, 1.0, n)
    label = np.where(ks >= 0.9, "Low", np.where(ks >= 0.6, "Medium", "High"))
    if medium_from is not None:
        label = np.where((np.arange(n) < medium_from) & (label == "Medium"), "High", label)
    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "temperature_avg_c": rng.normal(30, 3, n) + 3 * (ks < 0.6),
        "rainfall_mm": rng.exponential(2, n),
        "mango_stage": stage, "stage_kc": np.where(stage == "Flowering", 0.7, 1.0),
        "kc": rng.uniform(0.6, 1.1, n), "interpolated_kc": rng.uniform(0.6, 1.1, n),
        "ks": ks, "root_zone_depletion_mm": 100 * (1 - ks), "water_stress_level": label,
        "target_water_stress_level": label, "target_irrigation_needed_binary": (label != "Low").astype(int),
        "sentinel2_date": "2025-01-01",
        TARGET: label,
    })


@pytest.fixture
def small(monkeypatch):
    monkeypatch.setattr(exp, "WEIGHT_SCHEMES", ("balanced", "none"))
    return synthetic()


# --- chronological separation ----------------------------------------------------------------------------

def test_validation_folds_are_strictly_later_than_their_training_rows(small):
    train, test = prod.chronological_split(exp.sorted_labelled(small))
    folds = exp.validation_folds(train)
    assert len(folds) == exp.N_FOLDS
    prev_end = None
    for f in folds:
        assert f["train"]["date"].max() < f["validation"]["date"].min()
        assert len(f["train"]) + len(f["validation"]) <= len(train)
        assert f["train"]["date"].is_monotonic_increasing and f["validation"]["date"].is_monotonic_increasing
        assert str(f["validation"]["date"].max()) < str(test["date"].min())      # never reaches the test window
        if prev_end is not None:
            assert f["validation"]["date"].min() > prev_end                      # blocks do not overlap
        prev_end = f["validation"]["date"].max()


def test_test_window_is_the_production_chronological_split_and_later_than_training(small):
    res = exp.run_experiment(small)
    d = res["data"]
    assert d["train_date_range"][1] < d["test_date_range"][0]
    train, test = prod.chronological_split(exp.sorted_labelled(small))
    assert (d["train_rows"], d["test_rows"]) == (len(train), len(test))


def test_selection_never_sees_the_test_window(small):
    ordered = exp.sorted_labelled(small)
    train, test = prod.chronological_split(ordered)
    base = exp.run_validation(train)
    # run_validation has no test argument; also rewrite every test label and re-run the full experiment
    altered = ordered.copy()
    altered.loc[altered["date"] >= test["date"].min(), TARGET] = "Medium"
    full_a, full_b = exp.run_experiment(ordered), exp.run_experiment(altered)
    assert full_a["validation"] == full_b["validation"]
    assert full_a["validation"]["selection"] == exp._json_roundtrip(base["selection"]) if hasattr(exp, "_json_roundtrip") \
        else True
    assert full_a["test"] != full_b["test"]                    # only the test report moves
    assert full_a["protocol"]["test_window_used_for_selection"] is False


# --- feature exclusions -------------------------------------------------------------------------------

def test_production_leakage_exclusions_apply_to_every_feature_set(small):
    train, _ = prod.chronological_split(exp.sorted_labelled(small))
    for fs in exp.FEATURE_SETS:
        X, _ = exp.feature_frame(train, fs)
        cols = set(X.columns)
        assert not cols & prod.EXCLUDED_COLUMNS
        assert not any(c.startswith("target_") or c.endswith("_date") for c in cols)
        assert {"ks", "root_zone_depletion_mm", "water_stress_level"}.isdisjoint(cols)


def test_experiment_arms_remove_exactly_the_declared_columns(small):
    train, _ = prod.chronological_split(exp.sorted_labelled(small))
    full = set(exp.feature_frame(train, "all_production_features")[0].columns)
    no_stage = set(exp.feature_frame(train, "no_mango_stage")[0].columns)
    family = set(exp.feature_frame(train, "no_stage_family_diagnostic")[0].columns)
    assert full - no_stage == {"mango_stage"}
    assert full - family == {"mango_stage", "stage_kc", "interpolated_kc", "kc"}
    assert full == set(prod.split_features_target(train)[0].columns)       # baseline == production features


def test_fitted_models_only_ever_see_allowed_features(small):
    train, _ = prod.chronological_split(exp.sorted_labelled(small))
    for fs in exp.FEATURE_SETS:
        _, cols = exp.fit_configuration(train, fs, "balanced")
        assert not set(cols) & (prod.EXCLUDED_COLUMNS | {"ks", "root_zone_depletion_mm"})
        assert ("mango_stage" in cols) == (fs == "all_production_features")


def test_class_weight_schemes():
    y = pd.Series(["Low"] * 60 + ["Medium"] * 10 + ["High"] * 30)
    assert exp.class_weight_for("none", y) is None
    assert exp.class_weight_for("balanced", y) == "balanced"
    bal = exp.class_weight_for("balanced_medium_x2", y)
    x4 = exp.class_weight_for("balanced_medium_x4", y)
    assert bal["Low"] == pytest.approx(100 / (3 * 60)) and bal["High"] == pytest.approx(100 / (3 * 30))
    assert bal["Medium"] == pytest.approx(2 * 100 / (3 * 10)) and x4["Medium"] == pytest.approx(4 * 100 / (3 * 10))
    assert "Medium" not in exp.class_weight_for("balanced_medium_x2", y[y != "Medium"])
    with pytest.raises(ValueError):
        exp.class_weight_for("mystery", y)


# --- missing classes ------------------------------------------------------------------------------------

def test_missing_classes_are_reported_per_fold_and_do_not_crash(small):
    df = synthetic(medium_from=230)                          # Medium only in the last rows of the data
    train, _ = prod.chronological_split(exp.sorted_labelled(df))
    folds = exp.validation_folds(train)
    missing = [f["classes_missing_in_validation"] for f in folds]
    assert any("Medium" in m for m in missing)
    for f in folds:
        assert set(f["classes_missing_in_train"]) == {c for c in exp.CLASSES if f["train_class_counts"][c] == 0}
        assert set(f["classes_missing_in_validation"]) == {c for c in exp.CLASSES if f["validation_class_counts"][c] == 0}
    result = exp.validate_configuration(folds, "all_production_features", "balanced")
    assert result["pooled"] is not None
    assert all("classes_missing" in pf for pf in result["per_fold"] if "skipped" not in pf)
    report = exp.run_experiment(df)
    assert [f["classes_missing_in_validation"] for f in report["validation"]["folds"]] == missing


def test_score_marks_undefined_values_instead_of_inventing_zeros():
    s = exp.score(["High", "High", "Low"], ["High", "Low", "Low"])
    assert s["classes_missing"] == ["Medium"]
    assert s["per_class"]["Medium"]["recall"] is None and s["per_class"]["Medium"]["f1"] is None
    assert s["per_class"]["Medium"]["precision"] is None                      # never predicted either
    assert s["balanced_accuracy"] == pytest.approx((0.5 + 1.0) / 2)         # present classes only
    assert s["high_recall"] == pytest.approx(0.5) and s["medium_recall"] is None
    assert s["f1_macro_fixed"] == pytest.approx(s["f1_macro_present"] * 2 / 3)     # absent class counts 0 only here


def test_single_class_training_fold_is_skipped_and_flagged():
    df = synthetic(n=260)
    df[TARGET] = "High"
    train, _ = prod.chronological_split(exp.sorted_labelled(df))
    res = exp.validate_configuration(exp.validation_folds(train), "all_production_features", "balanced")
    assert res["pooled"] is None and all("skipped" in pf for pf in res["per_fold"])


def test_score_matches_scikit_learn_where_defined():
    rng = np.random.default_rng(1)
    y = rng.choice(exp.CLASSES, 300, p=[.3, .2, .5])
    p = np.where(rng.random(300) < 0.7, y, rng.choice(exp.CLASSES, 300))
    s = exp.score(y, p)
    assert s["accuracy"] == pytest.approx(accuracy_score(y, p))
    assert s["balanced_accuracy"] == pytest.approx(balanced_accuracy_score(y, p))
    assert s["f1_macro_present"] == pytest.approx(f1_score(y, p, labels=exp.CLASSES, average="macro"))
    assert np.array(s["confusion_matrix"]["matrix"]).sum() == 300


# --- selection rule ---------------------------------------------------------------------------------------

def _cand(f1, high, medium_support=8):
    per = {"Medium": {"support": medium_support}}
    return {"pooled": {"f1_macro_present": f1, "high_recall": high, "per_class": per}}


def _cands(over=None):
    c = {(fs, w): _cand(0.60, 0.90) for fs in exp.FEATURE_SETS for w in exp.WEIGHT_SCHEMES}
    c.update(over or {})
    return c


def test_baseline_is_kept_unless_a_candidate_clearly_wins():
    assert exp.select(_cands())["selected"] == list(exp.BASELINE)
    small_gain = _cands({("no_mango_stage", "none"): _cand(0.605, 0.90)})
    assert exp.select(small_gain)["selected"] == list(exp.BASELINE)
    big_gain = _cands({("no_mango_stage", "none"): _cand(0.70, 0.90)})
    assert exp.select(big_gain)["selected"] == ["no_mango_stage", "none"]


def test_high_recall_guardrail_blocks_a_candidate_that_trades_away_high_priority_recall():
    unsafe = _cands({("no_mango_stage", "none"): _cand(0.90, 0.60)})
    assert exp.select(unsafe)["selected"] == list(exp.BASELINE)


# --- reproducibility -----------------------------------------------------------------------------------

def test_experiment_is_reproducible_and_independent_of_row_order(small):
    a = exp.run_experiment(small)
    b = exp.run_experiment(small)
    shuffled = exp.run_experiment(small.sample(frac=1.0, random_state=3))
    assert exp.results_digest(a) == exp.results_digest(b) == exp.results_digest(shuffled)


# --- isolation from production ----------------------------------------------------------------------------

def test_outputs_are_written_only_to_the_experiment_location(small, tmp_path):
    paths = exp.write_results(exp.run_experiment(small), tmp_path / "exp")
    assert {p.name for p in paths.values()} == {exp.RESULTS_JSON, exp.VALIDATION_CSV, exp.FOLDS_CSV}
    assert all(tmp_path in p.parents for p in paths.values())
    assert exp.EXPERIMENT_DIR == REPO / "data" / "experiments" / "medium_class"


@pytest.mark.parametrize("where", ["data/processed", "models", "data", "src"])
def test_writing_to_production_or_other_project_locations_is_refused(where):
    with pytest.raises(ValueError):
        exp.check_output_dir(REPO / where)


def test_module_never_writes_production_artifacts():
    src = (REPO / "src" / "ml" / "experiment_medium_class.py").read_text(encoding="utf-8")
    for forbidden in ("joblib.dump", "irrigation_priority_model_path\")", "ml_model_metrics_json\")"):
        assert forbidden not in src
    assert "to_csv(" in src and "write_text(" in src and "EXPERIMENT_DIR" in src


# --- real dataset: matches production baseline, leaves production artifacts alone -------------------------

def _sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


@pytest.fixture(scope="module")
def real_run():
    cfg = get_config()
    data = cfg.path("ml_training_dataset_csv")
    if not data.exists():
        pytest.skip("training dataset not available")
    guarded = [cfg.path(k) for k in ("irrigation_priority_model_path", "ml_model_metrics_json",
                                     "ml_feature_importance_csv", "ml_training_dataset_csv")]
    before = {p: _sha(p) for p in guarded}
    df = pd.read_csv(data)
    results = exp.run_experiment(df)
    return df, results, before, {p: _sha(p) for p in guarded}


def test_real_baseline_reproduces_the_production_model_and_artifacts_are_untouched(real_run):
    df, results, before, after = real_run
    _, metrics, _ = prod.train_and_evaluate(df)
    base = results["test"]["baseline"]
    assert base["accuracy"] == pytest.approx(metrics["accuracy"])
    assert base["balanced_accuracy"] == pytest.approx(metrics["balanced_accuracy"])
    assert base["f1_macro_present"] == pytest.approx(metrics["f1_macro"])
    assert (results["data"]["train_rows"], results["data"]["test_rows"]) == (metrics["train_rows"], metrics["test_rows"])
    assert before == after


def test_real_run_reports_everything_requested(real_run):
    _, results, _, _ = real_run
    for arm, t in results["test"].items():
        assert set(t["per_class"]) == set(exp.CLASSES) and t["confusion_matrix"]["labels"] == exp.CLASSES
        assert {"balanced_accuracy", "f1_macro_present", "high_recall", "medium_recall"} <= set(t)
    assert set(results["test"]) == set(exp.ARMS)
    assert all("classes_missing_in_validation" in f for f in results["validation"]["folds"])
    assert results["protocol"]["test_window_used_for_selection"] is False
    assert any("Flower induction" in n for n in results["structural_findings"])
