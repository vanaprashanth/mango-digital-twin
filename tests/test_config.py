"""
Tests for src/utils/config.py.

These tests only read configs/config.yaml from disk — no network calls,
no cloud, no GPU. Safe to run anywhere, anytime.
"""

from pathlib import Path

from src.utils.config import get_config


def test_config_loads_without_error():
    config = get_config()
    assert config is not None


def test_study_area_fields_present():
    config = get_config()
    assert config.study_area.name
    assert config.study_area.district
    assert config.study_area.state
    assert config.study_area.country
    assert isinstance(config.latitude, float)
    assert isinstance(config.longitude, float)


def test_path_helper_returns_absolute_path():
    config = get_config()
    path = config.path("historical_risk_csv")
    assert isinstance(path, Path)
    assert path.is_absolute()
    assert str(path).endswith("muthukur_weather_risk_scores.csv")


def test_get_threshold_returns_a_number():
    config = get_config()
    high_threshold = config.get_threshold("classification", "high")
    medium_threshold = config.get_threshold("classification", "medium")
    assert isinstance(high_threshold, (int, float))
    assert isinstance(medium_threshold, (int, float))
    assert high_threshold > medium_threshold
