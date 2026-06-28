"""
Column validation utilities for the Sensor-Free Mango Digital Twin.

Each pipeline stage (fetch -> risk engine -> dashboard) expects a specific
set of columns to be present in the DataFrame it receives. Rather than
letting a missing/renamed column blow up later with a confusing pandas
KeyError, these helpers check up front and raise one clear error that says
exactly what is missing and what is present.

Usage:

    from src.utils.validation import validate_historical_weather
    validate_historical_weather(weather_df)
"""

from __future__ import annotations

import pandas as pd

REQUIRED_HISTORICAL_WEATHER_COLUMNS = [
    "date",
    "temperature_avg_c",
    "temperature_max_c",
    "temperature_min_c",
    "relative_humidity_percent",
    "rainfall_mm",
    "solar_radiation_mj_m2",
    "wind_speed_m_s",
]

REQUIRED_FORECAST_WEATHER_COLUMNS = [
    "date",
    "openmeteo_temperature_avg_c",
    "openmeteo_temperature_max_c",
    "openmeteo_temperature_min_c",
    "openmeteo_relative_humidity_percent",
    "openmeteo_precipitation_mm",
    "openmeteo_rain_mm",
    "openmeteo_solar_radiation_mj_m2",
    "openmeteo_wind_speed_max_kmh",
    "openmeteo_et0_mm",
]

REQUIRED_SOIL_COLUMNS = [
    "property",
    "depth",
    "raw_value",
    "converted_value",
    "unit",
]

REQUIRED_RISK_COLUMNS = [
    "date",
    "irrigation_risk_score",
    "irrigation_risk_level",
    "heat_stress_risk_score",
    "heat_stress_risk_level",
    "disease_risk_score",
    "disease_risk_level",
]

REQUIRED_VEGETATION_COLUMNS = [
    "date",
    "cloud_percentage",
    "ndvi_mean",
    "ndwi_mean",
    "ndmi_mean",
    "ndre_mean",
    "scene_count",
    "ndvi_level",
    "moisture_level",
    "canopy_stress_level",
]

REQUIRED_COMBINED_FEATURE_COLUMNS = [
    "date",
    "irrigation_risk_score",
    "irrigation_risk_level",
    "heat_stress_risk_score",
    "heat_stress_risk_level",
    "disease_risk_score",
    "disease_risk_level",
    "relative_humidity_percent",
    "rainfall_3day_mm",
    "rainfall_7day_mm",
    "soil_irrigation_factor",
    "sentinel2_date",
    "ndvi_mean",
    "ndmi_mean",
    "ndvi_level",
    "moisture_level",
    "canopy_stress_level",
    "days_since_sentinel2_observation",
    "vegetation_data_freshness",
]


REQUIRED_FAO56_INPUT_COLUMNS = [
    "date",
    "temperature_avg_c",
    "temperature_max_c",
    "temperature_min_c",
    "relative_humidity_percent",
    "rainfall_mm",
    "solar_radiation_mj_m2",
    "wind_speed_m_s",
    "sand_percent",
    "clay_percent",
    "organic_carbon_g_kg",
]

REQUIRED_FAO56_OUTPUT_COLUMNS = [
    "date",
    "et0_mm",
    "etc_mm",
    "rainfall_mm",
    "root_zone_depletion_mm",
    "taw_mm",
    "raw_mm",
    "water_stress_coefficient_ks",
    "water_stress_level",
]

REQUIRED_PHENOLOGY_OUTPUT_COLUMNS = [
    "date",
    "month",
    "day_of_year",
    "mango_stage",
    "stage_description",
    "water_sensitivity",
    "heat_sensitivity",
    "disease_sensitivity",
    "recommended_monitoring_focus",
]

REQUIRED_FAO56_PHENOLOGY_OUTPUT_COLUMNS = [
    "date",
    "mango_stage",
    "kc",
    "et0_mm_day",
    "etc_mm_day",
    "rainfall_mm",
    "root_zone_depletion_mm",
    "taw_mm",
    "raw_mm",
    "ks",
    "water_stress_score",
    "water_stress_level",
]


class MissingColumnsError(ValueError):
    """Raised when a DataFrame is missing one or more required columns."""


def validate_columns(df: pd.DataFrame, required_columns: list[str], data_name: str) -> None:
    """
    Raise MissingColumnsError with a clear, beginner-friendly message if any
    column in `required_columns` is not present in `df`.
    """
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise MissingColumnsError(
            f"{data_name} is missing required column(s): {missing}.\n"
            f"Columns actually found: {list(df.columns)}.\n"
            "This usually means an earlier pipeline step needs to be "
            "re-run, the wrong file was loaded, or an API response "
            "changed shape."
        )


def validate_historical_weather(df: pd.DataFrame) -> None:
    """Validate a NASA POWER historical weather DataFrame."""
    validate_columns(df, REQUIRED_HISTORICAL_WEATHER_COLUMNS, "NASA POWER historical weather data")


def validate_forecast_weather(df: pd.DataFrame) -> None:
    """Validate an Open-Meteo recent/forecast weather DataFrame."""
    validate_columns(df, REQUIRED_FORECAST_WEATHER_COLUMNS, "Open-Meteo forecast weather data")


def validate_soil_data(df: pd.DataFrame) -> None:
    """Validate a SoilGrids soil-properties DataFrame."""
    validate_columns(df, REQUIRED_SOIL_COLUMNS, "SoilGrids soil data")


def validate_risk_data(df: pd.DataFrame) -> None:
    """Validate a processed (historical or forecast) mango risk DataFrame."""
    validate_columns(df, REQUIRED_RISK_COLUMNS, "Processed mango risk data")


def validate_vegetation_data(df: pd.DataFrame) -> None:
    """Validate a daily Sentinel-2 vegetation index DataFrame."""
    validate_columns(df, REQUIRED_VEGETATION_COLUMNS, "Sentinel-2 daily vegetation index data")


def validate_combined_feature_data(df: pd.DataFrame) -> None:
    """Validate the combined weather + soil + vegetation feature table."""
    validate_columns(df, REQUIRED_COMBINED_FEATURE_COLUMNS, "Combined weather/soil/vegetation feature table")


def validate_fao56_input(df: pd.DataFrame) -> None:
    """Validate that a DataFrame has what the FAO-56 water balance script needs."""
    validate_columns(df, REQUIRED_FAO56_INPUT_COLUMNS, "FAO-56 water balance input data")


def validate_fao56_output(df: pd.DataFrame) -> None:
    """Validate the FAO-56 daily soil-water balance output table."""
    validate_columns(df, REQUIRED_FAO56_OUTPUT_COLUMNS, "FAO-56 soil-water balance output data")


def validate_phenology_output(df: pd.DataFrame) -> None:
    """Validate the mango phenology calendar output table."""
    validate_columns(df, REQUIRED_PHENOLOGY_OUTPUT_COLUMNS, "Mango phenology calendar output data")


def validate_fao56_phenology_output(df: pd.DataFrame) -> None:
    """Validate the phenology-aware FAO-56 soil-water balance output table."""
    validate_columns(df, REQUIRED_FAO56_PHENOLOGY_OUTPUT_COLUMNS, "Phenology-aware FAO-56 water balance output data")
