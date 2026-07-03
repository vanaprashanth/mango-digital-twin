import sys
import datetime as dt
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.sections.fao56_model_comparison import render_fao56_model_comparison_page
from app.sections.water_balance import render_water_balance_page
from app.sections.phenology_water_balance import render_phenology_water_balance_page
from app.sections.fao56_sensitivity_analysis import render_fao56_sensitivity_analysis_page
from app.sections.irrigation_advisory import render_irrigation_advisory_page
from app.sections.mango_phenology import render_mango_phenology_page
from app.sections.combined_intelligence import render_combined_intelligence_page
from app.sections.vegetation_health import render_vegetation_health_page
from app.sections.soil_intelligence import render_soil_intelligence_page
from app.sections.historical_risk import render_historical_risk_page
from app.sections.forecast_risk import render_forecast_risk_page
from app.sections.overview_map import render_overview_map_page
from app.sections.what_if_simulator import render_what_if_simulator_page
from app.sections.raw_data import render_raw_data_page
from src.utils.config import get_config
from src.utils.soil_factor import soil_factor_label
from src.utils.pipeline_metadata import load_metadata_json
from src.utils.validation import (
    validate_risk_data,
    validate_soil_data,
    validate_vegetation_data,
    validate_combined_feature_data,
    validate_fao56_output,
    validate_phenology_output,
    validate_fao56_phenology_output,
    MissingColumnsError,
)

config = get_config()

DATA_PATH = config.path("historical_risk_csv")
FORECAST_DATA_PATH = config.path("forecast_risk_csv")
SOIL_DATA_PATH = config.path("soilgrids_csv")
NASA_POWER_RAW_PATH = config.path("nasa_power_csv")
OPEN_METEO_RAW_PATH = config.path("open_meteo_csv")
SENTINEL2_DAILY_PATH = config.path("sentinel2_daily_csv")
SENTINEL2_TIMESERIES_PATH = config.path("sentinel2_timeseries_csv")
COMBINED_FEATURE_TABLE_PATH = config.path("combined_feature_table_csv")
FAO56_WATER_BALANCE_PATH = config.path("fao56_water_balance_csv")
PHENOLOGY_CALENDAR_PATH = config.path("mango_phenology_calendar_csv")
FAO56_PHENOLOGY_WATER_BALANCE_PATH = config.path("fao56_phenology_water_balance_csv")
FAO56_MODEL_COMPARISON_CSV_PATH = config.path("fao56_model_comparison_csv")
FAO56_MODEL_COMPARISON_SUMMARY_MD_PATH = config.path("fao56_model_comparison_summary_md")
FORECAST_AWARE_ADVISORY_PATH = config.path("forecast_aware_irrigation_advisory_csv")
FAO56_SENSITIVITY_CSV_PATH = config.path("fao56_sensitivity_analysis_csv")
FAO56_SENSITIVITY_SUMMARY_MD_PATH = config.path("fao56_sensitivity_summary_md")
PIPELINE_METADATA_PATH = config.path("pipeline_run_metadata_json")


st.set_page_config(
    page_title="Mango Digital Twin",
    page_icon="🥭",
    layout="wide"
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def risk_color(level: str) -> str:
    """Return emoji indicator based on risk level."""
    if level == "High":
        return "🔴 High"
    elif level == "Medium":
        return "🟠 Medium"
    else:
        return "🟢 Low"


def classify_risk(score: float) -> str:
    """Convert numeric risk score into category."""
    if score >= 0.70:
        return "High"
    elif score >= 0.40:
        return "Medium"
    else:
        return "Low"


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    """Load a processed mango risk dataset and check it has the expected columns."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    validate_risk_data(df)
    return df


@st.cache_data
def load_soil_data(path: Path) -> pd.DataFrame:
    """Load SoilGrids point soil data and check it has the expected columns."""
    df = pd.read_csv(path)
    validate_soil_data(df)
    return df


@st.cache_data
def load_vegetation_data(path: Path) -> pd.DataFrame:
    """Load the daily Sentinel-2 vegetation index CSV and check its columns."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    validate_vegetation_data(df)
    return df


@st.cache_data
def load_vegetation_timeseries_data(path: Path) -> pd.DataFrame:
    """
    Load the image-level Sentinel-2 time series CSV (one row per scene, may
    include duplicate dates). No column validation beyond what pandas does
    by default — this is only shown as a raw reference table.
    """
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df


@st.cache_data
def load_combined_feature_data(path: Path) -> pd.DataFrame:
    """
    Load the combined weather + soil + vegetation feature table and check
    its columns. `date` is the weather date; `sentinel2_date` (already a
    column in the file) is the date of the matched satellite observation,
    which can be earlier than `date` or missing entirely for the first
    few rows before any Sentinel-2 scene existed.
    """
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    if "sentinel2_date" in df.columns:
        df["sentinel2_date"] = pd.to_datetime(df["sentinel2_date"])
    df = df.sort_values("date")
    validate_combined_feature_data(df)
    return df


def safe_load_data(path: Path, label: str) -> pd.DataFrame | None:
    """
    Load a processed risk CSV, but never crash the whole dashboard if the
    file is missing, empty, or malformed. Shows a friendly warning instead.
    """
    try:
        return load_data(path)
    except FileNotFoundError:
        st.warning(f"{label} file not found at `{path}`. This section will be unavailable.")
    except MissingColumnsError as exc:
        st.warning(f"{label} file is missing expected columns and could not be loaded.\n\n{exc}")
    except Exception as exc:  # pandas parse errors, empty file, etc.
        st.warning(f"{label} file could not be loaded ({exc.__class__.__name__}): {exc}")
    return None


def safe_load_soil_data(path: Path, label: str) -> pd.DataFrame | None:
    """Same as safe_load_data, but for the SoilGrids soil-properties CSV."""
    try:
        return load_soil_data(path)
    except FileNotFoundError:
        st.warning(f"{label} file not found at `{path}`. This section will be unavailable.")
    except MissingColumnsError as exc:
        st.warning(f"{label} file is missing expected columns and could not be loaded.\n\n{exc}")
    except Exception as exc:
        st.warning(f"{label} file could not be loaded ({exc.__class__.__name__}): {exc}")
    return None


def safe_load_vegetation_data(path: Path, label: str) -> pd.DataFrame | None:
    """Same pattern as safe_load_data, but for the daily Sentinel-2 vegetation index CSV."""
    try:
        return load_vegetation_data(path)
    except FileNotFoundError:
        st.warning(f"{label} file not found at `{path}`. This section will be unavailable.")
    except MissingColumnsError as exc:
        st.warning(f"{label} file is missing expected columns and could not be loaded.\n\n{exc}")
    except Exception as exc:
        st.warning(f"{label} file could not be loaded ({exc.__class__.__name__}): {exc}")
    return None


def safe_load_vegetation_timeseries_data(path: Path, label: str) -> pd.DataFrame | None:
    """Same pattern, but for the raw image-level Sentinel-2 time series CSV (no column validation)."""
    try:
        return load_vegetation_timeseries_data(path)
    except FileNotFoundError:
        st.warning(f"{label} file not found at `{path}`. This section will be unavailable.")
    except Exception as exc:
        st.warning(f"{label} file could not be loaded ({exc.__class__.__name__}): {exc}")
    return None


def safe_load_combined_feature_data(path: Path, label: str) -> pd.DataFrame | None:
    """Same pattern as safe_load_data, but for the combined weather/soil/vegetation feature table."""
    try:
        return load_combined_feature_data(path)
    except FileNotFoundError:
        st.warning(f"{label} file not found at `{path}`. This section will be unavailable.")
    except MissingColumnsError as exc:
        st.warning(f"{label} file is missing expected columns and could not be loaded.\n\n{exc}")
    except Exception as exc:
        st.warning(f"{label} file could not be loaded ({exc.__class__.__name__}): {exc}")
    return None


@st.cache_data
def load_fao56_water_balance_data(path: Path) -> pd.DataFrame:
    """Load the standalone FAO-56 soil-water balance CSV and check its columns."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    validate_fao56_output(df)
    return df


def safe_load_fao56_water_balance_data(path: Path, label: str) -> pd.DataFrame | None:
    """Same pattern as safe_load_data, but for the FAO-56 soil-water balance CSV."""
    try:
        return load_fao56_water_balance_data(path)
    except FileNotFoundError:
        st.warning(f"{label} file not found at `{path}`. This section will be unavailable.")
    except MissingColumnsError as exc:
        st.warning(f"{label} file is missing expected columns and could not be loaded.\n\n{exc}")
    except Exception as exc:
        st.warning(f"{label} file could not be loaded ({exc.__class__.__name__}): {exc}")
    return None


@st.cache_data
def load_phenology_calendar_data(path: Path) -> pd.DataFrame:
    """Load the standalone mango phenology calendar CSV and check its columns."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    validate_phenology_output(df)
    return df


def safe_load_phenology_calendar_data(path: Path, label: str) -> pd.DataFrame | None:
    """Same pattern as safe_load_data, but for the mango phenology calendar CSV."""
    try:
        return load_phenology_calendar_data(path)
    except FileNotFoundError:
        st.warning(f"{label} file not found at `{path}`. This section will be unavailable.")
    except MissingColumnsError as exc:
        st.warning(f"{label} file is missing expected columns and could not be loaded.\n\n{exc}")
    except Exception as exc:
        st.warning(f"{label} file could not be loaded ({exc.__class__.__name__}): {exc}")
    return None


@st.cache_data
def load_fao56_phenology_water_balance_data(path: Path) -> pd.DataFrame:
    """Load the standalone phenology-aware FAO-56 soil-water balance CSV and check its columns."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    validate_fao56_phenology_output(df)
    return df


def safe_load_fao56_phenology_water_balance_data(path: Path, label: str) -> pd.DataFrame | None:
    """Same pattern as safe_load_data, but for the phenology-aware FAO-56 soil-water balance CSV."""
    try:
        return load_fao56_phenology_water_balance_data(path)
    except FileNotFoundError:
        st.warning(f"{label} file not found at `{path}`. This section will be unavailable.")
    except MissingColumnsError as exc:
        st.warning(f"{label} file is missing expected columns and could not be loaded.\n\n{exc}")
    except Exception as exc:
        st.warning(f"{label} file could not be loaded ({exc.__class__.__name__}): {exc}")
    return None


@st.cache_data
def load_fao56_model_comparison_data(path: Path) -> pd.DataFrame:
    """Load the standalone FAO-56 model comparison CSV (constant-Kc vs phenology-aware)."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df


def safe_load_fao56_model_comparison_data(path: Path, label: str) -> pd.DataFrame | None:
    """
    Load the FAO-56 model comparison CSV, but never crash the dashboard if it's
    missing or malformed. Shows the specific re-run hint requested for this page
    if the file simply doesn't exist yet.
    """
    try:
        return load_fao56_model_comparison_data(path)
    except FileNotFoundError:
        st.info("Run `python main.py --skip-fetch` to generate the FAO-56 model comparison output.")
    except Exception as exc:  # pandas parse errors, empty file, etc.
        st.warning(f"{label} file could not be loaded ({exc.__class__.__name__}): {exc}")
    return None


def load_fao56_model_comparison_summary_text(path: Path) -> str | None:
    """Load the markdown summary for the FAO-56 model comparison, or return None if missing/unreadable."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except Exception:
        return None


@st.cache_data
def load_fao56_sensitivity_data(path: Path) -> pd.DataFrame:
    """Load the FAO-56 sensitivity analysis CSV."""
    df = pd.read_csv(path)
    return df


def safe_load_fao56_sensitivity_data(path: Path, label: str) -> pd.DataFrame | None:
    """Load FAO-56 sensitivity CSV without crashing the dashboard if missing/malformed."""
    try:
        return load_fao56_sensitivity_data(path)
    except FileNotFoundError:
        st.info("Run `python main.py` to generate the FAO-56 sensitivity analysis output.")
    except Exception as exc:
        st.warning(f"{label} file could not be loaded ({exc.__class__.__name__}): {exc}")
    return None


def load_fao56_sensitivity_summary_text(path: Path) -> str | None:
    """Load the markdown summary for the FAO-56 sensitivity analysis, or None if missing."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except Exception:
        return None


@st.cache_data
def load_irrigation_advisory_data(path: Path) -> pd.DataFrame:
    """Load the forecast-aware irrigation advisory CSV (single-row snapshot)."""
    df = pd.read_csv(path)
    return df


def safe_load_irrigation_advisory_data(path: Path, label: str) -> pd.DataFrame | None:
    """
    Load the irrigation advisory CSV without crashing the dashboard.
    Shows the specific re-run hint if the file simply doesn't exist yet.
    """
    try:
        return load_irrigation_advisory_data(path)
    except FileNotFoundError:
        st.info("Run `python main.py --skip-fetch` to generate the forecast-aware irrigation advisory.")
    except Exception as exc:
        st.warning(f"{label} file could not be loaded ({exc.__class__.__name__}): {exc}")
    return None


def file_status(path: Path) -> dict:
    """
    Return a small status record for a data file: whether it exists and,
    if so, when it was last modified. Used to render data-source badges
    in the sidebar so it's obvious at a glance which pipeline stages have
    actually run and how fresh each file is.
    """
    if not path.exists():
        return {"exists": False, "modified": None}

    modified_ts = dt.datetime.fromtimestamp(path.stat().st_mtime)
    return {"exists": True, "modified": modified_ts}


def render_status_badge(label: str, path: Path) -> None:
    """Render a single data-source status badge in the sidebar."""
    status = file_status(path)

    if not status["exists"]:
        st.sidebar.markdown(f"🔴 **{label}** — missing")
        return

    age = dt.datetime.now() - status["modified"]
    age_hours = age.total_seconds() / 3600

    if age_hours <= 48:
        indicator = "🟢"
    elif age_hours <= 24 * 14:
        indicator = "🟡"
    else:
        indicator = "🟠"

    st.sidebar.markdown(
        f"{indicator} **{label}** — updated {status['modified'].strftime('%Y-%m-%d %H:%M')}"
    )


def _format_metadata_timestamp(iso_timestamp: str | None) -> str:
    """Format an ISO-8601 UTC timestamp from the metadata JSON for display."""
    if not iso_timestamp:
        return "Unknown"
    try:
        parsed = dt.datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        return f"{parsed.strftime('%Y-%m-%d %H:%M')} UTC"
    except ValueError:
        return iso_timestamp


def render_data_freshness_section() -> None:
    """
    Render the "near-real-time" data freshness summary: when the pipeline
    last ran and how current each key data source is, read from
    data/processed/pipeline_run_metadata.json (written by
    src/pipeline/run_pipeline.py). Never raises -- if the metadata file is
    missing or unreadable, shows a friendly message instead.
    """
    st.sidebar.subheader("Data freshness")

    metadata = load_metadata_json(PIPELINE_METADATA_PATH)

    if metadata is None:
        st.sidebar.info("Run `python main.py --skip-fetch` to generate pipeline metadata.")
        return

    status = metadata.get("status", "unknown")
    status_indicator = "🟢" if status == "success" else "🔴"
    st.sidebar.markdown(
        f"{status_indicator} **Last pipeline run:** "
        f"{_format_metadata_timestamp(metadata.get('run_completed_at'))} ({metadata.get('pipeline_mode', 'unknown mode')})"
    )

    latest_dates = metadata.get("latest_dates", {})
    freshness_rows = [
        ("Weather risk", latest_dates.get("weather_risk_latest_date")),
        ("Open-Meteo forecast", latest_dates.get("open_meteo_forecast_latest_date")),
        ("Sentinel-2 observation", latest_dates.get("sentinel2_daily_latest_date")),
        ("Phenology-aware FAO-56", latest_dates.get("fao56_phenology_water_balance_latest_date")),
        ("Model comparison", latest_dates.get("fao56_model_comparison_latest_date")),
    ]
    for label, latest_date in freshness_rows:
        st.sidebar.caption(f"{label}: {latest_date if latest_date else 'not available'}")

    missing_warnings = metadata.get("missing_file_warnings", [])
    if missing_warnings:
        st.sidebar.warning(f"{len(missing_warnings)} expected file(s) missing — see Raw Data / status badges above.")


# ---------------------------------------------------------------------
# Load data (shared across all pages)
# ---------------------------------------------------------------------

if not DATA_PATH.exists():
    st.error("Processed historical risk file not found.")
    st.info("Please run: python src/risk/historical_risk_engine.py (or `python main.py`)")
    st.stop()

df = safe_load_data(DATA_PATH, "Historical risk")
if df is None or df.empty:
    st.error("Historical risk data could not be loaded or is empty. The dashboard cannot continue.")
    st.info("Please run: python src/risk/historical_risk_engine.py (or `python main.py`)")
    st.stop()

latest = df.iloc[-1]
has_soil_adjusted_irrigation = "soil_adjusted_irrigation_risk_level" in df.columns

forecast_df = None
soil_df = None
vegetation_df = None
vegetation_timeseries_df = None
combined_feature_df = None

if FORECAST_DATA_PATH.exists():
    forecast_df = safe_load_data(FORECAST_DATA_PATH, "Forecast risk")

if SOIL_DATA_PATH.exists():
    soil_df = safe_load_soil_data(SOIL_DATA_PATH, "SoilGrids soil")

if SENTINEL2_DAILY_PATH.exists():
    vegetation_df = safe_load_vegetation_data(SENTINEL2_DAILY_PATH, "Sentinel-2 daily vegetation")

if SENTINEL2_TIMESERIES_PATH.exists():
    vegetation_timeseries_df = safe_load_vegetation_timeseries_data(
        SENTINEL2_TIMESERIES_PATH, "Sentinel-2 image-level vegetation"
    )

if COMBINED_FEATURE_TABLE_PATH.exists():
    combined_feature_df = safe_load_combined_feature_data(
        COMBINED_FEATURE_TABLE_PATH, "Combined feature table"
    )

fao56_water_balance_df = None

if FAO56_WATER_BALANCE_PATH.exists():
    fao56_water_balance_df = safe_load_fao56_water_balance_data(
        FAO56_WATER_BALANCE_PATH, "FAO-56 water balance"
    )

phenology_df = None

if PHENOLOGY_CALENDAR_PATH.exists():
    phenology_df = safe_load_phenology_calendar_data(
        PHENOLOGY_CALENDAR_PATH, "Mango phenology calendar"
    )

fao56_phenology_water_balance_df = None

if FAO56_PHENOLOGY_WATER_BALANCE_PATH.exists():
    fao56_phenology_water_balance_df = safe_load_fao56_phenology_water_balance_data(
        FAO56_PHENOLOGY_WATER_BALANCE_PATH, "Phenology-aware FAO-56 water balance"
    )

fao56_model_comparison_df = None

if FAO56_MODEL_COMPARISON_CSV_PATH.exists():
    fao56_model_comparison_df = safe_load_fao56_model_comparison_data(
        FAO56_MODEL_COMPARISON_CSV_PATH, "FAO-56 model comparison"
    )

fao56_model_comparison_summary_text = None

if FAO56_MODEL_COMPARISON_SUMMARY_MD_PATH.exists():
    fao56_model_comparison_summary_text = load_fao56_model_comparison_summary_text(
        FAO56_MODEL_COMPARISON_SUMMARY_MD_PATH
    )

irrigation_advisory_df = None

if FORECAST_AWARE_ADVISORY_PATH.exists():
    irrigation_advisory_df = safe_load_irrigation_advisory_data(
        FORECAST_AWARE_ADVISORY_PATH, "Irrigation advisory"
    )

fao56_sensitivity_df = None

if FAO56_SENSITIVITY_CSV_PATH.exists():
    fao56_sensitivity_df = safe_load_fao56_sensitivity_data(
        FAO56_SENSITIVITY_CSV_PATH, "FAO-56 sensitivity analysis"
    )

fao56_sensitivity_summary_text = None

if FAO56_SENSITIVITY_SUMMARY_MD_PATH.exists():
    fao56_sensitivity_summary_text = load_fao56_sensitivity_summary_text(
        FAO56_SENSITIVITY_SUMMARY_MD_PATH
    )


# ---------------------------------------------------------------------
# Sidebar — navigation, study area, data source status
# ---------------------------------------------------------------------

st.sidebar.title("🥭 Mango Digital Twin")
st.sidebar.caption(f"{config.study_area.name}")
st.sidebar.caption(f"{config.study_area.district} district, {config.study_area.state}, {config.study_area.country}")

page = st.sidebar.radio(
    "Navigate",
    [
        "Overview & Map",
        "Historical Risk",
        "Forecast Risk",
        "Soil Intelligence",
        "Vegetation Health",
        "Combined Intelligence",
        "Water Balance",
        "Mango Phenology",
        "Phenology Water Balance",
        "FAO-56 Model Comparison",
        "FAO-56 Sensitivity Analysis",
        "Irrigation Advisory",
        "What-if Simulator",
        "Raw Data",
    ],
)

st.sidebar.divider()
st.sidebar.subheader("Data source status")
render_status_badge("NASA POWER (raw)", NASA_POWER_RAW_PATH)
render_status_badge("Open-Meteo (raw)", OPEN_METEO_RAW_PATH)
render_status_badge("SoilGrids (raw)", SOIL_DATA_PATH)
render_status_badge("Historical risk (processed)", DATA_PATH)
render_status_badge("Forecast risk (processed)", FORECAST_DATA_PATH)
render_status_badge("Sentinel-2 daily vegetation (processed)", SENTINEL2_DAILY_PATH)
render_status_badge("Combined feature table (processed)", COMBINED_FEATURE_TABLE_PATH)
render_status_badge("FAO-56 water balance (processed)", FAO56_WATER_BALANCE_PATH)
render_status_badge("Mango phenology calendar (processed)", PHENOLOGY_CALENDAR_PATH)
render_status_badge("Phenology-aware FAO-56 water balance (processed)", FAO56_PHENOLOGY_WATER_BALANCE_PATH)
render_status_badge("FAO-56 model comparison (processed)", FAO56_MODEL_COMPARISON_CSV_PATH)
render_status_badge("FAO-56 sensitivity analysis (processed)", FAO56_SENSITIVITY_CSV_PATH)
render_status_badge("Irrigation advisory (processed)", FORECAST_AWARE_ADVISORY_PATH)

st.sidebar.divider()
render_data_freshness_section()

st.sidebar.divider()
st.sidebar.caption(
    "Future prediction = Open-Meteo weather forecast + risk rules, not a trained ML model yet."
)
st.sidebar.caption(
    "This is a near-real-time digital twin: forecast weather updates often, Sentinel-2 every few "
    "days, NASA POWER historical data can lag, and SoilGrids is mostly static."
)


# =======================================================================
# PAGE: Overview & Map
# =======================================================================

if page == "Overview & Map":
    render_overview_map_page(config, latest, has_soil_adjusted_irrigation)


# =======================================================================
# PAGE: Historical Risk
# =======================================================================

elif page == "Historical Risk":
    render_historical_risk_page(df)


# =======================================================================
# PAGE: Forecast Risk
# =======================================================================

elif page == "Forecast Risk":
    render_forecast_risk_page(forecast_df)


# =======================================================================
# PAGE: Soil Intelligence
# =======================================================================

elif page == "Soil Intelligence":
    render_soil_intelligence_page(soil_df, latest, has_soil_adjusted_irrigation)


# =======================================================================
# PAGE: Vegetation Health
# =======================================================================

elif page == "Vegetation Health":
    render_vegetation_health_page(vegetation_df, vegetation_timeseries_df)


# =======================================================================
# PAGE: Combined Intelligence
# =======================================================================

elif page == "Combined Intelligence":
    render_combined_intelligence_page(combined_feature_df)


# =======================================================================
# PAGE: Water Balance (FAO-56, standalone)
# =======================================================================

elif page == "Water Balance":
    render_water_balance_page(fao56_water_balance_df)


# =======================================================================
# PAGE: Mango Phenology (standalone calendar)
# =======================================================================

elif page == "Mango Phenology":
    render_mango_phenology_page(phenology_df)


# =======================================================================
# PAGE: Phenology Water Balance (phenology-aware FAO-56, standalone)
# =======================================================================

elif page == "Phenology Water Balance":
    render_phenology_water_balance_page(fao56_phenology_water_balance_df, fao56_water_balance_df)


# =======================================================================
# PAGE: FAO-56 Model Comparison
# =======================================================================

elif page == "FAO-56 Model Comparison":
    render_fao56_model_comparison_page(fao56_model_comparison_df, fao56_model_comparison_summary_text)


# =======================================================================
# PAGE: FAO-56 Sensitivity Analysis
# =======================================================================

elif page == "FAO-56 Sensitivity Analysis":
    render_fao56_sensitivity_analysis_page(fao56_sensitivity_df, fao56_sensitivity_summary_text)


# =======================================================================
# PAGE: Irrigation Advisory
# =======================================================================

elif page == "Irrigation Advisory":
    render_irrigation_advisory_page(irrigation_advisory_df)


# =======================================================================
# PAGE: What-if Simulator
# =======================================================================

elif page == "What-if Simulator":
    render_what_if_simulator_page(latest)


# =======================================================================
# PAGE: Raw Data
# =======================================================================

elif page == "Raw Data":
    render_raw_data_page(df, forecast_df, soil_df, vegetation_df, phenology_df, fao56_phenology_water_balance_df)
