"""
tests/test_ml_backtest.py

Tests for src.ml.backtest_irrigation_priority_model (expanding-window
chronological backtest of the surrogate-label classifier).
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

from src.ml.backtest_irrigation_priority_model import (
    backtest_irrigation_priority_model,
    compute_metrics,
    evaluate_fold,
    fold_results_frame,
    make_expanding_folds,
    run_backtest,
)
from src.ml.train_irrigation_priority_model import TARGET

CLASSES = ["High", "Low", "Medium"]


def _dataset(n=200, seed=0, labels=None):
    rng = np.random.default_rng(seed)
    temp = rng.normal(28, 4, n)
    if labels is None:
        labels = np.where(temp > 29, "High", np.where(temp > 26, "Medium", "Low"))
    return pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=n).strftime("%Y-%m-%d"),
        "temperature_avg_c": temp,
        "rainfall_mm": rng.exponential(2, n),
        "mango_stage": rng.choice(["Flowering", "Fruit set"], n),
        "ks": 1.0,                        # leakage column, must stay excluded
        "water_stress_level": "Low",      # leakage column, must stay excluded
        TARGET: labels,
    })


# 1/2. Chronological ordering and non-overlapping test periods ----------------

def test_folds_are_chronological_and_non_overlapping():
    folds = make_expanding_folds(200, n_folds=4, initial_train_fraction=0.5)
    assert len(folds) == 4
    seen_test = set()
    prev_stop = None
    for train_idx, test_idx in folds:
        assert train_idx.max() < test_idx.min()                  # train strictly before test
        assert np.array_equal(train_idx, np.arange(len(train_idx)))  # expanding from the start
        assert not (seen_test & set(test_idx))                   # no overlap between test blocks
        if prev_stop is not None:
            assert test_idx.min() == prev_stop                   # contiguous, in order
        prev_stop = test_idx.max() + 1
        seen_test |= set(test_idx)
    assert prev_stop == 200
    sizes = [len(f[0]) for f in folds]
    assert sizes == sorted(sizes) and len(set(sizes)) == len(sizes)  # train windows expand


def test_backtest_handles_shuffled_input_and_dates_do_not_overlap():
    shuffled = _dataset().sample(frac=1, random_state=3)
    summary, preds = run_backtest(shuffled)
    for f in summary["folds"]:
        assert f["train_end"] < f["test_start"]
    ends = [f["test_end"] for f in summary["folds"]]
    starts = [f["test_start"] for f in summary["folds"]]
    for prev_end, next_start in zip(ends[:-1], starts[1:]):
        assert prev_end < next_start
    assert preds["date"].is_unique                                # each date predicted once


# 3. Preprocessing is fitted on training data only ---------------------------

def test_preprocessing_statistics_come_from_training_fold_only():
    df = _dataset(100)
    df.loc[60:, "temperature_avg_c"] = 1000.0          # extreme values only in the test period
    df.loc[10, "temperature_avg_c"] = np.nan
    train, test = df.iloc[:60], df.iloc[60:]
    _, _, pipe = evaluate_fold(1, train, test, CLASSES)
    pre = pipe.named_steps["preprocess"]
    num_cols = list(pre.transformers_[0][2])
    imputer = pre.named_transformers_["num"]
    got = imputer.statistics_[num_cols.index("temperature_avg_c")]
    assert got == pytest.approx(train["temperature_avg_c"].median())
    assert got < 100                                    # test-period 1000s did not leak in


def test_feature_columns_selected_from_training_fold_only():
    df = _dataset(100)
    df["only_in_future"] = np.nan
    df.loc[70:, "only_in_future"] = 5.0
    result, _, pipe = evaluate_fold(1, df.iloc[:60], df.iloc[60:], CLASSES)
    assert "only_in_future" not in pipe.feature_names_in_
    assert "ks" not in pipe.feature_names_in_ and "water_stress_level" not in pipe.feature_names_in_


# 4/5. Missing classes and metric reporting ----------------------------------

def test_absent_classes_are_reported_and_metrics_split():
    labels = ["Low"] * 90 + ["Medium"] * 10 + ["High"] * 100   # test blocks hold only "High"
    summary, _ = run_backtest(_dataset(labels=np.array(labels)))
    assert summary["classes"] == ["High", "Low", "Medium"]
    for f in summary["folds"]:
        assert f["classes_absent_from_test"] == ["Low", "Medium"]
        assert f["test_class_distribution"]["Low"] == 0
    # first training block (rows 0-99) has never seen "High"
    assert summary["folds"][0]["classes_absent_from_train"] == ["High"]
    assert summary["folds"][1]["classes_absent_from_train"] == []
    assert summary["folds_with_single_class_test"] == 4
    assert summary["folds_with_absent_test_classes"] == 4
    m = summary["folds"][-1]["model"]
    # absent classes count as 0 in the fixed-class macro, so it cannot exceed present-class
    assert m["f1_macro_fixed"] <= m["f1_macro_present"]
    assert m["recall_macro_fixed"] <= m["recall_macro_present"] / 3 + 1e-12


def test_compute_metrics_fixed_vs_present():
    y_true = ["High"] * 4
    y_pred = ["High", "High", "High", "Low"]
    m = compute_metrics(y_true, y_pred, CLASSES)
    assert m["accuracy"] == 0.75
    assert m["recall_macro_present"] == 0.75                # only "High" is present
    assert m["recall_macro_fixed"] == pytest.approx(0.75 / 3)  # absent classes count as 0
    assert m["balanced_accuracy"] == 0.75


def test_confusion_matrix_uses_consistent_class_order_in_every_fold():
    summary, _ = run_backtest(_dataset())
    for f in summary["folds"]:
        assert f["confusion_matrix"]["labels"] == summary["classes"]
        assert f["baseline_confusion_matrix"]["labels"] == summary["classes"]
        assert np.array(f["confusion_matrix"]["matrix"]).sum() == f["test_rows"]


def test_summary_reports_required_fields_and_surrogate_warning():
    summary, preds = run_backtest(_dataset())
    assert summary["label_type"] == "surrogate_rule_based"
    assert "surrogate" in summary["warning"].lower()
    assert "not field" in summary["interpretation_note"].lower()
    assert {"fold", "date", "actual", "predicted", "baseline_predicted"} <= set(preds.columns)
    for f in summary["folds"]:
        for who in ("model", "baseline"):
            for key in ("accuracy", "balanced_accuracy", "precision_macro_fixed",
                        "recall_macro_fixed", "f1_macro_fixed", "f1_macro_present"):
                assert key in f[who]
    flat = fold_results_frame(summary)
    assert len(flat) == summary["n_folds"]
    assert "baseline_accuracy" in flat.columns and "model_f1_macro_present" in flat.columns


# 6. Majority-class baseline and class imbalance -----------------------------

def test_majority_baseline_predicts_most_frequent_training_class():
    labels = ["High"] * 160 + ["Low"] * 40
    summary, preds = run_backtest(_dataset(labels=np.array(labels)))
    for f in summary["folds"]:
        assert f["majority_class_baseline_prediction"] == "High"
    assert (preds["baseline_predicted"] == "High").all()


def test_class_imbalance_baseline_scores_high_accuracy_but_low_balanced_accuracy():
    rng = np.random.default_rng(1)
    labels = np.array(["High"] * 190 + ["Low"] * 10)
    rng.shuffle(labels)
    summary, _ = run_backtest(_dataset(labels=labels))
    base = summary["mean_baseline_metrics"]
    assert base["accuracy"] > 0.85                        # accuracy flatters the majority class
    assert base["balanced_accuracy"] < base["accuracy"]
    assert summary["mean_accuracy_minus_baseline"] is not None


# 7. Insufficient data --------------------------------------------------------

def test_insufficient_data_returns_none():
    assert make_expanding_folds(20) == []
    assert run_backtest(_dataset(20)) is None
    assert run_backtest(pd.DataFrame({"date": [], TARGET: []})) is None
    assert run_backtest(_dataset().drop(columns=[TARGET])) is None


def _config(tmp_path, df):
    data = tmp_path / "ds.csv"
    df.to_csv(data, index=False)
    paths = {
        "ml_training_dataset_csv": data,
        "ml_backtest_folds_csv": tmp_path / "out" / "folds.csv",
        "ml_backtest_predictions_csv": tmp_path / "out" / "preds.csv",
        "ml_backtest_summary_json": tmp_path / "out" / "summary.json",
    }
    return SimpleNamespace(path=lambda k: paths[k]), paths


def test_end_to_end_writes_outputs(tmp_path):
    cfg, paths = _config(tmp_path, _dataset())
    assert backtest_irrigation_priority_model(cfg) is True
    summary = json.loads(paths["ml_backtest_summary_json"].read_text())
    assert summary["label_type"] == "surrogate_rule_based"
    assert pd.read_csv(paths["ml_backtest_folds_csv"]).shape[0] == summary["n_folds"]
    assert pd.read_csv(paths["ml_backtest_predictions_csv"]).shape[0] > 0


def test_skips_gracefully_when_dataset_missing_or_small(tmp_path):
    cfg, paths = _config(tmp_path, _dataset(20))
    assert backtest_irrigation_priority_model(cfg) is False
    assert not paths["ml_backtest_summary_json"].exists()
    paths["ml_training_dataset_csv"].unlink()
    assert backtest_irrigation_priority_model(cfg) is False
