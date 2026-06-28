"""
Tests for the soil-adjusted irrigation factor logic in
src/utils/soil_factor.py (the single shared utility used by both risk
engines and the Streamlit dashboard).
"""

import pytest

from src.utils.soil_factor import (
    calculate_soil_irrigation_factor,
    soil_factor_label,
)


def test_factor_is_neutral_for_baseline_soil():
    """clay=20, sand=40, soc=10 are the heuristic's neutral baseline values."""
    factor = calculate_soil_irrigation_factor({"clay": 20.0, "sand": 40.0, "soc": 10.0})
    assert factor == 1.0


def test_high_clay_and_organic_carbon_reduce_factor():
    factor = calculate_soil_irrigation_factor({"clay": 40.0, "sand": 20.0, "soc": 30.0})
    assert factor < 1.0


def test_high_sand_increases_factor():
    factor = calculate_soil_irrigation_factor({"clay": 10.0, "sand": 80.0, "soc": 5.0})
    assert factor > 1.0


def test_factor_is_clipped_to_plausible_band():
    extreme_low = calculate_soil_irrigation_factor({"clay": 100.0, "sand": 0.0, "soc": 100.0})
    extreme_high = calculate_soil_irrigation_factor({"clay": 0.0, "sand": 100.0, "soc": 0.0})
    assert extreme_low >= 0.7
    assert extreme_high <= 1.3


def test_factor_label_matches_value():
    assert soil_factor_label(0.8) == "Reduces irrigation risk"
    assert soil_factor_label(1.2) == "Increases irrigation risk"
    assert soil_factor_label(1.0) == "Neutral soil effect"


def test_missing_soil_properties_fall_back_to_defaults():
    """
    An empty soil lookup should fall back to the function's built-in default
    soil values (clay=25, sand=40, soc=10) rather than raising an error.
    That default combination gives a factor of 0.98, not exactly neutral.
    """
    factor = calculate_soil_irrigation_factor({})
    assert factor == pytest.approx(0.98)
