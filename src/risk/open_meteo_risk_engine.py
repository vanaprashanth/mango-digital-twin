"""
Forecast mango risk engine.

Reads recent + forecast daily weather from Open-Meteo, engineers rolling
rainfall features, and scores irrigation / heat-stress / disease-friendly-
weather risk for the upcoming window. Mirrors the scoring logic in
src/risk/historical_risk_engine.py, with ET0 (provided directly by
Open-Meteo) used as the irrigation-demand signal instead of solar
radiation.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.risk.historical_risk_engine import load_topsoil_summary
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.soil_factor import calculate_soil_irrigation_factor, soil_factor_label
from src.utils.validation import validate_forecast_weather, validate_risk_data

log = get_logger(__name__)


def classify_risk(score: float, config) -> str:
    """Convert a numeric risk score (0-1) into Low / Medium / High."""
    high = config.get_threshold("classification", "high")
    medium = config.get_threshold("classification", "medium")

    if score >= high:
        return "High"
    elif score >= medium:
        return "Medium"
    return "Low"


def calculate_irrigation_risk(row, config) -> float:
    """
    Forecast irrigation risk using Open-Meteo daily weather.

    Logic:
    - Low 7-day rainfall increases irrigation risk.
    - High maximum temperature increases irrigation risk.
    - High ET0 increases irrigation demand.
    """

    score = 0.0
    t = config.risk_thresholds["irrigation"]

    if row["rainfall_7day_mm"] < t["rainfall_7day_low_mm"]:
        score += 0.45
    elif row["rainfall_7day_mm"] < t["rainfall_7day_medium_mm"]:
        score += 0.25

    if row["temperature_max_c"] >= t["temp_max_high_c"]:
        score += 0.30
    elif row["temperature_max_c"] >= t["temp_max_medium_c"]:
        score += 0.15

    if row["et0_mm"] >= t["et0_high_mm"]:
        score += 0.25
    elif row["et0_mm"] >= t["et0_medium_mm"]:
        score += 0.15

    return min(score, 1.0)


def calculate_heat_stress_risk(row, config) -> float:
    """Forecast heat stress risk using maximum and average temperature."""

    score = 0.0
    t = config.risk_thresholds["heat_stress"]

    if row["temperature_max_c"] >= t["temp_max_extreme_c"]:
        score += 0.80
    elif row["temperature_max_c"] >= t["temp_max_high_c"]:
        score += 0.60
    elif row["temperature_max_c"] >= t["temp_max_medium_c"]:
        score += 0.40
    elif row["temperature_max_c"] >= t["temp_max_low_c"]:
        score += 0.20

    if row["temperature_avg_c"] >= t["temp_avg_warm_c"]:
        score += 0.20

    return min(score, 1.0)


def calculate_disease_risk(row, config) -> float:
    """
    Forecast disease-friendly weather risk.

    Logic:
    - High humidity increases fungal disease-favorable conditions.
    - Moderate temperature range supports fungal conditions.
    - Recent rainfall increases wetness risk.
    """

    score = 0.0
    t = config.risk_thresholds["disease"]

    if row["relative_humidity_percent"] >= t["humidity_high_percent"]:
        score += 0.45
    elif row["relative_humidity_percent"] >= t["humidity_medium_percent"]:
        score += 0.30
    elif row["relative_humidity_percent"] >= t["humidity_low_percent"]:
        score += 0.15

    if t["temp_avg_favorable_min_c"] <= row["temperature_avg_c"] <= t["temp_avg_favorable_max_c"]:
        score += 0.30
    elif t["temp_avg_marginal_min_c"] <= row["temperature_avg_c"] < t["temp_avg_favorable_min_c"]:
        score += 0.15

    if row["rainfall_3day_mm"] >= t["rainfall_3day_high_mm"]:
        score += 0.25
    elif row["rainfall_3day_mm"] >= t["rainfall_3day_medium_mm"]:
        score += 0.10

    return min(score, 1.0)


def prepare_open_meteo_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename Open-Meteo columns to match our project naming pattern.
    """

    df = df.copy()

    df = df.rename(
        columns={
            "openmeteo_temperature_avg_c": "temperature_avg_c",
            "openmeteo_temperature_max_c": "temperature_max_c",
            "openmeteo_temperature_min_c": "temperature_min_c",
            "openmeteo_relative_humidity_percent": "relative_humidity_percent",
            "openmeteo_precipitation_mm": "precipitation_mm",
            "openmeteo_rain_mm": "rainfall_mm",
            "openmeteo_solar_radiation_mj_m2": "solar_radiation_mj_m2",
            "openmeteo_wind_speed_max_kmh": "wind_speed_max_kmh",
            "openmeteo_et0_mm": "et0_mm",
        }
    )

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    weather_columns = [
        "temperature_avg_c",
        "temperature_max_c",
        "temperature_min_c",
        "relative_humidity_percent",
        "rainfall_mm",
        "solar_radiation_mj_m2",
        "wind_speed_max_kmh",
        "et0_mm",
    ]

    df[weather_columns] = df[weather_columns].replace(-999, pd.NA)
    df = df.dropna(subset=weather_columns)

    return df


def add_forecast_risk_scores(df: pd.DataFrame, config, soil_lookup: dict[str, float] | None = None) -> pd.DataFrame:
    """
    Add rolling rainfall features, forecast risk scores, and (if soil data
    is available) the soil-adjusted irrigation risk.
    """

    df = prepare_open_meteo_data(df)

    df["rainfall_3day_mm"] = df["rainfall_mm"].rolling(window=3, min_periods=1).sum()
    df["rainfall_7day_mm"] = df["rainfall_mm"].rolling(window=7, min_periods=1).sum()

    df["irrigation_risk_score"] = df.apply(lambda row: calculate_irrigation_risk(row, config), axis=1)
    df["heat_stress_risk_score"] = df.apply(lambda row: calculate_heat_stress_risk(row, config), axis=1)
    df["disease_risk_score"] = df.apply(lambda row: calculate_disease_risk(row, config), axis=1)

    df["irrigation_risk_level"] = df["irrigation_risk_score"].apply(lambda s: classify_risk(s, config))
    df["heat_stress_risk_level"] = df["heat_stress_risk_score"].apply(lambda s: classify_risk(s, config))
    df["disease_risk_level"] = df["disease_risk_score"].apply(lambda s: classify_risk(s, config))

    if soil_lookup:
        soil_irrigation_factor = calculate_soil_irrigation_factor(soil_lookup)
        df["soil_irrigation_factor"] = soil_irrigation_factor
        df["soil_adjusted_irrigation_risk_score"] = (
            df["irrigation_risk_score"] * soil_irrigation_factor
        ).clip(0.0, 1.0)
        df["soil_adjusted_irrigation_risk_level"] = df["soil_adjusted_irrigation_risk_score"].apply(
            lambda s: classify_risk(s, config)
        )

    df["data_source"] = "Open-Meteo Forecast"

    return df


def main():
    config = get_config()

    input_path = config.path("open_meteo_csv")
    output_path = config.path("forecast_risk_csv")
    soil_csv = config.path("soilgrids_csv")

    log.info("Starting forecast mango risk scoring...")

    if not input_path.exists():
        log.error("Missing input file: %s", input_path)
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Run src/weather/fetch_open_meteo.py first (or `python "
            "main.py` for the full pipeline)."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        soil_lookup = load_topsoil_summary(soil_csv) if soil_csv.exists() else None

        open_meteo_df = pd.read_csv(input_path)
        validate_forecast_weather(open_meteo_df)

        forecast_risk_df = add_forecast_risk_scores(open_meteo_df, config, soil_lookup)
        validate_risk_data(forecast_risk_df)
    except Exception:
        log.error("Forecast risk scoring FAILED. See details below.")
        raise

    forecast_risk_df.to_csv(output_path, index=False)
    log.info("Open-Meteo forecast risk scores generated successfully.")
    log.info("Output file: %s", output_path)
    log.info("Rows: %d", len(forecast_risk_df))
    if soil_lookup:
        factor = forecast_risk_df["soil_irrigation_factor"].iloc[0]
        log.info("Soil irrigation factor applied: %.2f (%s)", factor, soil_factor_label(factor))

    preview_columns = [
        "date",
        "rainfall_mm",
        "rainfall_7day_mm",
        "temperature_max_c",
        "relative_humidity_percent",
        "et0_mm",
        "irrigation_risk_level",
        "heat_stress_risk_level",
        "disease_risk_level",
    ]

    print()
    print("First 5 rows:")
    print(forecast_risk_df[preview_columns].head())

    print()
    print("Last 5 rows:")
    print(forecast_risk_df[preview_columns].tail())

    print()
    print(f"Total rows: {len(forecast_risk_df)}")
    print(f"Start date: {forecast_risk_df['date'].min()}")
    print(f"End date: {forecast_risk_df['date'].max()}")


if __name__ == "__main__":
    main()
