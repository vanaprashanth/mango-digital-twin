"""
Open-Meteo recent + forecast weather pipeline.

Fetches a short window of recent and forecast daily weather for the study
area defined in configs/config.yaml and writes it to
data/raw/muthukur_weather_open_meteo.csv. Open-Meteo does not require an
API key.
"""

import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validation import validate_forecast_weather

log = get_logger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_open_meteo_weather(
    latitude: float,
    longitude: float,
    past_days: int,
    forecast_days: int,
    timezone: str,
) -> pd.DataFrame:
    """
    Fetch recent and forecast daily weather data from Open-Meteo.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "precipitation_sum",
            "rain_sum",
            "relative_humidity_2m_mean",
            "shortwave_radiation_sum",
            "wind_speed_10m_max",
            "et0_fao_evapotranspiration",
        ],
        "timezone": timezone,
        "past_days": past_days,
        "forecast_days": forecast_days,
    }

    # Retry up to MAX_ATTEMPTS times with increasing timeouts.
    # Open-Meteo is usually fast but can be slow under load or from
    # GitHub Actions runners — a single 30-second timeout is too brittle.
    MAX_ATTEMPTS = 3
    TIMEOUTS = [45, 75, 120]   # seconds per attempt
    RETRY_DELAYS = [5, 15]     # seconds to wait between attempts

    last_exc: Exception | None = None
    for attempt, timeout in enumerate(TIMEOUTS, start=1):
        try:
            log.info(
                "Open-Meteo request attempt %d/%d (timeout=%ds)...",
                attempt, MAX_ATTEMPTS, timeout,
            )
            response = requests.get(OPEN_METEO_URL, params=params, timeout=timeout)
            response.raise_for_status()
            break   # success — exit retry loop
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            log.warning(
                "Open-Meteo attempt %d/%d failed: %s",
                attempt, MAX_ATTEMPTS, exc,
            )
            if attempt < MAX_ATTEMPTS:
                delay = RETRY_DELAYS[attempt - 1]
                log.info("Retrying in %ds...", delay)
                time.sleep(delay)
    else:
        # All attempts exhausted
        raise RuntimeError(
            f"Open-Meteo API request failed after {MAX_ATTEMPTS} attempts: {last_exc}. "
            "Check your internet connection and try again. "
            f"URL: {OPEN_METEO_URL}"
        ) from last_exc

    data = response.json()

    if "daily" not in data:
        raise RuntimeError(
            f"Open-Meteo API returned an unexpected response (no 'daily' "
            f"weather block found). Raw response: {data}"
        )

    daily = data["daily"]

    df = pd.DataFrame(daily)

    df = df.rename(
        columns={
            "time": "date",
            "temperature_2m_mean": "openmeteo_temperature_avg_c",
            "temperature_2m_max": "openmeteo_temperature_max_c",
            "temperature_2m_min": "openmeteo_temperature_min_c",
            "precipitation_sum": "openmeteo_precipitation_mm",
            "rain_sum": "openmeteo_rain_mm",
            "relative_humidity_2m_mean": "openmeteo_relative_humidity_percent",
            "shortwave_radiation_sum": "openmeteo_solar_radiation_mj_m2",
            "wind_speed_10m_max": "openmeteo_wind_speed_max_kmh",
            "et0_fao_evapotranspiration": "openmeteo_et0_mm",
        }
    )

    df["date"] = pd.to_datetime(df["date"])

    return df


def main():
    config = get_config()

    output_path = config.path("open_meteo_csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Starting Open-Meteo recent/forecast weather fetch...")
    log.info(
        "Location: %s, %s district (lat=%s, lon=%s)",
        config.study_area.name,
        config.study_area.district,
        config.latitude,
        config.longitude,
    )

    try:
        weather_df = fetch_open_meteo_weather(
            latitude=config.latitude,
            longitude=config.longitude,
            past_days=config.forecast_weather["past_days"],
            forecast_days=config.forecast_weather["forecast_days"],
            timezone=config.forecast_weather["timezone"],
        )
        validate_forecast_weather(weather_df)
    except Exception as exc:
        log.error("Open-Meteo fetch FAILED. See details below.")
        # If a cached CSV already exists, reuse it so the pipeline can
        # continue (historical weather + all downstream steps still run).
        # This makes the daily automated refresh resilient to transient
        # Open-Meteo API outages or GitHub Actions network timeouts.
        # If NO cache exists this is a fresh environment and we must fail.
        if output_path.exists():
            log.warning(
                "Open-Meteo fetch failed but cached CSV exists — reusing "
                "cached data: %s", output_path
            )
            log.warning(
                "Cached Open-Meteo data may be stale. Re-run the pipeline "
                "when the API is reachable to refresh forecast data."
            )
            print()
            print(
                "WARNING: Open-Meteo fetch failed. Reusing cached CSV "
                f"({output_path.name}) from a previous run. "
                "Forecast pages may show stale data until the API is reachable."
            )
            print(f"Fetch error: {exc}")
            return   # do not re-raise; pipeline continues with cached CSV
        raise   # no cached CSV: fail clearly

    weather_df.to_csv(output_path, index=False)

    log.info("Open-Meteo weather data saved successfully.")
    log.info("Output file: %s", output_path)
    log.info("Rows fetched: %d", len(weather_df))
    log.info("Date range: %s to %s", weather_df["date"].min(), weather_df["date"].max())
    print()
    print(weather_df.head())
    print()
    print(weather_df.tail())


if __name__ == "__main__":
    main()
