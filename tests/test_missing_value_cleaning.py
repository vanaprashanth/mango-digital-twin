"""
Tests for the NASA POWER `-999` missing-value cleaning step inside
build_historical_risk_table() in src/risk/historical_risk_engine.py.

NASA POWER uses -999 as a "no data yet" sentinel, most often for the most
recent 1-3 days before its source data is finalized. These rows must be
dropped before rolling rainfall sums and risk scoring run, or a single
-999 would corrupt every downstream calculation that touches it.
"""

import pandas as pd

from src.risk.historical_risk_engine import build_historical_risk_table
from src.utils.config import get_config


def _make_weather_df(num_good_days: int = 10) -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=num_good_days, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "temperature_avg_c": [28.0] * num_good_days,
            "temperature_max_c": [33.0] * num_good_days,
            "temperature_min_c": [22.0] * num_good_days,
            "relative_humidity_percent": [70.0] * num_good_days,
            "rainfall_mm": [2.0] * num_good_days,
            "solar_radiation_mj_m2": [18.0] * num_good_days,
            "wind_speed_m_s": [2.5] * num_good_days,
        }
    )


def test_clean_rows_pass_through_unaffected():
    config = get_config()
    weather_df = _make_weather_df(num_good_days=10)
    soil_lookup = {"clay": 20.0, "sand": 40.0, "soc": 10.0}

    risk_df = build_historical_risk_table(weather_df, soil_lookup, config)

    assert len(risk_df) == 10


def test_minus_999_rows_are_dropped():
    config = get_config()
    weather_df = _make_weather_df(num_good_days=10)

    # Simulate NASA POWER not having finalized the most recent day yet.
    weather_df.loc[9, "temperature_avg_c"] = -999
    weather_df.loc[9, "rainfall_mm"] = -999

    soil_lookup = {"clay": 20.0, "sand": 40.0, "soc": 10.0}
    risk_df = build_historical_risk_table(weather_df, soil_lookup, config)

    # The sentinel row should be gone, and no -999 should leak into output.
    assert len(risk_df) == 9
    assert -999 not in risk_df["temperature_avg_c"].values
    assert -999 not in risk_df["rainfall_mm"].values


def test_multiple_minus_999_rows_are_dropped():
    config = get_config()
    weather_df = _make_weather_df(num_good_days=10)

    weather_df.loc[8, "relative_humidity_percent"] = -999
    weather_df.loc[9, "solar_radiation_mj_m2"] = -999

    soil_lookup = {"clay": 20.0, "sand": 40.0, "soc": 10.0}
    risk_df = build_historical_risk_table(weather_df, soil_lookup, config)

    assert len(risk_df) == 8
