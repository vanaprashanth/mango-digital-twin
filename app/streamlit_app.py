import sys
import datetime as dt
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.append(str(Path(__file__).resolve().parents[1]))

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
    st.title("Historical Risk")

    st.subheader("Time Range Filter")

    min_date = df["date"].min().date()
    max_date = df["date"].max().date()

    selected_range = st.date_input(
        "Select date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = selected_range
        filtered_df = df[(df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)]
    else:
        filtered_df = df.copy()

    st.divider()

    st.subheader("Rainfall Trend")
    rain_fig = px.line(
        filtered_df, x="date", y=["rainfall_mm", "rainfall_7day_mm"],
        title="Daily Rainfall and 7-Day Rolling Rainfall",
        labels={"date": "Date", "value": "Rainfall (mm)", "variable": "Metric"}
    )
    st.plotly_chart(rain_fig, use_container_width=True)

    st.subheader("Temperature Trend")
    temp_fig = px.line(
        filtered_df, x="date", y=["temperature_avg_c", "temperature_max_c", "temperature_min_c"],
        title="Average, Maximum, and Minimum Temperature",
        labels={"date": "Date", "value": "Temperature (°C)", "variable": "Metric"}
    )
    st.plotly_chart(temp_fig, use_container_width=True)

    st.subheader("Risk Score Trend")
    risk_fig = px.line(
        filtered_df, x="date",
        y=["irrigation_risk_score", "heat_stress_risk_score", "disease_risk_score"],
        title="Mango Risk Scores Over Time",
        labels={"date": "Date", "value": "Risk score", "variable": "Risk type"}
    )
    st.plotly_chart(risk_fig, use_container_width=True)

    st.divider()

    st.subheader("Risk Summary")

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.write("**Irrigation Risk Days**")
        irrigation_counts = filtered_df["irrigation_risk_level"].value_counts().reindex(["Low", "Medium", "High"], fill_value=0)
        st.dataframe(irrigation_counts.rename("Days"), use_container_width=True)

    with summary_col2:
        st.write("**Heat Stress Risk Days**")
        heat_counts = filtered_df["heat_stress_risk_level"].value_counts().reindex(["Low", "Medium", "High"], fill_value=0)
        st.dataframe(heat_counts.rename("Days"), use_container_width=True)

    with summary_col3:
        st.write("**Disease Risk Days**")
        disease_counts = filtered_df["disease_risk_level"].value_counts().reindex(["Low", "Medium", "High"], fill_value=0)
        st.dataframe(disease_counts.rename("Days"), use_container_width=True)

    st.divider()

    st.subheader("Monthly Risk Summary")

    monthly_df = filtered_df.copy()
    monthly_df["month"] = monthly_df["date"].dt.to_period("M").astype(str)

    monthly_summary = (
        monthly_df.groupby("month").agg(
            avg_irrigation_risk=("irrigation_risk_score", "mean"),
            avg_heat_stress_risk=("heat_stress_risk_score", "mean"),
            avg_disease_risk=("disease_risk_score", "mean"),
            total_rainfall_mm=("rainfall_mm", "sum"),
            avg_max_temperature_c=("temperature_max_c", "mean"),
        ).reset_index()
    )

    monthly_summary = monthly_summary.round({
        "avg_irrigation_risk": 2, "avg_heat_stress_risk": 2, "avg_disease_risk": 2,
        "total_rainfall_mm": 2, "avg_max_temperature_c": 2,
    })

    with st.expander("Monthly risk summary table", expanded=False):
        st.dataframe(monthly_summary, use_container_width=True)

    if not monthly_summary.empty:
        highest_irrigation_month = monthly_summary.loc[monthly_summary["avg_irrigation_risk"].idxmax()]
        highest_heat_month = monthly_summary.loc[monthly_summary["avg_heat_stress_risk"].idxmax()]
        highest_disease_month = monthly_summary.loc[monthly_summary["avg_disease_risk"].idxmax()]

        risk_month_col1, risk_month_col2, risk_month_col3 = st.columns(3)

        with risk_month_col1:
            st.metric(label="Highest irrigation-risk month", value=highest_irrigation_month["month"], delta=f"{highest_irrigation_month['avg_irrigation_risk']:.2f}")

        with risk_month_col2:
            st.metric(label="Highest heat-risk month", value=highest_heat_month["month"], delta=f"{highest_heat_month['avg_heat_stress_risk']:.2f}")

        with risk_month_col3:
            st.metric(label="Highest disease-risk month", value=highest_disease_month["month"], delta=f"{highest_disease_month['avg_disease_risk']:.2f}")


# =======================================================================
# PAGE: Forecast Risk
# =======================================================================

elif page == "Forecast Risk":
    st.title("Forecast Risk Intelligence")

    if forecast_df is None or forecast_df.empty:
        st.warning("Forecast risk file not found.")
        st.info("Please run: python src/weather/fetch_open_meteo.py and then python src/risk/open_meteo_risk_engine.py")
    else:
        forecast_latest = forecast_df.iloc[-1]
        has_soil_adjusted_forecast_irrigation = "soil_adjusted_irrigation_risk_level" in forecast_df.columns

        st.caption(
            "Open-Meteo recent and forecast weather risk layer — future risk is computed by applying "
            "our risk rules to Open-Meteo's API forecast values, not by a trained prediction model."
        )

        forecast_period_start = forecast_df["date"].min().strftime("%Y-%m-%d")
        forecast_period_end = forecast_df["date"].max().strftime("%Y-%m-%d")

        st.metric(
            label="Forecast date range",
            value=f"{forecast_period_start} → {forecast_period_end}",
            delta=f"{len(forecast_df)} days"
        )

        forecast_col1, forecast_col2, forecast_col3, forecast_col4 = st.columns(4)

        with forecast_col1:
            st.metric(label="Forecast irrigation risk (weather only)", value=risk_color(forecast_latest["irrigation_risk_level"]))

        with forecast_col2:
            if has_soil_adjusted_forecast_irrigation:
                st.metric(label="Forecast irrigation risk (soil-adjusted)", value=risk_color(forecast_latest["soil_adjusted_irrigation_risk_level"]))
            else:
                st.metric(label="Forecast irrigation risk (soil-adjusted)", value="N/A")

        with forecast_col3:
            st.metric(label="Forecast heat stress risk", value=risk_color(forecast_latest["heat_stress_risk_level"]))

        with forecast_col4:
            st.metric(label="Forecast disease risk", value=risk_color(forecast_latest["disease_risk_level"]))

        st.write("### Forecast Weather Conditions")

        forecast_weather_col1, forecast_weather_col2, forecast_weather_col3, forecast_weather_col4 = st.columns(4)

        with forecast_weather_col1:
            st.metric(label="Forecast max temperature", value=f"{forecast_latest['temperature_max_c']:.2f} °C")

        with forecast_weather_col2:
            st.metric(label="Forecast avg temperature", value=f"{forecast_latest['temperature_avg_c']:.2f} °C")

        with forecast_weather_col3:
            st.metric(label="Forecast rainfall", value=f"{forecast_latest['rainfall_mm']:.2f} mm")

        with forecast_weather_col4:
            st.metric(label="Forecast 7-day rainfall", value=f"{forecast_latest['rainfall_7day_mm']:.2f} mm")

        st.write("### Forecast Rainfall Trend")
        forecast_rain_fig = px.line(
            forecast_df, x="date", y=["rainfall_mm", "rainfall_7day_mm"],
            title="Open-Meteo Forecast Rainfall and 7-Day Rolling Rainfall",
            labels={"date": "Date", "value": "Rainfall (mm)", "variable": "Metric"}
        )
        st.plotly_chart(forecast_rain_fig, use_container_width=True)

        st.write("### Forecast Temperature Trend")
        forecast_temp_fig = px.line(
            forecast_df, x="date", y=["temperature_avg_c", "temperature_max_c", "temperature_min_c"],
            title="Open-Meteo Forecast Temperature",
            labels={"date": "Date", "value": "Temperature (°C)", "variable": "Metric"}
        )
        st.plotly_chart(forecast_temp_fig, use_container_width=True)

        st.write("### Forecast Risk Score Trend")
        forecast_risk_fig = px.line(
            forecast_df, x="date",
            y=["irrigation_risk_score", "heat_stress_risk_score", "disease_risk_score"],
            title="Open-Meteo Forecast Mango Risk Scores",
            labels={"date": "Date", "value": "Risk score", "variable": "Risk type"}
        )
        st.plotly_chart(forecast_risk_fig, use_container_width=True)

        st.write("### Forecast Risk Table")

        forecast_table_columns = [
            "date", "rainfall_mm", "rainfall_7day_mm", "temperature_max_c",
            "relative_humidity_percent", "irrigation_risk_level",
        ]

        if has_soil_adjusted_forecast_irrigation:
            forecast_table_columns.append("soil_adjusted_irrigation_risk_level")

        forecast_table_columns += ["heat_stress_risk_level", "disease_risk_level"]

        forecast_table_df = forecast_df[forecast_table_columns].copy()
        forecast_table_df["date"] = forecast_table_df["date"].dt.strftime("%Y-%m-%d")

        numeric_forecast_columns = forecast_table_df.select_dtypes(include="number").columns
        forecast_table_df[numeric_forecast_columns] = forecast_table_df[numeric_forecast_columns].round(2)

        forecast_table_df = forecast_table_df.rename(columns={
            "date": "Date",
            "rainfall_mm": "Rainfall (mm)",
            "rainfall_7day_mm": "7-day rainfall (mm)",
            "temperature_max_c": "Max temp (°C)",
            "relative_humidity_percent": "Humidity (%)",
            "irrigation_risk_level": "Irrigation risk",
            "soil_adjusted_irrigation_risk_level": "Irrigation risk (soil-adjusted)",
            "heat_stress_risk_level": "Heat stress risk",
            "disease_risk_level": "Disease risk",
        })

        with st.expander("Forecast risk table (all future dates)", expanded=True):
            st.dataframe(forecast_table_df, use_container_width=True)

        st.write("### Forecast Advisory")

        forecast_recommendations = []

        if forecast_latest["irrigation_risk_level"] == "High":
            forecast_recommendations.append("Forecast irrigation risk is high. Plan irrigation because upcoming rainfall may be insufficient.")
        elif forecast_latest["irrigation_risk_level"] == "Medium":
            forecast_recommendations.append("Forecast irrigation risk is medium. Monitor rainfall and soil moisture conditions closely.")
        else:
            forecast_recommendations.append("Forecast irrigation risk is low based on upcoming rainfall and temperature.")

        if forecast_latest["heat_stress_risk_level"] == "High":
            forecast_recommendations.append("Forecast heat stress is high. Avoid stressful orchard operations during peak heat periods.")
        elif forecast_latest["heat_stress_risk_level"] == "Medium":
            forecast_recommendations.append("Forecast heat stress is medium. Continue monitoring maximum temperature.")
        else:
            forecast_recommendations.append("Forecast heat stress is low.")

        if forecast_latest["disease_risk_level"] == "High":
            forecast_recommendations.append("Forecast disease-friendly conditions are high. Monitor orchard for fungal symptoms.")
        elif forecast_latest["disease_risk_level"] == "Medium":
            forecast_recommendations.append("Forecast disease-friendly conditions are medium. Watch humidity and rainfall conditions.")
        else:
            forecast_recommendations.append("Forecast disease risk is low.")

        for rec in forecast_recommendations:
            st.write(f"- {rec}")


# =======================================================================
# PAGE: Soil Intelligence
# =======================================================================

elif page == "Soil Intelligence":
    st.title("Soil Intelligence")

    if soil_df is None or soil_df.empty:
        st.warning("SoilGrids data file not found.")
        st.info("Please run: python src/soil/fetch_soilgrids.py")
    else:
        topsoil_summary = (
            soil_df.groupby("property").agg(
                average_0_30cm=("converted_value", "mean"),
                unit=("unit", "first"),
            ).reset_index()
        )

        soil_lookup = {row["property"]: row["average_0_30cm"] for _, row in topsoil_summary.iterrows()}

        soil_col1, soil_col2, soil_col3, soil_col4 = st.columns(4)

        with soil_col1:
            st.metric(label="Soil pH", value=f"{soil_lookup.get('phh2o', 0):.2f}")

        with soil_col2:
            st.metric(label="Sand", value=f"{soil_lookup.get('sand', 0):.2f} %")

        with soil_col3:
            st.metric(label="Silt", value=f"{soil_lookup.get('silt', 0):.2f} %")

        with soil_col4:
            st.metric(label="Clay", value=f"{soil_lookup.get('clay', 0):.2f} %")

        soil_col5, soil_col6, soil_col7, soil_col8 = st.columns(4)

        with soil_col5:
            st.metric(label="Organic carbon", value=f"{soil_lookup.get('soc', 0):.2f} g/kg")

        with soil_col6:
            st.metric(label="Bulk density", value=f"{soil_lookup.get('bdod', 0):.2f} g/cm³")

        with soil_col7:
            st.metric(label="CEC", value=f"{soil_lookup.get('cec', 0):.2f} cmol(c)/kg")

        with soil_col8:
            soil_factor = latest.get("soil_irrigation_factor", 1.0)
            st.metric(label="Soil irrigation factor", value=f"{soil_factor:.2f}", delta=soil_factor_label(soil_factor))

        if has_soil_adjusted_irrigation:
            st.metric(
                label="Soil-adjusted irrigation risk",
                value=risk_color(latest["soil_adjusted_irrigation_risk_level"]),
                delta=f"{latest['soil_adjusted_irrigation_risk_score']:.2f}"
            )

        sand = soil_lookup.get("sand", 0)
        clay = soil_lookup.get("clay", 0)
        ph = soil_lookup.get("phh2o", 0)
        soc = soil_lookup.get("soc", 0)
        soil_factor = latest.get("soil_irrigation_factor", 1.0)

        st.write("### Soil Interpretation")

        soil_notes = []

        if clay >= 35:
            soil_notes.append("Clay content is high, so the soil may hold water better than sandy soil but may drain more slowly.")
        elif clay >= 20:
            soil_notes.append("Clay content is moderate, giving the soil reasonable water-holding capacity.")
        else:
            soil_notes.append("Clay content is low, so the soil may lose water faster and irrigation risk can increase quickly.")

        if sand >= 50:
            soil_notes.append("Sand content is high, which may improve drainage but reduce water retention.")
        elif sand >= 30:
            soil_notes.append("Sand content is moderate, supporting drainage while still allowing some water retention.")
        else:
            soil_notes.append("Sand content is low, so drainage may be slower.")

        if 6.0 <= ph <= 7.5:
            soil_notes.append("Soil pH is near the generally suitable range for mango cultivation.")
        elif ph < 6.0:
            soil_notes.append("Soil pH is acidic and may require soil management depending on crop response.")
        else:
            soil_notes.append("Soil pH is alkaline and may affect nutrient availability.")

        if soc >= 15:
            soil_notes.append("Organic carbon is relatively good and can support soil structure and water retention.")
        elif soc >= 8:
            soil_notes.append("Organic carbon is moderate; compost, mulch, or organic amendments may improve soil health.")
        else:
            soil_notes.append("Organic carbon is low, so improving organic matter may help water retention and soil health.")

        if soil_factor < 0.95:
            soil_notes.append(f"The soil irrigation adjustment factor is {soil_factor:.2f}, meaning this soil reduces estimated irrigation risk because of better water-retention behavior.")
        elif soil_factor > 1.05:
            soil_notes.append(f"The soil irrigation adjustment factor is {soil_factor:.2f}, meaning this soil increases estimated irrigation risk because water may drain or deplete faster.")
        else:
            soil_notes.append(f"The soil irrigation adjustment factor is {soil_factor:.2f}, meaning soil has a mostly neutral effect on irrigation risk.")

        for note in soil_notes:
            st.write(f"- {note}")

        soil_summary_display = topsoil_summary.copy()
        soil_summary_display["average_0_30cm"] = soil_summary_display["average_0_30cm"].round(2)

        with st.expander("SoilGrids 0–30 cm summary table", expanded=False):
            st.dataframe(soil_summary_display, use_container_width=True)


# =======================================================================
# PAGE: Vegetation Health
# =======================================================================

elif page == "Vegetation Health":
    st.title("Vegetation Health (Sentinel-2)")

    st.caption(
        "Satellite-derived vegetation/water indices from Sentinel-2 imagery, aggregated to one "
        "row per day. This is a separate signal from the weather/soil risk pages above — it is "
        "not yet merged into the irrigation/heat/disease risk scores."
    )

    if vegetation_df is None or vegetation_df.empty:
        st.warning("Sentinel-2 daily vegetation file not found or could not be loaded.")
        st.info("Please run: python src/remote_sensing/aggregate_sentinel2_timeseries.py")
        st.info(
            "(That script itself needs the time series file from "
            "`python src/remote_sensing/build_sentinel2_index_timeseries.py`, which in turn needs "
            "Earth Engine set up via `python src/remote_sensing/gee_setup.py`.)"
        )
    else:
        veg_latest = vegetation_df.iloc[-1]

        st.write("### What these indices mean")
        index_explain_col1, index_explain_col2, index_explain_col3, index_explain_col4 = st.columns(4)
        with index_explain_col1:
            st.caption("**NDVI** — vegetation greenness")
        with index_explain_col2:
            st.caption("**NDWI** — water / surface water signal")
        with index_explain_col3:
            st.caption("**NDMI** — vegetation moisture")
        with index_explain_col4:
            st.caption("**NDRE** — chlorophyll / canopy stress signal")

        st.divider()

        st.subheader("Latest Sentinel-2 Reading")

        veg_metric_col1, veg_metric_col2, veg_metric_col3, veg_metric_col4, veg_metric_col5, veg_metric_col6 = st.columns(6)

        with veg_metric_col1:
            st.metric(label="Latest date", value=veg_latest["date"].strftime("%Y-%m-%d"))

        with veg_metric_col2:
            st.metric(label="NDVI", value=f"{veg_latest['ndvi_mean']:.3f}")

        with veg_metric_col3:
            st.metric(label="NDMI", value=f"{veg_latest['ndmi_mean']:.3f}")

        with veg_metric_col4:
            st.metric(label="NDRE", value=f"{veg_latest['ndre_mean']:.3f}")

        with veg_metric_col5:
            st.metric(label="Cloud cover", value=f"{veg_latest['cloud_percentage']:.1f}%")

        with veg_metric_col6:
            st.metric(label="Scenes that day", value=int(veg_latest["scene_count"]))

        st.write("### Interpretation")

        interp_col1, interp_col2, interp_col3 = st.columns(3)

        with interp_col1:
            st.info(f"**NDVI level:** {veg_latest['ndvi_level']}")

        with interp_col2:
            st.info(f"**Moisture level:** {veg_latest['moisture_level']}")

        with interp_col3:
            st.info(f"**Canopy stress level:** {veg_latest['canopy_stress_level']}")

        st.divider()

        st.subheader("Vegetation Index Trends")

        ndvi_fig = px.line(
            vegetation_df, x="date", y="ndvi_mean",
            title="NDVI Over Time (vegetation greenness)",
            labels={"date": "Date", "ndvi_mean": "NDVI"},
        )
        st.plotly_chart(ndvi_fig, use_container_width=True)

        ndmi_fig = px.line(
            vegetation_df, x="date", y="ndmi_mean",
            title="NDMI Over Time (vegetation moisture)",
            labels={"date": "Date", "ndmi_mean": "NDMI"},
        )
        st.plotly_chart(ndmi_fig, use_container_width=True)

        ndre_fig = px.line(
            vegetation_df, x="date", y="ndre_mean",
            title="NDRE Over Time (chlorophyll / canopy stress signal)",
            labels={"date": "Date", "ndre_mean": "NDRE"},
        )
        st.plotly_chart(ndre_fig, use_container_width=True)

        ndwi_fig = px.line(
            vegetation_df, x="date", y="ndwi_mean",
            title="NDWI Over Time (surface water signal)",
            labels={"date": "Date", "ndwi_mean": "NDWI"},
        )
        st.plotly_chart(ndwi_fig, use_container_width=True)

        st.write("### Combined Index View")
        combined_fig = px.line(
            vegetation_df, x="date",
            y=["ndvi_mean", "ndwi_mean", "ndmi_mean", "ndre_mean"],
            title="NDVI, NDWI, NDMI, and NDRE Over Time",
            labels={"date": "Date", "value": "Index value", "variable": "Index"},
        )
        st.plotly_chart(combined_fig, use_container_width=True)

        st.divider()

        st.subheader("Raw Tables")

        with st.expander("Daily Sentinel-2 vegetation index table", expanded=False):
            daily_preview = vegetation_df.copy()
            daily_preview["date"] = daily_preview["date"].dt.strftime("%Y-%m-%d")
            numeric_columns = daily_preview.select_dtypes(include="number").columns
            daily_preview[numeric_columns] = daily_preview[numeric_columns].round(3)
            st.dataframe(daily_preview, use_container_width=True)

        if vegetation_timeseries_df is not None and not vegetation_timeseries_df.empty:
            with st.expander("Image-level Sentinel-2 table (one row per scene)", expanded=False):
                image_preview = vegetation_timeseries_df.copy()
                image_preview["date"] = image_preview["date"].dt.strftime("%Y-%m-%d")
                numeric_columns = image_preview.select_dtypes(include="number").columns
                image_preview[numeric_columns] = image_preview[numeric_columns].round(3)
                st.dataframe(image_preview, use_container_width=True)


# =======================================================================
# PAGE: Combined Intelligence
# =======================================================================

elif page == "Combined Intelligence":
    st.title("Combined Intelligence")

    if combined_feature_df is None or combined_feature_df.empty:
        st.warning("Combined feature table file not found or could not be loaded.")
        st.info("Please run: python src/features/build_feature_table.py")
        st.info(
            "(That script needs the historical risk CSV, the daily Sentinel-2 vegetation CSV, "
            "and the SoilGrids CSV to already exist.)"
        )
    else:
        st.caption(
            "This page combines historical weather risk, static soil intelligence, and "
            "nearest-previous Sentinel-2 vegetation observations. It does not use future "
            "satellite observations — every row only uses vegetation data that was actually "
            "available on or before that date."
        )

        combined_latest = combined_feature_df.iloc[-1]

        st.subheader("Latest Combined Status")

        combined_metric_col1, combined_metric_col2, combined_metric_col3, combined_metric_col4 = st.columns(4)

        with combined_metric_col1:
            st.metric(label="Latest date", value=combined_latest["date"].strftime("%Y-%m-%d"))

        with combined_metric_col2:
            st.metric(label="Irrigation risk", value=risk_color(combined_latest["irrigation_risk_level"]))

        with combined_metric_col3:
            st.metric(label="Heat stress risk", value=risk_color(combined_latest["heat_stress_risk_level"]))

        with combined_metric_col4:
            st.metric(label="Disease risk", value=risk_color(combined_latest["disease_risk_level"]))

        combined_metric_col5, combined_metric_col6, combined_metric_col7, combined_metric_col8 = st.columns(4)

        with combined_metric_col5:
            ndvi_value = combined_latest["ndvi_mean"]
            st.metric(label="Latest NDVI", value=f"{ndvi_value:.3f}" if pd.notna(ndvi_value) else "N/A")

        with combined_metric_col6:
            ndmi_value = combined_latest["ndmi_mean"]
            st.metric(label="Latest NDMI", value=f"{ndmi_value:.3f}" if pd.notna(ndmi_value) else "N/A")

        with combined_metric_col7:
            st.metric(label="Vegetation freshness", value=combined_latest["vegetation_data_freshness"])

        with combined_metric_col8:
            st.metric(label="Soil irrigation factor", value=f"{combined_latest['soil_irrigation_factor']:.2f}")

        st.divider()

        st.subheader("Filters")

        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            combined_min_date = combined_feature_df["date"].min().date()
            combined_max_date = combined_feature_df["date"].max().date()

            combined_selected_range = st.date_input(
                "Date range",
                value=(combined_min_date, combined_max_date),
                min_value=combined_min_date,
                max_value=combined_max_date,
                key="combined_intelligence_date_range",
            )

        with filter_col2:
            freshness_options = ["Fresh", "Moderate", "Stale", "Missing"]
            selected_freshness = st.multiselect(
                "Vegetation freshness",
                options=freshness_options,
                default=freshness_options,
                key="combined_intelligence_freshness_filter",
            )

        if isinstance(combined_selected_range, tuple) and len(combined_selected_range) == 2:
            combined_start_date, combined_end_date = combined_selected_range
            filtered_combined_df = combined_feature_df[
                (combined_feature_df["date"].dt.date >= combined_start_date)
                & (combined_feature_df["date"].dt.date <= combined_end_date)
            ]
        else:
            filtered_combined_df = combined_feature_df.copy()

        if selected_freshness:
            filtered_combined_df = filtered_combined_df[
                filtered_combined_df["vegetation_data_freshness"].isin(selected_freshness)
            ]

        if filtered_combined_df.empty:
            st.warning("No rows match the selected date range and freshness filters.")
        else:
            st.divider()

            st.subheader("Risk Trends")

            irrigation_fig = px.line(
                filtered_combined_df, x="date", y="irrigation_risk_score",
                title="Irrigation Risk Score Over Time",
                labels={"date": "Date", "irrigation_risk_score": "Irrigation risk score"},
            )
            st.plotly_chart(irrigation_fig, use_container_width=True)

            disease_fig = px.line(
                filtered_combined_df, x="date", y="disease_risk_score",
                title="Disease Risk Score Over Time",
                labels={"date": "Date", "disease_risk_score": "Disease risk score"},
            )
            st.plotly_chart(disease_fig, use_container_width=True)

            st.subheader("Vegetation Trends")

            ndvi_combined_fig = px.line(
                filtered_combined_df, x="date", y="ndvi_mean",
                title="NDVI Over Time (matched Sentinel-2 observation)",
                labels={"date": "Date", "ndvi_mean": "NDVI"},
            )
            st.plotly_chart(ndvi_combined_fig, use_container_width=True)

            ndmi_combined_fig = px.line(
                filtered_combined_df, x="date", y="ndmi_mean",
                title="NDMI Over Time (matched Sentinel-2 observation)",
                labels={"date": "Date", "ndmi_mean": "NDMI"},
            )
            st.plotly_chart(ndmi_combined_fig, use_container_width=True)

            st.subheader("Irrigation Risk vs. NDVI")
            st.caption(
                "Irrigation risk score (left axis) and NDVI (right axis) plotted together, "
                "since they use different scales."
            )

            dual_axis_fig = make_subplots(specs=[[{"secondary_y": True}]])
            dual_axis_fig.add_trace(
                go.Scatter(
                    x=filtered_combined_df["date"], y=filtered_combined_df["irrigation_risk_score"],
                    name="Irrigation risk score", mode="lines",
                ),
                secondary_y=False,
            )
            dual_axis_fig.add_trace(
                go.Scatter(
                    x=filtered_combined_df["date"], y=filtered_combined_df["ndvi_mean"],
                    name="NDVI", mode="lines",
                ),
                secondary_y=True,
            )
            dual_axis_fig.update_layout(title="Irrigation Risk Score and NDVI Over Time")
            dual_axis_fig.update_xaxes(title_text="Date")
            dual_axis_fig.update_yaxes(title_text="Irrigation risk score", secondary_y=False)
            dual_axis_fig.update_yaxes(title_text="NDVI", secondary_y=True)
            st.plotly_chart(dual_axis_fig, use_container_width=True)

            st.subheader("Vegetation Data Freshness")

            freshness_counts_df = (
                filtered_combined_df["vegetation_data_freshness"]
                .value_counts()
                .reindex(freshness_options, fill_value=0)
                .rename_axis("freshness")
                .reset_index(name="days")
            )
            freshness_fig = px.bar(
                freshness_counts_df, x="freshness", y="days",
                title="Vegetation Data Freshness (days in selected range)",
                labels={"freshness": "Freshness", "days": "Number of days"},
            )
            st.plotly_chart(freshness_fig, use_container_width=True)

        st.divider()

        st.subheader("Interpretation")
        st.caption("Based on the latest combined row, not the filtered selection above.")

        interpretation_notes = []

        if (
            combined_latest["irrigation_risk_level"] == "High"
            and combined_latest["moisture_level"] == "Dry vegetation / moisture stress"
        ):
            interpretation_notes.append(
                ("warning", "Possible water stress: irrigation risk is high and the matched "
                            "Sentinel-2 observation shows dry vegetation / moisture stress (low NDMI).")
            )

        if combined_latest["disease_risk_level"] == "High" and (
            combined_latest["relative_humidity_percent"] >= 75
            or combined_latest["rainfall_3day_mm"] >= 20
        ):
            interpretation_notes.append(
                ("warning", "Disease-friendly conditions: disease risk is high alongside high "
                            "humidity and/or recent rainfall.")
            )

        if combined_latest["ndvi_level"] == "Low vegetation greenness" and (
            combined_latest["irrigation_risk_level"] == "High"
            or combined_latest["heat_stress_risk_level"] == "High"
            or combined_latest["disease_risk_level"] == "High"
        ):
            interpretation_notes.append(
                ("warning", "Possible combined stress: NDVI shows low vegetation greenness while "
                            "at least one weather risk score is high.")
            )

        if combined_latest["vegetation_data_freshness"] in ("Stale", "Missing"):
            interpretation_notes.append(
                ("info", f"Vegetation data freshness is '{combined_latest['vegetation_data_freshness']}' "
                         "for the latest date — the matched Sentinel-2 observation may be outdated or "
                         "may not exist yet, so vegetation-based interpretation should be treated with caution.")
            )

        if not interpretation_notes:
            st.info("No combined-stress conditions flagged for the latest date based on the rules above.")
        else:
            for level, note in interpretation_notes:
                if level == "warning":
                    st.warning(note)
                else:
                    st.info(note)

        st.divider()

        st.subheader("Raw Combined Feature Table")

        with st.expander("Combined feature table (filtered by the selections above)", expanded=False):
            combined_preview = filtered_combined_df.copy()
            combined_preview["date"] = combined_preview["date"].dt.strftime("%Y-%m-%d")
            if "sentinel2_date" in combined_preview.columns:
                combined_preview["sentinel2_date"] = combined_preview["sentinel2_date"].dt.strftime("%Y-%m-%d")
            numeric_columns = combined_preview.select_dtypes(include="number").columns
            combined_preview[numeric_columns] = combined_preview[numeric_columns].round(3)
            st.dataframe(combined_preview, use_container_width=True)


# =======================================================================
# PAGE: Water Balance (FAO-56, standalone)
# =======================================================================

elif page == "Water Balance":
    st.title("Water Balance (FAO-56)")

    st.warning(
        "This FAO-56 page is a simplified rainfed prototype. It does not yet include actual "
        "irrigation events, runoff, deep percolation, phenology-aware crop coefficients, or "
        "field validation."
    )

    if fao56_water_balance_df is None or fao56_water_balance_df.empty:
        st.warning("FAO-56 water balance file not found or could not be loaded.")
        st.info("Please run: python src/water_balance/fao56_water_balance.py")
        st.info(
            "(That script needs the combined feature table to already exist — "
            "see `python src/features/build_feature_table.py`.)"
        )
    else:
        st.caption(
            "Daily reference evapotranspiration (ET0), estimated crop water use (ETc), and a "
            "root-zone soil-water depletion balance computed with the FAO-56 Penman-Monteith "
            "method (Allen et al., 1998). This is a separate, standalone signal — it is not yet "
            "merged into the irrigation/heat/disease risk scores or the dashboard's other pages."
        )

        fao56_latest = fao56_water_balance_df.iloc[-1]

        st.subheader("Latest Water Balance Status")

        fao56_col1, fao56_col2, fao56_col3, fao56_col4 = st.columns(4)

        with fao56_col1:
            st.metric(label="Latest date", value=fao56_latest["date"].strftime("%Y-%m-%d"))

        with fao56_col2:
            st.metric(label="Latest ET0", value=f"{fao56_latest['et0_mm']:.2f} mm/day")

        with fao56_col3:
            st.metric(label="Latest ETc", value=f"{fao56_latest['etc_mm']:.2f} mm/day")

        with fao56_col4:
            st.metric(label="Latest root-zone depletion", value=f"{fao56_latest['root_zone_depletion_mm']:.1f} mm")

        fao56_col5, fao56_col6, fao56_col7, fao56_col8 = st.columns(4)

        with fao56_col5:
            st.metric(
                label="Latest Ks (water-stress coefficient)",
                value=f"{fao56_latest['water_stress_coefficient_ks']:.2f}",
            )

        with fao56_col6:
            st.metric(label="Latest water-stress level", value=risk_color(fao56_latest["water_stress_level"]))

        with fao56_col7:
            st.metric(label="TAW (total available water)", value=f"{fao56_latest['taw_mm']:.1f} mm")

        with fao56_col8:
            st.metric(label="RAW (readily available water)", value=f"{fao56_latest['raw_mm']:.1f} mm")

        st.divider()

        st.subheader("Water Balance Trends")

        et_fig = px.line(
            fao56_water_balance_df, x="date", y=["et0_mm", "etc_mm"],
            title="ET0 and ETc Over Time",
            labels={"date": "Date", "value": "mm/day", "variable": "Metric"},
        )
        st.plotly_chart(et_fig, use_container_width=True)

        st.caption(
            "Rainfall and ETc plotted together (different scales), since rainfall events and "
            "crop water use both drive the daily depletion balance."
        )
        rain_etc_fig = make_subplots(specs=[[{"secondary_y": True}]])
        rain_etc_fig.add_trace(
            go.Bar(
                x=fao56_water_balance_df["date"], y=fao56_water_balance_df["rainfall_mm"],
                name="Rainfall (mm)",
            ),
            secondary_y=False,
        )
        rain_etc_fig.add_trace(
            go.Scatter(
                x=fao56_water_balance_df["date"], y=fao56_water_balance_df["etc_mm"],
                name="ETc (mm/day)", mode="lines",
            ),
            secondary_y=True,
        )
        rain_etc_fig.update_layout(title="Rainfall and ETc Over Time")
        rain_etc_fig.update_xaxes(title_text="Date")
        rain_etc_fig.update_yaxes(title_text="Rainfall (mm)", secondary_y=False)
        rain_etc_fig.update_yaxes(title_text="ETc (mm/day)", secondary_y=True)
        st.plotly_chart(rain_etc_fig, use_container_width=True)

        depletion_fig = px.line(
            fao56_water_balance_df, x="date", y="root_zone_depletion_mm",
            title="Root-Zone Depletion Over Time",
            labels={"date": "Date", "root_zone_depletion_mm": "Depletion (mm)"},
        )
        depletion_fig.add_hline(
            y=fao56_latest["raw_mm"], line_dash="dash", line_color="orange",
            annotation_text="RAW (stress begins)",
        )
        depletion_fig.add_hline(
            y=fao56_latest["taw_mm"], line_dash="dash", line_color="red",
            annotation_text="TAW (all available water gone)",
        )
        st.plotly_chart(depletion_fig, use_container_width=True)

        ks_fig = px.line(
            fao56_water_balance_df, x="date", y="water_stress_coefficient_ks",
            title="Ks Water-Stress Coefficient Over Time",
            labels={"date": "Date", "water_stress_coefficient_ks": "Ks"},
        )
        st.plotly_chart(ks_fig, use_container_width=True)

        stress_level_counts_df = (
            fao56_water_balance_df["water_stress_level"]
            .value_counts()
            .reindex(["Low", "Medium", "High"], fill_value=0)
            .rename_axis("water_stress_level")
            .reset_index(name="days")
        )
        stress_level_fig = px.bar(
            stress_level_counts_df, x="water_stress_level", y="days",
            title="Water-Stress Level Counts (full date range)",
            labels={"water_stress_level": "Water-stress level", "days": "Number of days"},
        )
        st.plotly_chart(stress_level_fig, use_container_width=True)

        st.divider()

        st.subheader("Interpretation")

        st.write("- **ET0** is atmospheric evaporative demand — how much water the air/sun/wind could pull from a reference surface that day.")
        st.write("- **ETc** is estimated crop water use, derived from ET0 and a crop coefficient (Kc).")
        st.write("- **Depletion** is how much water has been removed from the root zone since it was last at field capacity.")
        st.write("- **Ks** is the water-stress coefficient — 1.0 means no stress, and lower values mean stronger water stress.")
        st.write("- **TAW** is total available water — the maximum water the root zone can hold and still release to the crop.")
        st.write("- **RAW** is readily available water — the portion of TAW that can be used before water stress (Ks < 1) begins.")

        st.divider()

        st.subheader("Raw FAO-56 Water Balance Table")

        with st.expander("FAO-56 water balance table (full)", expanded=False):
            fao56_preview = fao56_water_balance_df.copy()
            fao56_preview["date"] = fao56_preview["date"].dt.strftime("%Y-%m-%d")
            numeric_columns = fao56_preview.select_dtypes(include="number").columns
            fao56_preview[numeric_columns] = fao56_preview[numeric_columns].round(3)
            st.dataframe(fao56_preview, use_container_width=True)


# =======================================================================
# PAGE: Mango Phenology (standalone calendar)
# =======================================================================

elif page == "Mango Phenology":
    st.title("Mango Phenology Calendar")

    st.warning(
        "This is a simplified, regional (Andhra Pradesh / South India) mango phenology "
        "calendar. It is not cultivar-specific yet, it is not field-calibrated yet (no actual "
        "bloom/fruit-set/harvest dates from this orchard have been used), and every date is "
        "assigned a stage purely from the calendar day-of-year, regardless of that year's "
        "actual weather. It will later be used to make the FAO-56 water balance's crop "
        "coefficient (Kc) and the irrigation/heat/disease risk thresholds stage-aware — that "
        "wiring has not happened yet."
    )

    if phenology_df is None or phenology_df.empty:
        st.warning("Mango phenology calendar file not found or could not be loaded.")
        st.info("Please run: python src/phenology/mango_phenology_calendar.py")
        st.info(
            "(That script needs the combined feature table to already exist — "
            "see `python src/features/build_feature_table.py` — only its date range is used.)"
        )
    else:
        st.caption(
            "One growth stage is assigned to every calendar date using fixed, documented "
            "month/day boundaries (see the script's module docstring for the exact cutover "
            "rules). This is a separate, standalone signal — it is not yet merged into the "
            "FAO-56 water balance or the irrigation/heat/disease risk scores."
        )

        phenology_latest = phenology_df.iloc[-1]

        st.subheader("Current Mango Stage")

        phen_col1, phen_col2, phen_col3, phen_col4, phen_col5 = st.columns(5)

        with phen_col1:
            st.metric(label="Latest date", value=phenology_latest["date"].strftime("%Y-%m-%d"))

        with phen_col2:
            st.metric(label="Current mango stage", value=phenology_latest["mango_stage"])

        with phen_col3:
            st.metric(label="Water sensitivity", value=phenology_latest["water_sensitivity"])

        with phen_col4:
            st.metric(label="Heat sensitivity", value=phenology_latest["heat_sensitivity"])

        with phen_col5:
            st.metric(label="Disease sensitivity", value=phenology_latest["disease_sensitivity"])

        st.info(f"**Stage description:** {phenology_latest['stage_description']}")
        st.info(f"**Recommended monitoring focus:** {phenology_latest['recommended_monitoring_focus']}")

        st.divider()

        st.subheader("Stage Counts (full date range)")

        stage_order = [
            "Flowering",
            "Fruit set",
            "Fruit development",
            "Maturity / harvest",
            "Rest / vegetative phase",
            "Flower induction / pre-flowering",
        ]

        stage_counts_df = (
            phenology_df["mango_stage"]
            .value_counts()
            .reindex(stage_order, fill_value=0)
            .rename_axis("mango_stage")
            .reset_index(name="days")
        )
        stage_count_fig = px.bar(
            stage_counts_df, x="mango_stage", y="days",
            title="Number of Days per Mango Stage (full historical date range)",
            labels={"mango_stage": "Mango stage", "days": "Number of days"},
        )
        st.plotly_chart(stage_count_fig, use_container_width=True)

        st.subheader("Mango Stage Timeline")
        st.caption(
            "Each stage is shown as a numbered band over time so growth-stage transitions are "
            "visible at a glance."
        )

        stage_code_map = {name: i for i, name in enumerate(stage_order)}
        timeline_df = phenology_df.copy()
        timeline_df["stage_code"] = timeline_df["mango_stage"].map(stage_code_map)

        timeline_fig = px.scatter(
            timeline_df, x="date", y="mango_stage",
            title="Mango Growth Stage Over Time",
            labels={"date": "Date", "mango_stage": "Mango stage"},
            category_orders={"mango_stage": stage_order},
        )
        timeline_fig.update_traces(marker=dict(size=4))
        st.plotly_chart(timeline_fig, use_container_width=True)

        st.subheader("Monthly Stage Distribution")

        monthly_stage_df = phenology_df.copy()
        monthly_stage_df["month_name"] = monthly_stage_df["date"].dt.strftime("%b")
        monthly_stage_df["month_num"] = monthly_stage_df["date"].dt.month

        monthly_stage_table = (
            monthly_stage_df.groupby(["month_num", "month_name", "mango_stage"])
            .size()
            .reset_index(name="days")
            .sort_values(["month_num"])
        )

        monthly_stage_pivot = monthly_stage_table.pivot_table(
            index=["month_num", "month_name"], columns="mango_stage", values="days", fill_value=0
        ).reset_index().sort_values("month_num").drop(columns="month_num").rename(columns={"month_name": "Month"})

        with st.expander("Monthly stage distribution table", expanded=False):
            st.dataframe(monthly_stage_pivot, use_container_width=True)

        monthly_stage_fig = px.bar(
            monthly_stage_table, x="month_name", y="days", color="mango_stage",
            title="Mango Stage Distribution by Month (stacked, full historical range)",
            labels={"month_name": "Month", "days": "Number of days", "mango_stage": "Mango stage"},
            category_orders={
                "month_name": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                "mango_stage": stage_order,
            },
        )
        st.plotly_chart(monthly_stage_fig, use_container_width=True)

        st.divider()

        st.subheader("About This Calendar")
        st.write("- This is a **simplified regional phenology calendar** for mango in Andhra Pradesh / South India, not a field-measured calendar for this specific orchard.")
        st.write("- It is **not yet calibrated to a specific cultivar** (e.g. Banganapalli, Totapuri, Alphonso/Benishan bloom and harvest timing can differ).")
        st.write("- It **does not yet use field observations** — no actual bloom, fruit-set, or harvest dates from this orchard have been recorded or used.")
        st.write("- It will **later** be used to make the FAO-56 water balance's crop coefficient (Kc) and the irrigation/heat/disease risk thresholds stage-aware — that wiring has not happened yet.")

        st.divider()

        st.subheader("Raw Mango Phenology Calendar Table")

        with st.expander("Mango phenology calendar table (full)", expanded=False):
            phenology_preview = phenology_df.copy()
            phenology_preview["date"] = phenology_preview["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(phenology_preview, use_container_width=True)


# =======================================================================
# PAGE: Phenology Water Balance (phenology-aware FAO-56, standalone)
# =======================================================================

elif page == "Phenology Water Balance":
    st.title("Phenology Water Balance (Phenology-Aware FAO-56)")

    st.warning(
        "This is a simplified phenology-aware prototype. Kc values are assumed, not "
        "cultivar-specific, not field-calibrated, and irrigation events are not yet included."
    )

    if fao56_phenology_water_balance_df is None or fao56_phenology_water_balance_df.empty:
        st.warning("Phenology-aware FAO-56 water balance file not found or could not be loaded.")
        st.info("Please run: python src/water_balance/fao56_phenology_water_balance.py")
        st.info(
            "(That script needs the combined feature table and the mango phenology calendar "
            "to already exist — see `python src/features/build_feature_table.py` and "
            "`python src/phenology/mango_phenology_calendar.py`.)"
        )
    else:
        st.caption(
            "Same daily ET0 / TAW / RAW / root-zone-depletion logic as the constant-Kc FAO-56 "
            "page, but the crop coefficient (Kc) now changes by mango growth stage instead of "
            "staying fixed at 0.75. This is a separate, standalone signal — it is not yet "
            "merged into the irrigation/heat/disease risk scores, the constant-Kc Water Balance "
            "page, or `main.py`."
        )

        phen_wb_latest = fao56_phenology_water_balance_df.iloc[-1]

        st.subheader("Latest Phenology-Aware Water Balance Status")

        pwb_col1, pwb_col2, pwb_col3, pwb_col4 = st.columns(4)

        with pwb_col1:
            st.metric(label="Latest date", value=phen_wb_latest["date"].strftime("%Y-%m-%d"))

        with pwb_col2:
            st.metric(label="Current mango stage", value=phen_wb_latest["mango_stage"])

        with pwb_col3:
            st.metric(label="Latest Kc", value=f"{phen_wb_latest['kc']:.2f}")

        with pwb_col4:
            st.metric(label="Latest ET0", value=f"{phen_wb_latest['et0_mm_day']:.2f} mm/day")

        pwb_col5, pwb_col6, pwb_col7, pwb_col8 = st.columns(4)

        with pwb_col5:
            st.metric(label="Latest ETc", value=f"{phen_wb_latest['etc_mm_day']:.2f} mm/day")

        with pwb_col6:
            st.metric(
                label="Latest root-zone depletion",
                value=f"{phen_wb_latest['root_zone_depletion_mm']:.1f} mm",
            )

        with pwb_col7:
            st.metric(label="Latest Ks", value=f"{phen_wb_latest['ks']:.2f}")

        with pwb_col8:
            st.metric(label="Latest water-stress level", value=risk_color(phen_wb_latest["water_stress_level"]))

        st.divider()

        st.subheader("Phenology-Aware Water Balance Trends")

        kc_fig = px.line(
            fao56_phenology_water_balance_df, x="date", y="kc",
            title="Crop Coefficient (Kc) Over Time",
            labels={"date": "Date", "kc": "Kc"},
        )
        st.plotly_chart(kc_fig, use_container_width=True)

        phen_et_fig = px.line(
            fao56_phenology_water_balance_df, x="date", y=["et0_mm_day", "etc_mm_day"],
            title="ET0 and ETc Over Time (Phenology-Aware)",
            labels={"date": "Date", "value": "mm/day", "variable": "Metric"},
        )
        st.plotly_chart(phen_et_fig, use_container_width=True)

        phen_depletion_fig = px.line(
            fao56_phenology_water_balance_df, x="date", y="root_zone_depletion_mm",
            title="Root-Zone Depletion Over Time (Phenology-Aware)",
            labels={"date": "Date", "root_zone_depletion_mm": "Depletion (mm)"},
        )
        phen_depletion_fig.add_hline(
            y=phen_wb_latest["raw_mm"], line_dash="dash", line_color="orange",
            annotation_text="RAW (stress begins)",
        )
        phen_depletion_fig.add_hline(
            y=phen_wb_latest["taw_mm"], line_dash="dash", line_color="red",
            annotation_text="TAW (all available water gone)",
        )
        st.plotly_chart(phen_depletion_fig, use_container_width=True)

        phen_ks_fig = px.line(
            fao56_phenology_water_balance_df, x="date", y="ks",
            title="Ks Water-Stress Coefficient Over Time (Phenology-Aware)",
            labels={"date": "Date", "ks": "Ks"},
        )
        st.plotly_chart(phen_ks_fig, use_container_width=True)

        phen_stress_level_counts_df = (
            fao56_phenology_water_balance_df["water_stress_level"]
            .value_counts()
            .reindex(["Low", "Medium", "High"], fill_value=0)
            .rename_axis("water_stress_level")
            .reset_index(name="days")
        )
        phen_stress_level_fig = px.bar(
            phen_stress_level_counts_df, x="water_stress_level", y="days",
            title="Water-Stress Level Counts (full date range, phenology-aware)",
            labels={"water_stress_level": "Water-stress level", "days": "Number of days"},
        )
        st.plotly_chart(phen_stress_level_fig, use_container_width=True)

        phen_wb_stage_order = [
            "Flowering",
            "Fruit set",
            "Fruit development",
            "Maturity / harvest",
            "Rest / vegetative phase",
            "Flower induction / pre-flowering",
        ]
        stages_present = [
            s for s in phen_wb_stage_order
            if s in fao56_phenology_water_balance_df["mango_stage"].unique()
        ]

        stress_by_stage_df = (
            fao56_phenology_water_balance_df
            .groupby(["mango_stage", "water_stress_level"])
            .size()
            .reset_index(name="days")
        )
        stress_by_stage_fig = px.bar(
            stress_by_stage_df, x="mango_stage", y="days", color="water_stress_level",
            title="Water-Stress Level by Mango Stage",
            labels={"mango_stage": "Mango stage", "days": "Number of days", "water_stress_level": "Water-stress level"},
            category_orders={"mango_stage": stages_present, "water_stress_level": ["Low", "Medium", "High"]},
        )
        st.plotly_chart(stress_by_stage_fig, use_container_width=True)

        etc_by_stage_df = (
            fao56_phenology_water_balance_df
            .groupby("mango_stage")["etc_mm_day"]
            .mean()
            .reindex(stages_present)
            .rename_axis("mango_stage")
            .reset_index(name="avg_etc_mm_day")
        )
        etc_by_stage_fig = px.bar(
            etc_by_stage_df, x="mango_stage", y="avg_etc_mm_day",
            title="Average ETc by Mango Stage",
            labels={"mango_stage": "Mango stage", "avg_etc_mm_day": "Average ETc (mm/day)"},
            category_orders={"mango_stage": stages_present},
        )
        st.plotly_chart(etc_by_stage_fig, use_container_width=True)

        st.divider()

        if fao56_water_balance_df is not None and not fao56_water_balance_df.empty:
            st.subheader("Comparison with Constant-Kc FAO-56 (Prototype Comparison)")
            st.caption(
                "**Prototype comparison only** — both models share the same ET0/TAW/RAW/depletion "
                "logic and only differ in how Kc is assigned (constant 0.75 vs. stage-aware). This "
                "is not a validated benchmark against field data."
            )

            comparison_df = pd.merge(
                fao56_water_balance_df[["date", "etc_mm", "water_stress_level"]].rename(
                    columns={"etc_mm": "etc_mm_constant_kc", "water_stress_level": "water_stress_level_constant_kc"}
                ),
                fao56_phenology_water_balance_df[["date", "etc_mm_day", "water_stress_level"]].rename(
                    columns={"etc_mm_day": "etc_mm_phenology_kc", "water_stress_level": "water_stress_level_phenology_kc"}
                ),
                on="date", how="inner",
            )

            if comparison_df.empty:
                st.info(
                    "No overlapping dates found between the constant-Kc and phenology-aware "
                    "FAO-56 outputs, so a direct comparison can't be shown yet."
                )
            else:
                etc_compare_fig = px.line(
                    comparison_df, x="date", y=["etc_mm_constant_kc", "etc_mm_phenology_kc"],
                    title="ETc: Constant-Kc vs. Phenology-Aware Kc",
                    labels={"date": "Date", "value": "ETc (mm/day)", "variable": "Model"},
                )
                st.plotly_chart(etc_compare_fig, use_container_width=True)

                constant_kc_counts = (
                    comparison_df["water_stress_level_constant_kc"]
                    .value_counts()
                    .reindex(["Low", "Medium", "High"], fill_value=0)
                )
                phenology_kc_counts = (
                    comparison_df["water_stress_level_phenology_kc"]
                    .value_counts()
                    .reindex(["Low", "Medium", "High"], fill_value=0)
                )
                stress_compare_df = pd.DataFrame({
                    "water_stress_level": ["Low", "Medium", "High"],
                    "Constant Kc": constant_kc_counts.values,
                    "Phenology-Aware Kc": phenology_kc_counts.values,
                }).melt(id_vars="water_stress_level", var_name="Model", value_name="days")

                stress_compare_fig = px.bar(
                    stress_compare_df, x="water_stress_level", y="days", color="Model", barmode="group",
                    title="Water-Stress Level Counts: Constant Kc vs. Phenology-Aware Kc",
                    labels={"water_stress_level": "Water-stress level", "days": "Number of days"},
                    category_orders={"water_stress_level": ["Low", "Medium", "High"]},
                )
                st.plotly_chart(stress_compare_fig, use_container_width=True)
        else:
            st.info(
                "Constant-Kc FAO-56 output not found — run "
                "`python src/water_balance/fao56_water_balance.py` to enable the comparison view."
            )

        st.divider()

        st.subheader("Interpretation")

        st.write("- **Kc changes by mango stage** instead of staying fixed — flowering, fruit set, fruit development, maturity/harvest, and rest each get their own assumed value.")
        st.write("- **Higher Kc means higher crop water demand** for the same atmospheric ET0.")
        st.write("- **Fruit development and fruit set usually have higher water sensitivity**, which is reflected in their higher assumed Kc values (0.90 and 0.85).")
        st.write("- **This model is still assumption-based and not field-calibrated** — the Kc-by-stage values are first-pass estimates from general mango/FAO-56 guidance, not measurements from this orchard.")

        st.divider()

        st.subheader("Disclaimer")
        st.info(
            "This is a simplified phenology-aware prototype. Kc values are assumed, not "
            "cultivar-specific, not field-calibrated, and irrigation events are not yet included."
        )

        st.divider()

        st.subheader("Raw Phenology-Aware FAO-56 Water Balance Table")

        with st.expander("Phenology-aware FAO-56 water balance table (full)", expanded=False):
            phen_wb_preview = fao56_phenology_water_balance_df.copy()
            phen_wb_preview["date"] = phen_wb_preview["date"].dt.strftime("%Y-%m-%d")
            numeric_columns = phen_wb_preview.select_dtypes(include="number").columns
            phen_wb_preview[numeric_columns] = phen_wb_preview[numeric_columns].round(3)
            st.dataframe(phen_wb_preview, use_container_width=True)

        if fao56_water_balance_df is not None and not fao56_water_balance_df.empty:
            with st.expander("Constant-Kc FAO-56 water balance table (full, for comparison)", expanded=False):
                const_wb_preview = fao56_water_balance_df.copy()
                const_wb_preview["date"] = const_wb_preview["date"].dt.strftime("%Y-%m-%d")
                numeric_columns = const_wb_preview.select_dtypes(include="number").columns
                const_wb_preview[numeric_columns] = const_wb_preview[numeric_columns].round(3)
                st.dataframe(const_wb_preview, use_container_width=True)


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
