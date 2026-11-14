"""
app/sections/data_sources_health.py

"Data Sources & Health" page (Stage C): a read-only data-observability view.

Everything shown is computed at runtime from the real files and the existing
pipeline metadata JSON; nothing is hardcoded or fetched, and no credentials
(API tokens, GEE service-account JSON) are read or displayed.

Freshness is source-specific. A file that merely exists is NOT "Fresh":
  observation  latest valid observation date vs today (per-source thresholds)
  forecast     forecast horizon must still reach today or later
  static       SoilGrids-like data that does not change (state "Static")
  manual       user-maintained log (state "Manual"; latest entry shown)
  artifact     manually produced ML artifacts (age of training timestamp)

States: Fresh, Aging, Stale, Static, Manual, Unknown (no usable timestamp),
Missing (file absent).

File modification time is shown for reference only. On hosted deployments it
reflects checkout/deploy time, so observation dates drive the freshness state.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

from app.theme import esc, kpi_card, page_header, section_header, status_pill
from src.utils.pipeline_metadata import load_metadata_json

NOTE_MTIME = ("File refresh time is the file's modification time. On Streamlit Cloud this "
              "reflects deployment, so freshness is judged from the latest observation date.")


@dataclass(frozen=True)
class SourceSpec:
    key: str
    name: str
    category: str
    path_key: str
    purpose: str
    mode: str                      # observation | forecast | static | manual | artifact
    date_col: str | None = "date"
    valid_col: str | None = None   # rows where this column == -999 are ignored (NASA POWER)
    cap_today: bool = False        # ignore dates after today (raw files containing forecasts)
    json_date_key: str | None = None
    fresh_days: int | None = None
    aging_days: int | None = None
    expectation: str = ""
    optional: bool = False


SOURCES: list[SourceSpec] = [
    SourceSpec("nasa_power", "NASA POWER", "Weather (raw)", "nasa_power_csv",
               "Historical daily weather that drives the risk and FAO-56 engines.",
               "observation", valid_col="temperature_avg_c", fresh_days=7, aging_days=14,
               expectation="Publishes with a 2-7 day lag; -999 placeholder rows are ignored."),
    SourceSpec("open_meteo", "Open-Meteo", "Weather (raw)", "open_meteo_csv",
               "Recent observed weather plus short-range forecast inputs.",
               "observation", cap_today=True, fresh_days=2, aging_days=5,
               expectation="Updated daily; observed days up to today are expected."),
    SourceSpec("soilgrids", "SoilGrids", "Soil (raw)", "soilgrids_csv",
               "Static point soil properties used for soil-adjusted irrigation factors.",
               "static", date_col=None, expectation="Effectively static; never judged stale."),
    SourceSpec("sentinel2", "Sentinel-2 optical imagery", "Remote sensing", "sentinel2_daily_csv",
               "NDVI/NDWI/NDMI/NDRE vegetation and canopy indicators.",
               "observation", fresh_days=10, aging_days=45,
               expectation="~5-day revisit, but cloud cover leaves long gaps in the monsoon; "
                           "up to 45 days is tolerated before Stale."),
    SourceSpec("sentinel1", "Sentinel-1 SAR", "Remote sensing", "sentinel1_daily_csv",
               "Radar backscatter proxy that continues through cloud cover.",
               "observation", fresh_days=14, aging_days=30, optional=True,
               expectation="6-12 day revisit and cloud-independent, so a gap beyond 30 days "
                           "indicates a pipeline problem."),
    SourceSpec("historical_risk", "Historical Risk", "Derived weather", "historical_risk_csv",
               "Daily irrigation, heat and disease risk scores from weather.",
               "observation", fresh_days=7, aging_days=14,
               expectation="Follows NASA POWER availability."),
    SourceSpec("forecast_risk", "Forecast Risk", "Derived weather", "forecast_risk_csv",
               "Forward-looking risk scores from the Open-Meteo forecast.",
               "forecast", fresh_days=0, aging_days=3,
               expectation="Forecast horizon must still reach today or later."),
    SourceSpec("combined", "Combined Feature Table", "Derived features", "combined_feature_table_csv",
               "Weather + soil + satellite features for combined intelligence and ML.",
               "observation", fresh_days=7, aging_days=14, expectation="Follows NASA POWER availability."),
    SourceSpec("phenology", "Mango Phenology", "Derived features", "mango_phenology_calendar_csv",
               "Growth-stage calendar and Kc references.", "observation", fresh_days=7, aging_days=14,
               expectation="Calendar follows the weather date range."),
    SourceSpec("fao56", "FAO-56 water balances", "Water balance", "fao56_interpolated_kc_water_balance_csv",
               "Soil-water depletion, Ks and water-stress level (interpolated-Kc balance).",
               "observation", fresh_days=7, aging_days=14, expectation="Follows NASA POWER availability."),
    SourceSpec("irrigation_events", "Irrigation Events", "Manual log", "irrigation_events_csv",
               "User-recorded irrigation applied in the FAO-56 water balance.",
               "manual", expectation="Recorded manually; unrecorded irrigation is not tracked."),
    SourceSpec("ml_artifacts", "ML evaluation artifacts", "AI / ML (experimental)", "ml_model_metrics_json",
               "Surrogate-label model metrics; not field validated.",
               "artifact", date_col=None, json_date_key="trained_at", fresh_days=45, aging_days=120,
               expectation="Produced by manual evaluation runs, not by the daily refresh."),
]


# ---------------------------------------------------------------------------
# Pure helpers (no Streamlit)
# ---------------------------------------------------------------------------

def _to_date(value) -> dt.date | None:
    try:
        ts = pd.to_datetime(value, errors="coerce")
    except Exception:
        return None
    return None if pd.isna(ts) else ts.date()


def latest_csv_date(path: Path, date_col: str = "date", valid_col: str | None = None,
                    cap: dt.date | None = None) -> dt.date | None:
    """Latest valid date in a CSV, or None if missing/unreadable/no dates."""
    try:
        cols = [date_col] + ([valid_col] if valid_col else [])
        df = pd.read_csv(path, usecols=lambda c: c in cols)
    except Exception:
        return None
    if date_col not in df.columns:
        return None
    if valid_col and valid_col in df.columns:
        df = df[pd.to_numeric(df[valid_col], errors="coerce").fillna(-999) != -999]
    dates = pd.to_datetime(df[date_col], errors="coerce").dropna()
    if cap is not None:
        dates = dates[dates.dt.date <= cap]
    return None if dates.empty else dates.max().date()


def latest_json_date(path: Path, key: str) -> dt.date | None:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return _to_date(data.get(key)) if isinstance(data, dict) else None


def classify_age(age_days: int | None, fresh_days: int | None, aging_days: int | None) -> str:
    """Fresh / Aging / Stale from an age in days; Unknown when age or thresholds are missing."""
    if age_days is None or fresh_days is None or aging_days is None:
        return "Unknown"
    if age_days <= fresh_days:
        return "Fresh"
    if age_days <= aging_days:
        return "Aging"
    return "Stale"


def evaluate_source(spec: SourceSpec, path: Path, now: dt.datetime | None = None) -> dict:
    """Compute the status record for one source. Never raises."""
    now = now or dt.datetime.now()
    today = now.date()
    path = Path(path)
    rec = {
        "key": spec.key, "name": spec.name, "category": spec.category, "purpose": spec.purpose,
        "expectation": spec.expectation, "optional": spec.optional, "path": str(path),
        "available": False, "latest_observation": None, "file_modified": None,
        "age_days": None, "state": "Missing", "detail": "",
    }
    try:
        exists = path.exists()
    except OSError:
        exists = False
    if not exists:
        rec["detail"] = "Optional source not produced yet." if spec.optional else "File not found."
        return rec

    rec["available"] = True
    try:
        rec["file_modified"] = dt.datetime.fromtimestamp(path.stat().st_mtime)
    except (OSError, ValueError, OverflowError):
        rec["file_modified"] = None

    if spec.json_date_key:
        latest = latest_json_date(path, spec.json_date_key)
    elif spec.date_col:
        latest = latest_csv_date(path, spec.date_col, spec.valid_col, today if spec.cap_today else None)
    else:
        latest = None
    rec["latest_observation"] = latest

    if spec.mode == "static":
        rec["state"] = "Static"
        rec["detail"] = "Static data; freshness not applicable."
    elif spec.mode == "manual":
        rec["state"] = "Manual"
        if latest is not None:
            rec["age_days"] = (today - latest).days
            rec["detail"] = f"Last recorded event {rec['age_days']} day(s) ago."
        else:
            rec["detail"] = "No events recorded yet."
    elif latest is None:
        rec["state"] = "Unknown"
        rec["detail"] = "No usable observation date found in the file."
    elif spec.mode == "forecast":
        rec["age_days"] = (today - latest).days            # <= 0 means horizon still ahead
        rec["state"] = classify_age(max(rec["age_days"], 0), spec.fresh_days, spec.aging_days)
        rec["detail"] = (f"Forecast reaches {latest.isoformat()}." if rec["age_days"] <= 0
                         else f"Forecast ended {rec['age_days']} day(s) ago.")
    else:
        rec["age_days"] = (today - latest).days
        rec["state"] = classify_age(rec["age_days"], spec.fresh_days, spec.aging_days)
        rec["detail"] = f"Latest observation is {rec['age_days']} day(s) old."
    return rec


def evaluate_all(config, now: dt.datetime | None = None, specs: list[SourceSpec] | None = None) -> list[dict]:
    out = []
    for spec in (specs or SOURCES):
        try:
            path = Path(config.path(spec.path_key))
        except Exception:
            path = Path(f"<unconfigured:{spec.path_key}>")
        out.append(evaluate_source(spec, path, now))
    return out


def summarize(records: list[dict]) -> dict:
    return {
        "total": len(records),
        "available": sum(r["available"] for r in records),
        "missing": sum(r["state"] == "Missing" for r in records),
        "stale": sum(r["state"] == "Stale" for r in records),
        "aging": sum(r["state"] == "Aging" for r in records),
        "unknown": sum(r["state"] == "Unknown" for r in records),
    }


def pipeline_summary(metadata: dict | None) -> dict:
    """Pipeline status from the existing run metadata (None-safe)."""
    if not metadata:
        return {"available": False, "status": "Unknown", "last_run": None,
                "last_successful_run": None, "mode": None}
    completed = metadata.get("run_completed_at")
    parsed = None
    if completed:
        try:
            parsed = dt.datetime.strptime(completed, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            parsed = None
    status = metadata.get("status", "unknown")
    return {
        "available": True, "status": status, "mode": metadata.get("pipeline_mode"),
        "last_run": parsed,
        "last_successful_run": parsed if status == "success" else None,
        "missing_warnings": len(metadata.get("missing_file_warnings") or []),
    }


def _fmt_dt(value: dt.datetime | None) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value else "n/a"


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

def _source_card(r: dict) -> str:
    latest = r["latest_observation"].isoformat() if r["latest_observation"] else "n/a"
    avail = "Available" if r["available"] else "Missing"
    return (
        '<div class="mt-card">'
        f'<div style="display:flex;justify-content:space-between;gap:.5rem;align-items:center">'
        f'<h4>{esc(r["name"])}</h4>{status_pill(r["state"])}</div>'
        f'<div class="mt-meta">{esc(r["category"])}<br>{esc(r["purpose"])}</div>'
        f'<div class="mt-meta" style="margin-top:.5rem">'
        f'<b>File:</b> {status_pill(avail)} &nbsp; <b>Latest observation:</b> {esc(latest)}<br>'
        f'<b>File refreshed:</b> {esc(_fmt_dt(r["file_modified"]))}<br>'
        f'<b>Status:</b> {esc(r["detail"])}<br>'
        f'<b>Expectation:</b> {esc(r["expectation"])}</div></div>'
    )


def render_data_sources_health_page(config, metadata_path: Path | None = None,
                                    now: dt.datetime | None = None) -> None:
    page_header("Data & System", "Data Sources & Health",
                "Runtime observability for every dataset feeding the digital twin.")

    records = evaluate_all(config, now)
    s = summarize(records)
    metadata = load_metadata_json(metadata_path or config.path("pipeline_run_metadata_json"))
    pipe = pipeline_summary(metadata)

    cols = st.columns(5)
    cards = [
        ("Configured sources", str(s["total"]), "", None),
        ("Available", f'{s["available"]} / {s["total"]}', "", "Available" if s["available"] == s["total"] else "Caution"),
        ("Missing", str(s["missing"]), "", "Missing" if s["missing"] else "Healthy"),
        ("Stale", str(s["stale"]), f'{s["aging"]} aging', "Stale" if s["stale"] else "Healthy"),
        ("Last successful pipeline run",
         _fmt_dt(pipe["last_successful_run"]) + (" UTC" if pipe["last_successful_run"] else ""),
         "" if pipe["available"] else "No pipeline metadata", None),
    ]
    for col, (label, value, note, state) in zip(cols, cards):
        col.markdown(kpi_card(label, value, note, state), unsafe_allow_html=True)

    st.write("")
    section_header("Pipeline status")
    if not pipe["available"]:
        st.info("Pipeline metadata not found. It is written by `python main.py` "
                "(`pipeline_run_metadata_json`).")
    else:
        ok = pipe["status"] == "success"
        st.markdown(
            f'{status_pill("Healthy" if ok else "Stale", "Last run: " + str(pipe["status"]))} '
            f'&nbsp; Completed {esc(_fmt_dt(pipe["last_run"]))} UTC &nbsp;·&nbsp; '
            f'mode: {esc(pipe["mode"] or "unknown")}', unsafe_allow_html=True)
        if pipe.get("missing_warnings"):
            st.warning(f'{pipe["missing_warnings"]} expected file(s) were reported missing by the last run.')
        if pipe["last_run"] and (( now or dt.datetime.now()) - pipe["last_run"]).days > 3:
            st.caption("Pipeline metadata is more than 3 days old; it may not reflect the latest "
                       "automated refresh.")
    st.caption(NOTE_MTIME)

    categories: dict[str, list[dict]] = {}
    for r in records:
        categories.setdefault(r["category"], []).append(r)
    for category, recs in categories.items():
        section_header(category)
        for i in range(0, len(recs), 2):
            row = st.columns(2)
            for col, r in zip(row, recs[i:i + 2]):
                col.markdown(_source_card(r), unsafe_allow_html=True)
