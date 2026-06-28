"""
Historical mango risk engine.

Reads raw NASA POWER weather and SoilGrids soil data, engineers rolling
rainfall features, scores irrigation / heat-stress / disease-friendly-weather
risk, applies a soil water-retention adjustment to irrigation risk, and
writes the combined table to data/processed/muthukur_weather_risk_scores.csv.

The irrigation/heat/disease scoring logic intentionally mirrors
src/risk/open_meteo_risk_engine.py (the forecast engine) so historical and
forecast risk scores are computed the same way and stay comparable. The one
NASA-POWER-specific difference is that solar radiation is used as an
irrigation-demand proxy in place of Open-Meteo's ET0 field, since NASA POWER
does not provide ET0 directly.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.soil_factor import calculate_soil_irrigation_factor, soil_factor_label
from src.utils.validation import validate_historical_weather, validate_risk_data

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
    Irrigation risk from low recent rainfall, high max temperature, and
    high solar radiation (a proxy for evaporative demand in the absence of
    an ET0 field from NASA POWER).
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

    if row["solar_radiation_mj_m2"] >= t["solar_radiation_high_mj_m2"]:
        score += 0.25
    elif row["solar_radiation_mj_m2"] >= t["solar_radiation_medium_mj_m2"]:
        score += 0.15

    return min(score, 1.0)


def calculate_heat_stress_risk(row, config) -> float:
    """Heat stress risk from maximum and average temperature."""

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
    Disease-friendly weather risk from humidity, a fungal-favorable
    temperature band, and recent (3-day) rainfall/wetness.
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


def load_topsoil_summary(soil_csv_path: Path) -> dict[str, float]:
    """
    Load the SoilGrids point CSV and average each property over 0-30 cm,
    returning a simple {property: value} lookup.
    """

    soil_df = pd.read_csv(soil_csv_path)

    topsoil_summary = (
        soil_df.groupby("property")["converted_value"].mean()
    )

    return topsoil_summary.to_dict()


def build_historical_risk_table(weather_df: pd.DataFrame, soil_lookup: dict[str, float], config) -> pd.DataFrame:
    """
    Engineer rolling rainfall features, score irrigation / heat / disease
    risk, and apply the soil-adjusted irrigation risk.
    """

    df = weather_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # NASA POWER uses -999 as a missing-data sentinel (most often for the
    # most recent 1-3 days, before its source data has been finalized).
    # Drop any row where a sentinel would otherwise leak into rolling
    # rainfall sums or risk scoring as a real reading.
    weather_columns = [
        "temperature_avg_c",
        "temperature_max_c",
        "temperature_min_c",
        "relative_humidity_percent",
        "rainfall_mm",
        "solar_radiation_mj_m2",
        "wind_speed_m_s",
    ]
    df[weather_columns] = df[weather_columns].replace(-999, pd.NA)
    df = df.dropna(subset=weather_columns).reset_index(drop=True)

    df["rainfall_3day_mm"] = df["rainfall_mm"].rolling(window=3, min_periods=1).sum()
    df["rainfall_7day_mm"] = df["rainfall_mm"].rolling(window=7, min_periods=1).sum()

    df["irrigation_risk_score"] = df.apply(lambda row: calculate_irrigation_risk(row, config), axis=1)
    df["heat_stress_risk_score"] = df.apply(lambda row: calculate_heat_stress_risk(row, config), axis=1)
    df["disease_risk_score"] = df.apply(lambda row: calculate_disease_risk(row, config), axis=1)

    soil_irrigation_factor = calculate_soil_irrigation_factor(soil_lookup)
    df["soil_irrigation_factor"] = soil_irrigation_factor

    df["soil_adjusted_irrigation_risk_score"] = (
        df["irrigation_risk_score"] * soil_irrigation_factor
    ).clip(0.0, 1.0)

    df["irrigation_risk_level"] = df["irrigation_risk_score"].apply(lambda s: classify_risk(s, config))
    df["heat_stress_risk_level"] = df["heat_stress_risk_score"].apply(lambda s: classify_risk(s, config))
    df["disease_risk_level"] = df["disease_risk_score"].apply(lambda s: classify_risk(s, config))
    df["soil_adjusted_irrigation_risk_level"] = df["soil_adjusted_irrigation_risk_score"].apply(
        lambda s: classify_risk(s, config)
    )

    df["data_source"] = "NASA POWER Historical"

    return df


def main():
    config = get_config()

    weather_csv = config.path("nasa_power_csv")
    soil_csv = config.path("soilgrids_csv")
    output_path = config.path("historical_risk_csv")

    log.info("Starting historical mango risk scoring...")

    if not weather_csv.exists():
        log.error("Missing input file: %s", weather_csv)
        raise FileNotFoundError(
            f"NASA POWER weather file not found: {weather_csv}. "
            "Run src/weather/fetch_weather.py first (or `python main.py` "
            "for the full pipeline)."
        )
    if not soil_csv.exists():
        log.error("Missing input file: %s", soil_csv)
        raise FileNotFoundError(
            f"SoilGrids file not found: {soil_csv}. "
            "Run src/soil/fetch_soilgrids.py first (or `python main.py` "
            "for the full pipeline)."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        weather_df = pd.read_csv(weather_csv)
        validate_historical_weather(weather_df)
        soil_lookup = load_topsoil_summary(soil_csv)

        risk_df = build_historical_risk_table(weather_df, soil_lookup, config)
        validate_risk_data(risk_df)
    except Exception:
        log.error("Historical risk scoring FAILED. See details below.")
        raise

    risk_df.to_csv(output_path, index=False)

    soil_factor = risk_df["soil_irrigation_factor"].iloc[0]
    log.info("Historical mango risk scores generated successfully.")
    log.info("Output file: %s", output_path)
    log.info("Rows: %d | Soil irrigation factor: %.2f (%s)", len(risk_df), soil_factor, soil_factor_label(soil_factor))

    preview_columns = [
        "date",
        "rainfall_mm",
        "rainfall_7day_mm",
        "temperature_max_c",
        "relative_humidity_percent",
        "irrigation_risk_level",
        "soil_adjusted_irrigation_risk_level",
        "heat_stress_risk_level",
        "disease_risk_level",
    ]

    print()
    print("First 5 rows:")
    print(risk_df[preview_columns].head())
    print()
    print("Last 5 rows:")
    print(risk_df[preview_columns].tail())
    print()
    print(f"Total rows: {len(risk_df)}")
    print(f"Start date: {risk_df['date'].min()}")
    print(f"End date: {risk_df['date'].max()}")


if __name__ == "__main__":
    main()
