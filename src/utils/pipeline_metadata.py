"""
Pipeline run metadata / data freshness utility.

WHAT THIS MODULE DOES
  Collects a single, lightweight JSON snapshot describing the most recent
  pipeline run: when it started/finished, which mode it ran in, whether it
  succeeded, which files it read/wrote, how many rows each output file has,
  the latest available date in each key time-series CSV, when each file was
  last modified on disk, and which expected files are missing.

  This makes the project behave like a NEAR-REAL-TIME digital twin: the
  dashboard (or any other consumer) can read this one JSON file to answer
  "how fresh is this data right now?" without re-reading every CSV itself.

  "Near-real-time" is deliberate wording, not "real-time" — the underlying
  sources update on very different cadences:
    - Open-Meteo forecast weather: updates frequently (hourly/daily).
    - Sentinel-2 vegetation indices: updates every few days, depending on
      satellite revisit time and cloud cover over the study area.
    - NASA POWER historical weather: can lag several days behind "today".
    - SoilGrids soil properties: effectively static (rarely changes).
  A single "last updated" timestamp can never make all of these current at
  once, so this module reports per-source freshness rather than implying
  one global "live" state.

WHAT THIS MODULE DOES NOT DO
  - No database, no scheduler, no cloud calls, no new external APIs.
  - No machine learning / deep learning.
  - It does not fetch or recompute anything itself — it only inspects files
    that the existing fetch scripts and risk/water-balance engines already
    produced, and records what it finds.

OUTPUT
  data/processed/pipeline_run_metadata.json (path comes from
  configs/config.yaml -> paths.pipeline_run_metadata_json, like every other
  file path in this project).

HOW TO USE
  from src.utils.pipeline_metadata import build_pipeline_metadata, write_metadata_json

  start = utc_now()
  ... run pipeline steps ...
  metadata = build_pipeline_metadata(
      run_started_at=start,
      run_completed_at=utc_now(),
      pipeline_mode="full pipeline",
      status="success",
  )
  write_metadata_json(metadata, get_config().path("pipeline_run_metadata_json"))

  To read it back later (e.g. from the dashboard):
      from src.utils.pipeline_metadata import load_metadata_json
      metadata = load_metadata_json(get_config().path("pipeline_run_metadata_json"))
"""

import csv
import datetime as dt
import json
from pathlib import Path

import pandas as pd

from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger(__name__)


# Raw/input files this project's fetch scripts produce. Logical name ->
# configs/config.yaml path key.
SOURCE_FILE_PATH_KEYS: dict[str, str] = {
    "nasa_power_raw_weather": "nasa_power_csv",
    "open_meteo_raw_weather": "open_meteo_csv",
    "soilgrids_raw_soil": "soilgrids_csv",
}

# Processed/output files this project's risk engines and standalone
# scripts produce. Logical name -> configs/config.yaml path key.
# All of these are produced by the unified freshness-aware pipeline
# (python main.py --skip-fetch) but may not yet exist on a first run
# or if a required upstream input is still missing -- that is handled
# gracefully (file missing → row_count = None, no error).
OUTPUT_FILE_PATH_KEYS: dict[str, str] = {
    "historical_risk": "historical_risk_csv",
    "forecast_risk": "forecast_risk_csv",
    "sentinel2_daily_vegetation": "sentinel2_daily_csv",
    "sentinel2_timeseries_vegetation": "sentinel2_timeseries_csv",
    "combined_feature_table": "combined_feature_table_csv",
    "fao56_water_balance": "fao56_water_balance_csv",
    "mango_phenology_calendar": "mango_phenology_calendar_csv",
    "fao56_phenology_water_balance": "fao56_phenology_water_balance_csv",
    "fao56_model_comparison": "fao56_model_comparison_csv",
    "forecast_aware_irrigation_advisory": "forecast_aware_irrigation_advisory_csv",
}

# Files to inspect for "latest available date" -- the freshness signal that
# matters most for a near-real-time digital twin. All of these CSVs have a
# `date` column. Logical name -> path key (re-using the keys above so there
# is only one place that lists each file's location).
LATEST_DATE_FILE_KEYS: dict[str, str] = {
    "weather_risk_latest_date": "historical_risk_csv",
    "open_meteo_forecast_latest_date": "forecast_risk_csv",
    "sentinel2_daily_latest_date": "sentinel2_daily_csv",
    "combined_feature_table_latest_date": "combined_feature_table_csv",
    "fao56_water_balance_latest_date": "fao56_water_balance_csv",
    "phenology_calendar_latest_date": "mango_phenology_calendar_csv",
    "fao56_phenology_water_balance_latest_date": "fao56_phenology_water_balance_csv",
    "fao56_model_comparison_latest_date": "fao56_model_comparison_csv",
}

NEAR_REAL_TIME_NOTE = (
    "This is a near-real-time digital twin, not a real-time one. Open-Meteo "
    "forecast weather refreshes frequently, Sentinel-2 vegetation indices "
    "update only every few days (satellite revisit time and cloud cover "
    "permitting), NASA POWER historical weather can lag behind today by "
    "several days, and SoilGrids soil properties are effectively static. "
    "Check the per-file latest dates below rather than assuming everything "
    "is equally current."
)


def utc_now() -> dt.datetime:
    """Current time as a timezone-aware UTC datetime."""
    return dt.datetime.now(dt.timezone.utc)


def _iso(timestamp: dt.datetime | None) -> str | None:
    """Format a datetime as an ISO-8601 UTC string, or None if not given."""
    if timestamp is None:
        return None
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=dt.timezone.utc)
    return timestamp.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_csv_row_count(path: Path) -> int | None:
    """
    Count data rows in a CSV (excluding the header) without loading the
    whole file into a DataFrame. Returns None if the file is missing or
    can't be read, rather than raising.
    """
    if not path.exists():
        return None
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                return 0
            return sum(1 for _ in reader)
    except Exception as exc:
        log.warning("Could not count rows in %s: %s", path, exc)
        return None


def safe_latest_date(path: Path, date_column: str = "date") -> str | None:
    """
    Return the latest date (YYYY-MM-DD) found in `date_column` of the given
    CSV, or None if the file is missing, the column is absent, or no row
    parses as a valid date. Never raises.
    """
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, usecols=[date_column])
    except (ValueError, pd.errors.EmptyDataError) as exc:
        log.warning("Could not read column '%s' from %s: %s", date_column, path, exc)
        return None
    except Exception as exc:
        log.warning("Could not read %s: %s", path, exc)
        return None

    if df.empty:
        return None

    parsed = pd.to_datetime(df[date_column], errors="coerce").dropna()
    if parsed.empty:
        return None

    return parsed.max().strftime("%Y-%m-%d")


def safe_file_mtime(path: Path) -> str | None:
    """Return a file's last-modified time as an ISO-8601 UTC string, or None."""
    if not path.exists():
        return None
    try:
        return _iso(dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc))
    except Exception as exc:
        log.warning("Could not read modified time for %s: %s", path, exc)
        return None


def write_metadata_json(metadata: dict, path: Path) -> None:
    """Write the metadata dict to disk as pretty-printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")


def load_metadata_json(path: Path) -> dict | None:
    """
    Load a previously written metadata JSON file, for dashboard or other
    read-only use. Returns None (never raises) if the file is missing or
    not valid JSON, so callers can show a friendly fallback message.
    """
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning("Could not parse metadata JSON at %s: %s", path, exc)
        return None


def build_pipeline_metadata(
    run_started_at: dt.datetime,
    run_completed_at: dt.datetime,
    pipeline_mode: str,
    status: str,
    extra_warnings: list[str] | None = None,
    step_results: list[dict] | None = None,
) -> dict:
    """
    Build the full pipeline-run metadata dict by inspecting the project's
    existing source and output CSVs. Does not read or write any file other
    than the small reads needed for row counts / latest dates -- it does
    not regenerate or modify any pipeline output.

    `step_results` is an optional list of dicts (each with "name", "status"
    -- RUN / SKIP_FRESH / SKIP_MISSING_INPUT / FAILED -- and "detail"),
    produced by src/pipeline/run_pipeline.py's freshness-aware step runner.
    This is purely additive: it does not change any existing field, so
    older consumers of this JSON (e.g. the dashboard's freshness panel)
    keep working unchanged even though this key wasn't present before.
    """
    config = get_config()

    all_file_keys: dict[str, str] = {**SOURCE_FILE_PATH_KEYS, **OUTPUT_FILE_PATH_KEYS}

    source_files: dict[str, str] = {}
    output_files: dict[str, str] = {}
    row_counts: dict[str, int | None] = {}
    file_modified_timestamps: dict[str, str | None] = {}
    missing_file_warnings: list[str] = []

    for name, path_key in all_file_keys.items():
        path = config.path(path_key)
        path_str = str(path)

        if name in SOURCE_FILE_PATH_KEYS:
            source_files[name] = path_str
        else:
            output_files[name] = path_str

        row_counts[name] = safe_csv_row_count(path)
        file_modified_timestamps[name] = safe_file_mtime(path)

        if not path.exists():
            missing_file_warnings.append(f"{name}: {path_str} not found")

    latest_dates: dict[str, str | None] = {}
    for latest_key, path_key in LATEST_DATE_FILE_KEYS.items():
        path = config.path(path_key)
        latest_dates[latest_key] = safe_latest_date(path)

    if extra_warnings:
        missing_file_warnings.extend(extra_warnings)

    metadata = {
        "run_started_at": _iso(run_started_at),
        "run_completed_at": _iso(run_completed_at),
        "timezone": "UTC",
        "pipeline_mode": pipeline_mode,
        "status": status,
        "source_files": source_files,
        "output_files": output_files,
        "row_counts": row_counts,
        "latest_dates": latest_dates,
        "file_modified_timestamps": file_modified_timestamps,
        "missing_file_warnings": missing_file_warnings,
        "near_real_time_note": NEAR_REAL_TIME_NOTE,
        "step_results": step_results or [],
    }

    log.info(
        "Built pipeline run metadata: mode=%s status=%s missing_files=%d",
        pipeline_mode,
        status,
        len(missing_file_warnings),
    )

    return metadata
