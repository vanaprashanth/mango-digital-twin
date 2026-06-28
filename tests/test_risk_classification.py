"""
Tests for risk-score classification (Low / Medium / High) in
src/risk/historical_risk_engine.py. Uses the real project config so the
thresholds tested match what the dashboard and pipeline actually use.
"""

from src.risk.historical_risk_engine import classify_risk
from src.utils.config import get_config


def test_classify_risk_low():
    config = get_config()
    medium = config.get_threshold("classification", "medium")
    assert classify_risk(medium - 0.05, config) == "Low"


def test_classify_risk_medium():
    config = get_config()
    medium = config.get_threshold("classification", "medium")
    high = config.get_threshold("classification", "high")
    midpoint = (medium + high) / 2
    assert classify_risk(midpoint, config) == "Medium"


def test_classify_risk_high():
    config = get_config()
    high = config.get_threshold("classification", "high")
    assert classify_risk(high, config) == "High"
    assert classify_risk(1.0, config) == "High"


def test_classify_risk_boundaries_are_inclusive():
    """Scores exactly at a threshold should round up to that category."""
    config = get_config()
    medium = config.get_threshold("classification", "medium")
    high = config.get_threshold("classification", "high")
    assert classify_risk(medium, config) == "Medium"
    assert classify_risk(high, config) == "High"
