"""
Tests for src/utils/validation.py — the required-columns checks used by
every fetch script, risk engine, and the dashboard.
"""

import pandas as pd
import pytest

from src.utils.validation import (
    MissingColumnsError,
    validate_columns,
    validate_forecast_weather,
    validate_historical_weather,
    validate_risk_data,
    validate_soil_data,
    REQUIRED_HISTORICAL_WEATHER_COLUMNS,
    REQUIRED_FORECAST_WEATHER_COLUMNS,
    REQUIRED_SOIL_COLUMNS,
    REQUIRED_RISK_COLUMNS,
)


def _complete_df(columns: list[str]) -> pd.DataFrame:
    """Build a one-row DataFrame containing every required column."""
    return pd.DataFrame({col: [1] for col in columns})


def test_validate_columns_passes_when_all_present():
    df = _complete_df(["a", "b", "c"])
    # Should not raise.
    validate_columns(df, ["a", "b"], "test data")


def test_validate_columns_raises_when_missing():
    df = pd.DataFrame({"a": [1]})
    with pytest.raises(MissingColumnsError) as exc_info:
        validate_columns(df, ["a", "b"], "test data")
    assert "b" in str(exc_info.value)
    assert "test data" in str(exc_info.value)


def test_validate_historical_weather_with_complete_columns():
    df = _complete_df(REQUIRED_HISTORICAL_WEATHER_COLUMNS)
    validate_historical_weather(df)  # should not raise


def test_validate_forecast_weather_with_complete_columns():
    df = _complete_df(REQUIRED_FORECAST_WEATHER_COLUMNS)
    validate_forecast_weather(df)  # should not raise


def test_validate_soil_data_with_complete_columns():
    df = _complete_df(REQUIRED_SOIL_COLUMNS)
    validate_soil_data(df)  # should not raise


def test_validate_risk_data_with_complete_columns():
    df = _complete_df(REQUIRED_RISK_COLUMNS)
    validate_risk_data(df)  # should not raise


def test_validate_risk_data_raises_on_missing_column():
    columns = [c for c in REQUIRED_RISK_COLUMNS if c != "irrigation_risk_score"]
    df = _complete_df(columns)
    with pytest.raises(MissingColumnsError):
        validate_risk_data(df)
