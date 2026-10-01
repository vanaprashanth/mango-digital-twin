"""
tests/test_ml_training_dataset.py

Tests for src.ml.build_ml_training_dataset (dataset builder only; the
target columns are surrogate labels, not field-validated).

1. one row per date
2. FAO-56 fields join correctly
3. irrigation history features
4. target_irrigation_needed_binary derivation
5. missing optional Sentinel columns don't break the builder
6. output sorted by date
7. duplicate dates handled safely
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ml.build_ml_training_dataset import build_dataset_frame


def _features(dates, with_sentinel=True):
    df = pd.DataFrame({
        "date": dates,
        "temperature_avg_c": 25.0,
        "rainfall_mm": 0.0,
        "relative_humidity_percent": 60.0,
        "irrigation_risk_score": 0.5,
        "irrigation_risk_level": "Medium",
    })
    if with_sentinel:
        df["ndvi_mean"] = 0.6
        df["days_since_sentinel2_observation"] = 3
        df["vv_mean"] = -10.0
        df["sentinel1_freshness_level"] = "Fresh"
    return df


def _fao(dates, stress):
    n = len(dates)
    return pd.DataFrame({
        "date": dates,
        "mango_stage": ["Fruit set"] * n,
        "stage_kc": 0.8,
        "interpolated_kc": 0.8,
        "et0_mm_day": 5.0,
        "etc_mm_day": 4.0,
        "rainfall_mm": 0.0,
        "irrigation_mm": 0.0,
        "water_input_mm": 0.0,
        "root_zone_depletion_mm": np.arange(n, dtype=float) * 10,
        "ks": 0.9,
        "water_stress_level": stress,
    })


def _events(rows):
    return pd.DataFrame(
        [(pd.Timestamp(d), mm, "drip", "t", "") for d, mm in rows],
        columns=["date", "irrigation_mm", "method", "source", "notes"],
    )


DATES = pd.date_range("2026-01-01", periods=3).strftime("%Y-%m-%d").tolist()


def test_one_row_per_date():
    out = build_dataset_frame(_features(DATES), _fao(DATES, ["Low", "Medium", "High"]))
    assert len(out) == 3
    assert out["date"].is_unique


def test_fao56_fields_join():
    out = build_dataset_frame(_features(DATES), _fao(DATES, ["Low", "Medium", "High"]))
    assert out["root_zone_depletion_mm"].tolist() == [0.0, 10.0, 20.0]
    assert out["kc"].tolist() == [0.8] * 3
    assert out["water_stress_level"].tolist() == ["Low", "Medium", "High"]
    assert {"et0_mm_day", "etc_mm_day", "ks", "irrigation_mm", "water_input_mm"} <= set(out.columns)


def test_irrigation_history_features():
    dates = pd.date_range("2026-01-01", periods=20).strftime("%Y-%m-%d").tolist()
    events = _events([("2026-01-05", 20.0), ("2026-01-15", 10.0)])
    out = build_dataset_frame(_features(dates), _fao(dates, ["Low"] * 20), events)
    by = out.set_index("date")

    assert np.isnan(by.loc["2026-01-04", "days_since_last_irrigation"])
    assert by.loc["2026-01-05", "days_since_last_irrigation"] == 0
    assert by.loc["2026-01-10", "days_since_last_irrigation"] == 5
    assert by.loc["2026-01-17", "days_since_last_irrigation"] == 2

    assert by.loc["2026-01-10", "irrigation_last_7d_mm"] == 20.0
    assert by.loc["2026-01-11", "irrigation_last_7d_mm"] == 20.0
    assert by.loc["2026-01-12", "irrigation_last_7d_mm"] == 0.0   # Jan 5 left the window
    assert by.loc["2026-01-15", "irrigation_last_7d_mm"] == 10.0
    assert by.loc["2026-01-18", "irrigation_last_14d_mm"] == 30.0
    assert by.loc["2026-01-20", "irrigation_last_14d_mm"] == 10.0  # day 5 is 15 days back
    assert by.loc["2026-01-04", "irrigation_event_count_last_30d"] == 0
    assert by.loc["2026-01-20", "irrigation_event_count_last_30d"] == 2


def test_no_events_gives_neutral_history():
    out = build_dataset_frame(_features(DATES), _fao(DATES, ["Low"] * 3), _events([]))
    assert out["days_since_last_irrigation"].isna().all()
    assert (out["irrigation_last_7d_mm"] == 0).all()
    assert (out["irrigation_event_count_last_30d"] == 0).all()


def test_targets_derived_from_stress():
    out = build_dataset_frame(_features(DATES), _fao(DATES, ["Low", "Medium", "High"]))
    assert out["target_water_stress_level"].tolist() == ["Low", "Medium", "High"]
    assert out["target_irrigation_priority"].tolist() == ["Low", "Medium", "High"]
    assert out["target_irrigation_needed_binary"].tolist() == [0, 0, 1]


def test_missing_stress_gives_missing_target():
    out = build_dataset_frame(_features(DATES), _fao(DATES, ["Low", None, "High"]))
    assert pd.isna(out.loc[1, "target_irrigation_priority"])
    assert pd.isna(out.loc[1, "target_irrigation_needed_binary"])


def test_missing_optional_sentinel_columns():
    out = build_dataset_frame(
        _features(DATES, with_sentinel=False), _fao(DATES, ["Low"] * 3), None, None
    )
    assert len(out) == 3
    assert "ndvi_mean" not in out.columns


def test_forecast_columns_prefixed_when_available():
    fc = pd.DataFrame({"date": [DATES[1]], "irrigation_risk_score": [0.9],
                       "irrigation_risk_level": ["High"]})
    out = build_dataset_frame(_features(DATES), _fao(DATES, ["Low"] * 3), None, fc)
    assert out.loc[1, "forecast_irrigation_risk_score"] == 0.9
    assert out["forecast_irrigation_risk_score"].isna().sum() == 2


def test_sorted_by_date():
    rev = DATES[::-1]
    out = build_dataset_frame(_features(rev), _fao(rev, ["High", "Medium", "Low"]))
    assert out["date"].tolist() == sorted(DATES)


def test_duplicate_dates_handled():
    feats = pd.concat([_features(DATES), _features(DATES[:1])], ignore_index=True)  # exact dup
    fao = pd.concat([_fao(DATES, ["Low"] * 3), _fao(DATES[:1], ["High"])], ignore_index=True)
    out = build_dataset_frame(feats, fao)
    assert len(out) == 3
    assert out["date"].is_unique
    assert out.loc[0, "water_stress_level"] == "High"  # last wins for conflicting date
