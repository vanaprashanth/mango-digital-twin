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


def simulate_weather_risk(
    rainfall_7day_mm: float,
    temperature_max_c: float,
    temperature_avg_c: float,
    relative_humidity_percent: float,
    solar_radiation_mj_m2: float,
    rainfall_change_percent: float,
    temperature_change_c: float,
    humidity_change_percent: float,
):
    """Simulate mango risk under changed weather conditions."""

    simulated_rainfall_7day = rainfall_7day_mm * (1 + rainfall_change_percent / 100)
    simulated_temp_max = temperature_max_c + temperature_change_c
    simulated_temp_avg = temperature_avg_c + temperature_change_c
    simulated_humidity = relative_humidity_percent + humidity_change_percent

    simulated_humidity = max(0, min(simulated_humidity, 100))
    simulated_rainfall_7day = max(0, simulated_rainfall_7day)

    irrigation_score = 0.0

    if simulated_rainfall_7day < 10:
        irrigation_score += 0.45
    elif simulated_rainfall_7day < 25:
        irrigation_score += 0.25

    if simulated_temp_max >= 35:
        irrigation_score += 0.35
    elif simulated_temp_max >= 32:
        irrigation_score += 0.20

    if solar_radiation_mj_m2 >= 22:
        irrigation_score += 0.20
    elif solar_radiation_mj_m2 >= 18:
        irrigation_score += 0.10

    irrigation_score = min(irrigation_score, 1.0)

    heat_score = 0.0

    if simulated_temp_max >= 40:
        heat_score += 0.80
    elif simulated_temp_max >= 37:
        heat_score += 0.60
    elif simulated_temp_max >= 35:
        heat_score += 0.40
    elif simulated_temp_max >= 32:
        heat_score += 0.20

    if simulated_temp_avg >= 30:
        heat_score += 0.20

    heat_score = min(heat_score, 1.0)

    disease_score = 0.0

    if simulated_humidity >= 85:
        disease_score += 0.45
    elif simulated_humidity >= 75:
        disease_score += 0.30
    elif simulated_humidity >= 65:
        disease_score += 0.15

    if 24 <= simulated_temp_avg <= 30:
        disease_score += 0.30
    elif 20 <= simulated_temp_avg < 24:
        disease_score += 0.15

    if simulated_rainfall_7day >= 40:
        disease_score += 0.25
    elif simulated_rainfall_7day >= 15:
        disease_score += 0.10

    disease_score = min(disease_score, 1.0)

    return {
        "simulated_rainfall_7day_mm": simulated_rainfall_7day,
        "simulated_temperature_max_c": simulated_temp_max,
        "simulated_temperature_avg_c": simulated_temp_avg,
        "simulated_humidity_percent": simulated_humidity,
        "irrigation_risk_score": irrigation_score,
        "heat_stress_risk_score": heat_score,
        "disease_risk_score": disease_score,
        "irrigation_risk_level": classify_risk(irrigation_score),
        "heat_stress_risk_level": classify_risk(heat_score),
        "disease_risk_level": classify_risk(disease_score),
    }


def generate_simulation_explanation(simulation: dict) -> list[str]:
    """Generate human-readable explanations for simulated risk results."""

    explanations = []

    rainfall_7day = simulation["simulated_rainfall_7day_mm"]
    temp_max = simulation["simulated_temperature_max_c"]
    temp_avg = simulation["simulated_temperature_avg_c"]
    humidity = simulation["simulated_humidity_percent"]

    irrigation_level = simulation["irrigation_risk_level"]
    heat_level = simulation["heat_stress_risk_level"]
    disease_level = simulation["disease_risk_level"]

    if irrigation_level == "High":
        explanations.append(
            "Irrigation risk is high because simulated 7-day rainfall is low and/or temperature stress is elevated."
        )
    elif irrigation_level == "Medium":
        explanations.append(
            "Irrigation risk is medium because rainfall or temperature conditions may create moderate water stress."
        )
    else:
        explanations.append(
            "Irrigation risk is low because simulated recent rainfall is sufficient or temperature stress is limited."
        )

    if heat_level == "High":
        explanations.append(
            f"Heat stress is high because simulated maximum temperature reaches {temp_max:.2f} °C."
        )
    elif heat_level == "Medium":
        explanations.append(
            f"Heat stress is medium because simulated maximum temperature is {temp_max:.2f} °C."
        )
    else:
        explanations.append(
            f"Heat stress is low because simulated maximum temperature is {temp_max:.2f} °C."
        )

    if disease_level == "High":
        explanations.append(
            f"Disease-friendly weather is high because humidity is {humidity:.2f}% and recent rainfall is {rainfall_7day:.2f} mm."
        )
    elif disease_level == "Medium":
        explanations.append(
            f"Disease-friendly weather is medium because humidity is {humidity:.2f}% with moderate rainfall or suitable temperature."
        )
    else:
        explanations.append(
            "Disease risk is low because humidity, rainfall, or temperature are not strongly disease-favorable."
        )

    if rainfall_7day < 10:
        explanations.append(
            "The simulated 7-day rainfall is below 10 mm, which may increase water-stress risk."
        )

    if temp_max >= 35:
        explanations.append(
            "The simulated maximum temperature is above 35 °C, which may increase mango heat stress."
        )

    if humidity >= 75 and 24 <= temp_avg <= 30:
        explanations.append(
            "Humidity is high and average temperature is within a disease-favorable range, so fungal-risk conditions may increase."
        )

    return explanations


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
    st.title("🥭 Sensor-Free Mango Digital Twin")
    st.caption(f"{config.study_area.name}, {config.study_area.district} district, {config.study_area.state}")

    st.subheader("Latest Digital Twin Status")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(label="Latest valid date", value=latest["date"].strftime("%Y-%m-%d"))

    with col2:
        st.metric(label="Irrigation risk (weather only)", value=risk_color(latest["irrigation_risk_level"]))

    with col3:
        if has_soil_adjusted_irrigation:
            st.metric(label="Irrigation risk (soil-adjusted)", value=risk_color(latest["soil_adjusted_irrigation_risk_level"]))
        else:
            st.metric(label="Irrigation risk (soil-adjusted)", value="N/A")

    with col4:
        st.metric(label="Heat stress risk", value=risk_color(latest["heat_stress_risk_level"]))

    with col5:
        st.metric(label="Disease risk", value=risk_color(latest["disease_risk_level"]))

    st.divider()

    st.subheader("Study Area Map")

    map_df = pd.DataFrame(
        {"lat": [config.latitude], "lon": [config.longitude]}
    )
    st.map(map_df, zoom=10)
    st.caption(
        f"Latitude {config.latitude}, Longitude {config.longitude} — "
        f"{config.study_area.name}, {config.study_area.district}, {config.study_area.state}, {config.study_area.country}"
    )

    st.divider()

    st.subheader("Latest Weather Conditions")

    weather_col1, weather_col2, weather_col3, weather_col4 = st.columns(4)

    with weather_col1:
        st.metric(label="Max temperature", value=f"{latest['temperature_max_c']:.2f} °C")

    with weather_col2:
        st.metric(label="Avg temperature", value=f"{latest['temperature_avg_c']:.2f} °C")

    with weather_col3:
        st.metric(label="Rainfall", value=f"{latest['rainfall_mm']:.2f} mm")

    with weather_col4:
        st.metric(label="7-day rainfall", value=f"{latest['rainfall_7day_mm']:.2f} mm")

    st.divider()

    st.subheader("Latest Recommendation")

    recommendations = []

    irrigation_level_for_advisory = (
        latest["soil_adjusted_irrigation_risk_level"]
        if has_soil_adjusted_irrigation
        else latest["irrigation_risk_level"]
    )

    if irrigation_level_for_advisory == "High":
        recommendations.append(
            "Irrigation attention is needed because recent rainfall is low and weather stress is elevated."
        )
    elif irrigation_level_for_advisory == "Medium":
        recommendations.append(
            "Monitor irrigation need. Rainfall or heat conditions may create moderate water stress."
        )
    else:
        recommendations.append(
            "Irrigation risk is currently low based on recent rainfall, temperature, and soil-adjusted water-retention behavior."
        )

    if latest["heat_stress_risk_level"] == "High":
        recommendations.append("Heat stress risk is high. Avoid crop operations during peak afternoon heat.")
    elif latest["heat_stress_risk_level"] == "Medium":
        recommendations.append("Moderate heat stress risk. Continue monitoring maximum temperature.")
    else:
        recommendations.append("Heat stress risk is currently low.")

    if latest["disease_risk_level"] == "High":
        recommendations.append("Disease-friendly weather conditions are high. Monitor orchard for fungal symptoms.")
    elif latest["disease_risk_level"] == "Medium":
        recommendations.append("Moderate disease-friendly conditions exist. Continue monitoring humidity and rainfall.")
    else:
        recommendations.append("Disease risk is currently low based on weather conditions.")

    for rec in recommendations:
        st.write(f"- {rec}")


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
    st.title("What-if Simulator")

    st.write("Test how mango risk changes if rainfall, temperature, or humidity changes from the latest valid weather condition.")

    sim_col1, sim_col2, sim_col3 = st.columns(3)

    with sim_col1:
        rainfall_change_percent = st.slider("Rainfall change (%)", min_value=-100, max_value=100, value=0, step=5)

    with sim_col2:
        temperature_change_c = st.slider("Temperature change (°C)", min_value=-5.0, max_value=8.0, value=0.0, step=0.5)

    with sim_col3:
        humidity_change_percent = st.slider("Humidity change (%)", min_value=-50, max_value=50, value=0, step=5)

    simulation = simulate_weather_risk(
        rainfall_7day_mm=latest["rainfall_7day_mm"],
        temperature_max_c=latest["temperature_max_c"],
        temperature_avg_c=latest["temperature_avg_c"],
        relative_humidity_percent=latest["relative_humidity_percent"],
        solar_radiation_mj_m2=latest["solar_radiation_mj_m2"],
        rainfall_change_percent=rainfall_change_percent,
        temperature_change_c=temperature_change_c,
        humidity_change_percent=humidity_change_percent,
    )

    st.write("### Simulated Weather Condition")

    sim_weather_col1, sim_weather_col2, sim_weather_col3, sim_weather_col4 = st.columns(4)

    with sim_weather_col1:
        st.metric(label="Simulated 7-day rainfall", value=f"{simulation['simulated_rainfall_7day_mm']:.2f} mm")

    with sim_weather_col2:
        st.metric(label="Simulated max temperature", value=f"{simulation['simulated_temperature_max_c']:.2f} °C")

    with sim_weather_col3:
        st.metric(label="Simulated avg temperature", value=f"{simulation['simulated_temperature_avg_c']:.2f} °C")

    with sim_weather_col4:
        st.metric(label="Simulated humidity", value=f"{simulation['simulated_humidity_percent']:.2f} %")

    st.write("### Simulated Risk Result")

    sim_risk_col1, sim_risk_col2, sim_risk_col3 = st.columns(3)

    with sim_risk_col1:
        st.metric(label="Simulated irrigation risk", value=risk_color(simulation["irrigation_risk_level"]), delta=f"{simulation['irrigation_risk_score']:.2f}")

    with sim_risk_col2:
        st.metric(label="Simulated heat stress risk", value=risk_color(simulation["heat_stress_risk_level"]), delta=f"{simulation['heat_stress_risk_score']:.2f}")

    with sim_risk_col3:
        st.metric(label="Simulated disease risk", value=risk_color(simulation["disease_risk_level"]), delta=f"{simulation['disease_risk_score']:.2f}")

    st.write("### Scenario Explanation")

    simulation_explanations = generate_simulation_explanation(simulation)

    for explanation in simulation_explanations:
        st.write(f"- {explanation}")


# =======================================================================
# PAGE: Raw Data
# =======================================================================

elif page == "Raw Data":
    st.title("Raw Processed Data")

    st.write("### Historical Risk Data")
    with st.expander("Historical risk table (last 20 rows)", expanded=False):
        preview_df = df.tail(20).copy()
        numeric_columns = preview_df.select_dtypes(include="number").columns
        preview_df[numeric_columns] = preview_df[numeric_columns].round(2)
        st.dataframe(preview_df, use_container_width=True)

    if forecast_df is not None and not forecast_df.empty:
        st.write("### Forecast Risk Data")
        with st.expander("Forecast risk table (full)", expanded=False):
            forecast_preview = forecast_df.copy()
            numeric_columns = forecast_preview.select_dtypes(include="number").columns
            forecast_preview[numeric_columns] = forecast_preview[numeric_columns].round(2)
            st.dataframe(forecast_preview, use_container_width=True)

    if soil_df is not None and not soil_df.empty:
        st.write("### SoilGrids Raw Data")
        with st.expander("SoilGrids raw points", expanded=False):
            st.dataframe(soil_df, use_container_width=True)

    if vegetation_df is not None and not vegetation_df.empty:
        st.write("### Sentinel-2 Daily Vegetation Data")
        with st.expander("Sentinel-2 daily vegetation table (full)", expanded=False):
            veg_preview = vegetation_df.copy()
            veg_preview["date"] = veg_preview["date"].dt.strftime("%Y-%m-%d")
            numeric_columns = veg_preview.select_dtypes(include="number").columns
            veg_preview[numeric_columns] = veg_preview[numeric_columns].round(3)
            st.dataframe(veg_preview, use_container_width=True)

    if phenology_df is not None and not phenology_df.empty:
        st.write("### Mango Phenology Calendar Data")
        with st.expander("Mango phenology calendar table (full)", expanded=False):
            phenology_raw_preview = phenology_df.copy()
            phenology_raw_preview["date"] = phenology_raw_preview["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(phenology_raw_preview, use_container_width=True)

    if fao56_phenology_water_balance_df is not None and not fao56_phenology_water_balance_df.empty:
        st.write("### Phenology-Aware FAO-56 Water Balance Data")
        with st.expander("Phenology-aware FAO-56 water balance table (full)", expanded=False):
            phen_wb_raw_preview = fao56_phenology_water_balance_df.copy()
            phen_wb_raw_preview["date"] = phen_wb_raw_preview["date"].dt.strftime("%Y-%m-%d")
            numeric_columns = phen_wb_raw_preview.select_dtypes(include="number").columns
            phen_wb_raw_preview[numeric_columns] = phen_wb_raw_preview[numeric_columns].round(3)
            st.dataframe(phen_wb_raw_preview, use_container_width=True)
