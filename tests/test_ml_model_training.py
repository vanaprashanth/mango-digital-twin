"""
tests/test_ml_model_training.py

Tests for src.ml.train_irrigation_priority_model (surrogate-label prototype).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ml.train_irrigation_priority_model import (
    TARGET,
    chronological_split,
    split_features_target,
    train_irrigation_priority_model,
)


def _synthetic(n=120, with_optional=True):
    rng = np.random.default_rng(0)
    temp = rng.normal(28, 4, n)
    df = pd.DataFrame({
        "date": pd.date_range("2025-01-01", periods=n).strftime("%Y-%m-%d"),
        "temperature_avg_c": temp,
        "rainfall_mm": rng.exponential(2, n),
        "mango_stage": rng.choice(["Flowering", "Fruit set"], n),
        "water_stress_level": "Low",       # leakage column, must be excluded
        "ks": 1.0,                          # leakage column, must be excluded
        "root_zone_depletion_mm": 5.0,      # leakage column, must be excluded
        "sentinel2_date": "2025-01-01",     # raw observation date, excluded
    })
    df[TARGET] = np.where(temp > 28, "High", np.where(temp > 25, "Medium", "Low"))
    df["target_water_stress_level"] = df[TARGET]
    df["target_irrigation_needed_binary"] = (df[TARGET] == "High").astype(int)
    if with_optional:
        df["ndvi_mean"] = rng.uniform(0.3, 0.8, n)
        df.loc[::7, "ndvi_mean"] = np.nan
    return df


def _config(tmp_path, df):
    data = tmp_path / "ds.csv"
    df.to_csv(data, index=False)
    paths = {
        "ml_training_dataset_csv": data,
        "irrigation_priority_model_path": tmp_path / "models" / "m.joblib",
        "ml_model_metrics_json": tmp_path / "metrics.json",
        "ml_feature_importance_csv": tmp_path / "imp.csv",
    }
    return SimpleNamespace(path=lambda k: paths[k]), paths


def test_feature_target_split_excludes_targets_and_leakage():
    X, y = split_features_target(_synthetic())
    assert not any(c.startswith("target_") for c in X.columns)
    for bad in ("date", "water_stress_level", "ks", "root_zone_depletion_mm", "sentinel2_date"):
        assert bad not in X.columns
    assert {"temperature_avg_c", "rainfall_mm", "mango_stage"} <= set(X.columns)
    assert y.name == TARGET


def test_chronological_split_order_and_ratio():
    df = _synthetic(100).sample(frac=1, random_state=1)  # shuffled input
    train, test = chronological_split(df)
    assert len(train) == 80 and len(test) == 20
    assert train["date"].is_monotonic_increasing and test["date"].is_monotonic_increasing
    assert train["date"].max() < test["date"].min()


def test_training_on_synthetic_dataset_and_artifacts(tmp_path):
    cfg, paths = _config(tmp_path, _synthetic())
    assert train_irrigation_priority_model(cfg) is True
    assert paths["irrigation_priority_model_path"].exists()

    metrics = json.loads(paths["ml_model_metrics_json"].read_text())
    assert metrics["label_type"] == "surrogate_rule_based"
    assert "surrogate" in metrics["warning"].lower()
    assert metrics["train_rows"] == 96 and metrics["test_rows"] == 24
    for key in ("accuracy", "balanced_accuracy", "precision_macro", "recall_macro",
                "f1_macro", "classification_report", "confusion_matrix",
                "target_distribution", "trained_at", "model_type", "feature_count"):
        assert key in metrics

    imp = pd.read_csv(paths["ml_feature_importance_csv"])
    assert list(imp.columns) == ["feature", "importance"]
    assert len(imp) > 0
    assert imp["importance"].is_monotonic_decreasing
    assert not any("water_stress_level" in f or f == "ks" for f in imp["feature"])


def test_missing_optional_columns_do_not_break_training(tmp_path):
    cfg, _ = _config(tmp_path, _synthetic(with_optional=False))
    assert train_irrigation_priority_model(cfg) is True


def test_too_small_dataset_skipped_gracefully(tmp_path):
    cfg, paths = _config(tmp_path, _synthetic(n=20))
    assert train_irrigation_priority_model(cfg) is False
    assert not paths["irrigation_priority_model_path"].exists()


def test_missing_dataset_skipped_gracefully(tmp_path):
    paths = {k: tmp_path / k for k in (
        "ml_training_dataset_csv", "irrigation_priority_model_path",
        "ml_model_metrics_json", "ml_feature_importance_csv")}
    cfg = SimpleNamespace(path=lambda k: paths[k])
    assert train_irrigation_priority_model(cfg) is False
