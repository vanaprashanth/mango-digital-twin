"""
tests/test_ml_dataset_freshness.py

Freshness / rebuild behaviour of the ML training dataset builder, plus
guards on the daily GitHub Actions workflow and artifact policy.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ml.build_ml_training_dataset import (
    build_dataset_frame,
    build_ml_training_dataset,
    compute_freshness,
    dataset_is_current,
    eligible_latest_date,
    input_fingerprints,
)


def _features(n, start="2026-01-01"):
    return pd.DataFrame({
        "date": pd.date_range(start, periods=n).strftime("%Y-%m-%d"),
        "temperature_avg_c": 25.0,
        "rainfall_mm": 0.0,
        "irrigation_risk_level": "Medium",
    })


def _fao(n, start="2026-01-01"):
    return pd.DataFrame({
        "date": pd.date_range(start, periods=n).strftime("%Y-%m-%d"),
        "mango_stage": "Fruit set", "stage_kc": 0.8, "interpolated_kc": 0.8,
        "et0_mm_day": 5.0, "etc_mm_day": 4.0, "rainfall_mm": 0.0,
        "irrigation_mm": 0.0, "water_input_mm": 0.0,
        "root_zone_depletion_mm": 10.0, "ks": 0.95, "water_stress_level": "Low",
    })


def _setup(tmp_path, n_features=10, n_fao=10, write_forecast=False):
    paths = {
        "combined_feature_table_csv": tmp_path / "features.csv",
        "fao56_interpolated_kc_water_balance_csv": tmp_path / "fao.csv",
        "ml_training_dataset_csv": tmp_path / "out" / "ml.csv",
        "ml_training_dataset_metadata_json": tmp_path / "out" / "ml_meta.json",
        "forecast_risk_csv": tmp_path / "forecast.csv",
        "irrigation_events_csv": tmp_path / "events.csv",
    }
    if n_features is not None:
        _features(n_features).to_csv(paths["combined_feature_table_csv"], index=False)
    if n_fao is not None:
        _fao(n_fao).to_csv(paths["fao56_interpolated_kc_water_balance_csv"], index=False)
    return SimpleNamespace(path=lambda k: paths[k]), paths


TODAY = date(2026, 6, 1)


# 1. Newer upstream data triggers a rebuild -----------------------------------

def test_newer_upstream_triggers_rebuild(tmp_path):
    cfg, p = _setup(tmp_path, 10, 10)
    assert build_ml_training_dataset(cfg, today=TODAY) is True
    assert len(pd.read_csv(p["ml_training_dataset_csv"])) == 10

    _features(12).to_csv(p["combined_feature_table_csv"], index=False)   # two newer days
    _fao(12).to_csv(p["fao56_interpolated_kc_water_balance_csv"], index=False)
    assert not dataset_is_current(
        p["ml_training_dataset_csv"], p["ml_training_dataset_metadata_json"],
        input_fingerprints({
            "combined_feature_table": p["combined_feature_table_csv"],
            "fao56_interpolated_kc": p["fao56_interpolated_kc_water_balance_csv"],
            "forecast_risk": p["forecast_risk_csv"],
            "irrigation_events": p["irrigation_events_csv"],
        }))
    assert build_ml_training_dataset(cfg, today=TODAY) is True
    out = pd.read_csv(p["ml_training_dataset_csv"])
    assert len(out) == 12 and out["date"].max() == "2026-01-12"


# 2. Unchanged inputs skip cleanly --------------------------------------------

def test_unchanged_inputs_skip_without_rewriting(tmp_path, capsys):
    cfg, p = _setup(tmp_path)
    assert build_ml_training_dataset(cfg, today=TODAY) is True
    mtime = p["ml_training_dataset_csv"].stat().st_mtime_ns
    built_at = json.loads(p["ml_training_dataset_metadata_json"].read_text())["built_at"]
    capsys.readouterr()

    assert build_ml_training_dataset(cfg, today=TODAY) is True
    assert "rebuild skipped" in capsys.readouterr().out
    assert p["ml_training_dataset_csv"].stat().st_mtime_ns == mtime
    assert json.loads(p["ml_training_dataset_metadata_json"].read_text())["built_at"] == built_at


def test_force_rebuilds_even_when_unchanged(tmp_path):
    cfg, p = _setup(tmp_path)
    build_ml_training_dataset(cfg, today=TODAY)
    p["ml_training_dataset_csv"].unlink()
    assert build_ml_training_dataset(cfg, force=True, today=TODAY) is True
    assert p["ml_training_dataset_csv"].exists()


def test_changed_irrigation_events_trigger_rebuild(tmp_path):
    cfg, p = _setup(tmp_path)
    build_ml_training_dataset(cfg, today=TODAY)
    p["irrigation_events_csv"].write_text(
        "date,irrigation_mm,method,source,notes\n2026-01-03,20,drip,user,\n")
    build_ml_training_dataset(cfg, today=TODAY)
    out = pd.read_csv(p["ml_training_dataset_csv"]).set_index("date")
    assert out.loc["2026-01-03", "days_since_last_irrigation"] == 0


# 3. Missing required inputs ---------------------------------------------------

def test_missing_required_inputs_handled_safely(tmp_path):
    cfg, p = _setup(tmp_path, n_features=None, n_fao=10)
    assert build_ml_training_dataset(cfg, today=TODAY) is False
    assert not p["ml_training_dataset_csv"].exists()


def test_missing_input_keeps_existing_dataset(tmp_path):
    cfg, p = _setup(tmp_path)
    build_ml_training_dataset(cfg, today=TODAY)
    before = p["ml_training_dataset_csv"].read_text()
    p["fao56_interpolated_kc_water_balance_csv"].unlink()
    assert build_ml_training_dataset(cfg, today=TODAY) is False
    assert p["ml_training_dataset_csv"].read_text() == before


def test_no_overlapping_dates_writes_nothing(tmp_path):
    cfg, p = _setup(tmp_path, 5, 5)
    _fao(5, start="2030-01-01").to_csv(p["fao56_interpolated_kc_water_balance_csv"], index=False)
    assert build_ml_training_dataset(cfg, today=TODAY) is False
    assert not p["ml_training_dataset_csv"].exists()


# 4. Date coverage matches eligible input data ---------------------------------

def test_date_coverage_matches_eligible_dates_and_never_extends_to_today():
    feats = _features(10)
    feats.loc[9, ["temperature_avg_c", "rainfall_mm"]] = np.nan     # unavailable NASA POWER day
    fao = _fao(8)                                                   # FAO ends earlier
    out = build_dataset_frame(feats, fao)
    assert out["date"].tolist() == _features(8)["date"].tolist()
    assert out["date"].max() == "2026-01-08"
    assert out["date"].max() < TODAY.isoformat()                    # not padded toward today
    assert out["date"].is_unique and out["date"].is_monotonic_increasing


def test_nan_weather_dates_are_dropped_not_filled():
    feats = _features(6)
    feats.loc[3, "temperature_avg_c"] = np.nan
    out = build_dataset_frame(feats, _fao(6))
    assert "2026-01-04" not in out["date"].tolist()
    assert len(out) == 5
    assert out["temperature_avg_c"].notna().all()


def test_eligible_latest_date():
    feats = _features(10)
    feats.loc[9, "rainfall_mm"] = np.nan
    assert eligible_latest_date(feats, _fao(10)) == date(2026, 1, 9)
    assert eligible_latest_date(feats, _fao(5)) == date(2026, 1, 5)
    assert eligible_latest_date(None, _fao(5)) is None
    assert eligible_latest_date(_features(3, "2030-01-01"), _fao(3)) is None


# 5. Freshness metadata ---------------------------------------------------------

def test_compute_freshness_cases():
    cur = compute_freshness(date(2026, 5, 20), date(2026, 5, 20), 100, today=date(2026, 5, 25))
    assert cur["status"] == "current" and cur["lag_days_vs_upstream"] == 0
    assert cur["age_days_vs_today"] == 5
    behind = compute_freshness(date(2026, 5, 20), date(2026, 5, 15), 100, today=date(2026, 5, 25))
    assert behind["status"] == "behind" and behind["lag_days_vs_upstream"] == 5
    assert compute_freshness(date(2026, 5, 20), None)["status"] == "no_dataset"
    assert compute_freshness(None, date(2026, 5, 20))["status"] == "no_upstream"


def test_metadata_written_with_correct_values(tmp_path):
    cfg, p = _setup(tmp_path, 10, 10)
    assert build_ml_training_dataset(cfg, today=date(2026, 1, 20)) is True
    meta = json.loads(p["ml_training_dataset_metadata_json"].read_text())
    assert meta["row_count"] == 10
    assert meta["dataset_cutoff_date"] == "2026-01-10"
    assert meta["date_range"] == ["2026-01-01", "2026-01-10"]
    assert meta["upstream"]["eligible_latest_date"] == "2026-01-10"
    assert meta["freshness"]["status"] == "current"
    assert meta["freshness"]["lag_days_vs_upstream"] == 0
    assert meta["freshness"]["age_days_vs_today"] == 10
    assert meta["label_type"] == "surrogate_rule_based" and "surrogate" in meta["warning"].lower()
    assert meta["per_class_support"] == {"Low": 10}
    assert meta["inputs"]["combined_feature_table"]["sha256"]
    assert meta["inputs"]["forecast_risk"] is None                  # optional input absent


def test_stale_existing_dataset_is_warned_before_rebuild(tmp_path, capsys):
    cfg, p = _setup(tmp_path, 10, 10)
    build_ml_training_dataset(cfg, today=TODAY)
    _features(15).to_csv(p["combined_feature_table_csv"], index=False)
    _fao(15).to_csv(p["fao56_interpolated_kc_water_balance_csv"], index=False)
    capsys.readouterr()
    build_ml_training_dataset(cfg, today=TODAY)
    out = capsys.readouterr().out
    assert "WARNING" in out and "before rebuild" in out and "status=behind" in out
    assert "after rebuild" in out and "status=current" in out


# 6. Workflow and artifact policy -----------------------------------------------

def _workflow():
    return yaml.safe_load((PROJECT_ROOT / ".github" / "workflows" / "daily-data-refresh.yml").read_text(encoding="utf-8"))


def test_daily_workflow_retains_existing_functionality():
    wf = _workflow()
    on = wf.get("on", wf.get(True))
    assert "workflow_dispatch" in on
    assert on["schedule"][0]["cron"] == "30 2 * * *"
    assert wf["concurrency"] == {"group": "daily-data-refresh", "cancel-in-progress": False}
    assert wf["permissions"]["contents"] == "write"
    steps = wf["jobs"]["refresh-data"]["steps"]
    runs = "\n".join(s.get("run", "") for s in steps)
    assert "pip install -r requirements.txt" in runs
    assert "python main.py --skip-soil-fetch --refresh-sentinel2" in runs
    assert "git add data/raw data/processed" in runs
    assert "git pull --rebase origin master" in runs and "git push origin HEAD:master" in runs
    assert "Data: automated daily refresh" in runs
    pipeline_step = next(s for s in steps if "main.py" in s.get("run", ""))
    assert "GEE_SERVICE_ACCOUNT_KEY" in pipeline_step["env"]
    assert not any("train_irrigation_priority_model" in s.get("run", "") for s in steps)


def test_daily_pipeline_builds_dataset_but_does_not_retrain():
    from src.pipeline.run_pipeline import FRESHNESS_AWARE_STEPS
    names = [s.name for s in FRESHNESS_AWARE_STEPS]
    assert any(n.startswith("ML training dataset") for n in names)
    assert not any("model" in n.lower() and n.startswith("ML") for n in names)
    ml = next(s for s in FRESHNESS_AWARE_STEPS if s.name.startswith("ML training dataset"))
    assert ml.output_keys == ["ml_training_dataset_csv"]
    # builds after its upstream steps
    assert names.index(ml.name) > names.index("Forecast-aware irrigation advisory")
    assert names.index(ml.name) > names.index("Interpolated-Kc FAO-56 water balance")


def _ignored(path: str) -> bool:
    r = subprocess.run(["git", "check-ignore", "-q", path], cwd=PROJECT_ROOT)
    return r.returncode == 0


def test_artifact_policy_in_gitignore():
    assert _ignored("models/irrigation_priority_model.joblib")
    assert _ignored("anything.pkl")
    assert _ignored("data/processed/muthukur_ml_training_dataset.csv")
    assert _ignored("data/processed/muthukur_ml_training_dataset_metadata.json")
    assert not _ignored("data/processed/muthukur_ml_model_metrics.json")
    assert not _ignored("data/processed/muthukur_ml_feature_importance.csv")


def test_config_has_metadata_path():
    cfg = yaml.safe_load((PROJECT_ROOT / "configs" / "config.yaml").read_text(encoding="utf-8"))
    assert cfg["paths"]["ml_training_dataset_metadata_json"].endswith("ml_training_dataset_metadata.json")
