"""
tests/test_data_sources_health.py

Source status calculations for the Data Sources & Health page.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.sections import data_sources_health as dsh  # noqa: E402
from app.sections.data_sources_health import SOURCES, SourceSpec  # noqa: E402

NOW = dt.datetime(2026, 11, 14, 12, 0)


def _spec(key):
    return next(s for s in SOURCES if s.key == key)


def _csv(path, dates, **extra):
    df = pd.DataFrame({"date": dates, **extra})
    df.to_csv(path, index=False)
    return path


def test_all_required_sources_configured_and_importable():
    names = {s.name for s in SOURCES}
    for expected in ("NASA POWER", "Open-Meteo", "SoilGrids", "Sentinel-2 optical imagery",
                     "Sentinel-1 SAR", "Historical Risk", "Forecast Risk", "Combined Feature Table",
                     "Mango Phenology", "FAO-56 water balances", "Irrigation Events",
                     "ML evaluation artifacts"):
        assert expected in names
    assert callable(dsh.render_data_sources_health_page)


def test_existing_file_is_not_automatically_healthy(tmp_path):
    p = _csv(tmp_path / "s2.csv", ["2026-01-01"])
    rec = dsh.evaluate_source(_spec("sentinel2"), p, NOW)
    assert rec["available"] and rec["state"] == "Stale"


@pytest.mark.parametrize("age,expected", [(0, "Fresh"), (10, "Fresh"), (11, "Aging"), (45, "Aging"), (46, "Stale")])
def test_sentinel2_thresholds(tmp_path, age, expected):
    d = (NOW.date() - dt.timedelta(days=age)).isoformat()
    rec = dsh.evaluate_source(_spec("sentinel2"), _csv(tmp_path / "a.csv", [d]), NOW)
    assert rec["state"] == expected and rec["age_days"] == age


@pytest.mark.parametrize("age,expected", [(14, "Fresh"), (15, "Aging"), (30, "Aging"), (31, "Stale")])
def test_sentinel1_has_separate_thresholds(tmp_path, age, expected):
    d = (NOW.date() - dt.timedelta(days=age)).isoformat()
    rec = dsh.evaluate_source(_spec("sentinel1"), _csv(tmp_path / "b.csv", [d]), NOW)
    assert rec["state"] == expected


def test_s1_and_s2_logic_differ_for_same_age(tmp_path):
    d = (NOW.date() - dt.timedelta(days=40)).isoformat()
    s2 = dsh.evaluate_source(_spec("sentinel2"), _csv(tmp_path / "a.csv", [d]), NOW)
    s1 = dsh.evaluate_source(_spec("sentinel1"), _csv(tmp_path / "b.csv", [d]), NOW)
    assert (s2["state"], s1["state"]) == ("Aging", "Stale")


def test_missing_file(tmp_path):
    rec = dsh.evaluate_source(_spec("nasa_power"), tmp_path / "nope.csv", NOW)
    assert rec["state"] == "Missing" and not rec["available"] and rec["latest_observation"] is None
    opt = dsh.evaluate_source(_spec("sentinel1"), tmp_path / "nope.csv", NOW)
    assert opt["state"] == "Missing" and "Optional" in opt["detail"]


def test_missing_timestamps_give_unknown_not_healthy(tmp_path):
    p = tmp_path / "x.csv"
    pd.DataFrame({"date": [None, "garbage"], "v": [1, 2]}).to_csv(p, index=False)
    assert dsh.evaluate_source(_spec("historical_risk"), p, NOW)["state"] == "Unknown"
    nodate = tmp_path / "y.csv"
    pd.DataFrame({"v": [1]}).to_csv(nodate, index=False)
    assert dsh.evaluate_source(_spec("historical_risk"), nodate, NOW)["state"] == "Unknown"
    empty = tmp_path / "z.csv"
    empty.write_text("")
    assert dsh.evaluate_source(_spec("historical_risk"), empty, NOW)["state"] == "Unknown"


def test_nasa_power_ignores_minus_999_placeholder_rows(tmp_path):
    p = _csv(tmp_path / "n.csv", ["2026-11-09", "2026-11-13", "2026-11-14"],
             temperature_avg_c=[24.0, -999.0, -999.0])
    rec = dsh.evaluate_source(_spec("nasa_power"), p, NOW)
    assert rec["latest_observation"] == dt.date(2026, 11, 9) and rec["state"] == "Fresh"


def test_open_meteo_ignores_future_forecast_dates(tmp_path):
    p = _csv(tmp_path / "om.csv", ["2026-11-12", "2026-11-20"])
    rec = dsh.evaluate_source(_spec("open_meteo"), p, NOW)
    assert rec["latest_observation"] == dt.date(2026, 11, 12) and rec["state"] == "Fresh"


def test_forecast_horizon_logic(tmp_path):
    assert dsh.evaluate_source(_spec("forecast_risk"), _csv(tmp_path / "f1.csv", ["2026-11-20"]), NOW)["state"] == "Fresh"
    assert dsh.evaluate_source(_spec("forecast_risk"), _csv(tmp_path / "f2.csv", ["2026-11-12"]), NOW)["state"] == "Aging"
    assert dsh.evaluate_source(_spec("forecast_risk"), _csv(tmp_path / "f3.csv", ["2026-10-01"]), NOW)["state"] == "Stale"


def test_static_and_manual_sources(tmp_path):
    soil = tmp_path / "soil.csv"
    soil.write_text("property,depth\nbdod,0-5cm\n")
    assert dsh.evaluate_source(_spec("soilgrids"), soil, NOW)["state"] == "Static"
    ev = _csv(tmp_path / "ev.csv", ["2026-08-21"])
    rec = dsh.evaluate_source(_spec("irrigation_events"), ev, NOW)
    assert rec["state"] == "Manual" and rec["age_days"] == 85
    none = tmp_path / "ev2.csv"
    none.write_text("date\n")
    assert dsh.evaluate_source(_spec("irrigation_events"), none, NOW)["state"] == "Manual"


def test_ml_artifacts_use_trained_at(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps({"trained_at": "2026-11-01T10:00:00"}))
    assert dsh.evaluate_source(_spec("ml_artifacts"), p, NOW)["state"] == "Fresh"
    p.write_text(json.dumps({"trained_at": "2026-01-01T10:00:00"}))
    assert dsh.evaluate_source(_spec("ml_artifacts"), p, NOW)["state"] == "Stale"
    p.write_text("{not json")
    assert dsh.evaluate_source(_spec("ml_artifacts"), p, NOW)["state"] == "Unknown"


def test_file_modified_time_reported(tmp_path):
    p = _csv(tmp_path / "a.csv", ["2026-11-10"])
    assert isinstance(dsh.evaluate_source(_spec("historical_risk"), p, NOW)["file_modified"], dt.datetime)


def test_evaluate_all_and_summary_with_missing_files(tmp_path):
    cfg = SimpleNamespace(path=lambda k: tmp_path / f"{k}.csv")
    recs = dsh.evaluate_all(cfg, NOW)
    s = dsh.summarize(recs)
    assert s["total"] == len(SOURCES) and s["available"] == 0 and s["missing"] == len(SOURCES)
    _csv(tmp_path / "sentinel2_daily_csv.csv", ["2026-01-01"])
    _csv(tmp_path / "historical_risk_csv.csv", ["2026-11-12"])
    s = dsh.summarize(dsh.evaluate_all(cfg, NOW))
    assert s["available"] == 2 and s["stale"] == 1 and s["missing"] == len(SOURCES) - 2


def test_evaluate_all_survives_unconfigured_path_key():
    def bad(_k):
        raise KeyError(_k)
    recs = dsh.evaluate_all(SimpleNamespace(path=bad), NOW)
    assert all(r["state"] == "Missing" for r in recs)


def test_pipeline_summary():
    assert dsh.pipeline_summary(None)["available"] is False
    ok = dsh.pipeline_summary({"status": "success", "run_completed_at": "2026-11-13T01:02:03Z",
                               "pipeline_mode": "full"})
    assert ok["last_successful_run"] == dt.datetime(2026, 11, 13, 1, 2, 3)
    failed = dsh.pipeline_summary({"status": "failed", "run_completed_at": "2026-11-13T01:02:03Z"})
    assert failed["last_successful_run"] is None and failed["last_run"] is not None
    bad_ts = dsh.pipeline_summary({"status": "success", "run_completed_at": "garbage"})
    assert bad_ts["last_successful_run"] is None


def test_no_secrets_referenced_by_page_module():
    src = (PROJECT_ROOT / "app" / "sections" / "data_sources_health.py").read_text(encoding="utf-8")
    for needle in ("os.environ", "getenv", "st.secrets", "service_account"):
        assert needle not in src
