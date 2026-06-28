"""
NASA POWER historical weather pipeline.

Fetches daily historical weather for the study area defined in
configs/config.yaml and writes it to data/raw/muthukur_weather_nasa_power.csv.
"""

import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validation import validate_historical_weather

log = get_logger(__name__)

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


def fetch_nasa_power_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    parameters: list[str],
) -> pd.DataFrame:
    """
    Fetch daily weather data from NASA POWER API for a given point location.

    Parameters:
        latitude (float): Latitude of the study area
        longitude (float): Longitude of the study area
        start_date (str): Start date in YYYYMMDD format
        end_date (str): End date in YYYYMMDD format
        parameters (list[str]): NASA POWER parameter codes to request

    Returns:
        pandas.DataFrame: Daily weather data
    """

    params = {
        "parameters": ",".join(parameters),
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": start_date,
        "end": end_date,
        "format": "JSON",
    }

    try:
        response = requests.get(NASA_POWER_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            f"NASA POWER API request failed: {exc}. "
            "Check your internet connection and try again. "
            f"URL: {NASA_POWER_URL}"
        ) from exc

    data = response.json()

    if "properties" not in data or "parameter" not in data["properties"]:
        raise RuntimeError(
            "NASA POWER API returned an unexpected response (no weather "
            f"data found). Raw response: {data}"
        )

    daily_parameters = data["properties"]["parameter"]

    df = pd.DataFrame(daily_parameters)

    # NASA POWER returns dates as YYYYMMDD in the index
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df.index.name = "date"

    df = df.reset_index()

    # Rename columns into readable names
    df = df.rename(
        columns={
            "T2M": "temperature_avg_c",
            "T2M_MAX": "temperature_max_c",
            "T2M_MIN": "temperature_min_c",
            "RH2M": "relative_humidity_percent",
            "PRECTOTCORR": "rainfall_mm",
            "ALLSKY_SFC_SW_DWN": "solar_radiation_mj_m2",
            "WS2M": "wind_speed_m_s",
        }
    )

    return df


def main():
    config = get_config()

    output_path = config.path("nasa_power_csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    start_date = config.historical_start_date()
    end_date = config.historical_end_date()

    log.info("Starting NASA POWER historical weather fetch...")
    log.info(
        "Location: %s, %s district (lat=%s, lon=%s)",
        config.study_area.name,
        config.study_area.district,
        config.latitude,
        config.longitude,
    )
    log.info("Date range: %s to %s", start_date, end_date)

    try:
        weather_df = fetch_nasa_power_weather(
            latitude=config.latitude,
            longitude=config.longitude,
            start_date=start_date,
            end_date=end_date,
            parameters=config.historical_weather["parameters"],
        )
        validate_historical_weather(weather_df)
    except Exception:
        log.error("NASA POWER fetch FAILED. See details below.")
        raise

    weather_df.to_csv(output_path, index=False)

    log.info("NASA POWER weather data saved successfully.")
    log.info("Output file: %s", output_path)
    log.info("Rows fetched: %d", len(weather_df))
    print()
    print(weather_df.head())


if __name__ == "__main__":
    main()
