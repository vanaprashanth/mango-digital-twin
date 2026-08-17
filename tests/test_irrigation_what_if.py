"""
tests/test_irrigation_what_if.py

Tests for the pure helper functions in app/sections/irrigation_what_if.py.

These functions are fully independent of Streamlit and can be imported and
tested without any dashboard context.

Test inventory
--------------
1. apply_scenario_irrigation: positive irrigation reduces depletion correctly
2. apply_scenario_irrigation: irrigation cannot push depletion below zero
3. apply_scenario_irrigation: zero irrigation leaves depletion unchanged
4. classify_stress_from_depletion: below RAW → Low stress
5. classify_stress_from_depletion: above RAW, moderate deficit → Medium stress
6. classify_stress_from_depletion: high depletion → High stress
7. classify_stress_from_depletion: depletion at zero (field capacity) → Low
8. classify_stress_from_depletion: depletion equals TAW (all water gone) → High
9. classify_stress_from_depletion: TAW == RAW (degenerate soil) → graceful Low
10. scenario_stress_rank: ordering is consistent (Low < Medium < High)
11. Dashboard page import succeeds without error
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.sections.irrigation_what_if import (
    apply_scenario_irrigation,
    classify_stress_from_depletion,
    scenario_stress_rank,
)


# ---------------------------------------------------------------------------
# apply_scenario_irrigation
# ---------------------------------------------------------------------------

def test_positive_irrigation_reduces_depletion():
    result = apply_scenario_irrigation(current_depletion_mm=50.0, irrigation_mm=25.0)
    assert result == pytest.approx(25.0)


def test_irrigation_clamped_at_zero():
    """Irrigating more than current depletion → depletion hits 0 (field capacity)."""
    result = apply_scenario_irrigation(current_depletion_mm=10.0, irrigation_mm=30.0)
    assert result == pytest.approx(0.0)
    assert result >= 0.0


def test_zero_irrigation_leaves_depletion_unchanged():
    result = apply_scenario_irrigation(current_depletion_mm=42.7, irrigation_mm=0.0)
    assert result == pytest.approx(42.7)


def test_exact_match_irrigation_gives_zero():
    """Irrigating exactly the current depletion → depletion = 0."""
    result = apply_scenario_irrigation(current_depletion_mm=35.0, irrigation_mm=35.0)
    assert result == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# classify_stress_from_depletion
# ---------------------------------------------------------------------------

def test_stress_low_when_below_raw():
    """Depletion below RAW → Ks = 1.0 → Low stress."""
    result = classify_stress_from_depletion(depletion_mm=20.0, taw_mm=100.0, raw_mm=50.0)
    assert result == "Low"


def test_stress_medium_at_intermediate_depletion():
    """
    Depletion at 75 mm, TAW=100, RAW=50 → Ks = (100-75)/(100-50) = 0.50 → High.
    Depletion at 65 mm → Ks = (100-65)/(100-50) = 0.70 → Medium.
    """
    result = classify_stress_from_depletion(depletion_mm=65.0, taw_mm=100.0, raw_mm=50.0)
    assert result == "Medium"


def test_stress_high_at_large_depletion():
    """Depletion near TAW → Ks very low → High stress."""
    result = classify_stress_from_depletion(depletion_mm=95.0, taw_mm=100.0, raw_mm=50.0)
    assert result == "High"


def test_stress_low_at_field_capacity():
    """Depletion = 0 (field capacity, freshly irrigated) → Low stress."""
    result = classify_stress_from_depletion(depletion_mm=0.0, taw_mm=100.0, raw_mm=50.0)
    assert result == "Low"


def test_stress_high_when_depletion_equals_taw():
    """Depletion = TAW (all available water exhausted) → Ks = 0 → High."""
    result = classify_stress_from_depletion(depletion_mm=100.0, taw_mm=100.0, raw_mm=50.0)
    assert result == "High"


def test_degenerate_taw_equals_raw_returns_low():
    """Edge case: TAW == RAW (denom = 0) → treated as no stress threshold → Low."""
    result = classify_stress_from_depletion(depletion_mm=50.0, taw_mm=50.0, raw_mm=50.0)
    assert result == "Low"


# ---------------------------------------------------------------------------
# scenario_stress_rank
# ---------------------------------------------------------------------------

def test_stress_rank_ordering():
    assert scenario_stress_rank("Low") < scenario_stress_rank("Medium")
    assert scenario_stress_rank("Medium") < scenario_stress_rank("High")


def test_stress_rank_unknown_defaults_to_medium():
    assert scenario_stress_rank("Unknown") == scenario_stress_rank("Medium")


# ---------------------------------------------------------------------------
# Dashboard page import
# ---------------------------------------------------------------------------

def test_dashboard_page_imports_successfully():
    """Import must succeed and expose render_irrigation_what_if_page."""
    mod = importlib.import_module("app.sections.irrigation_what_if")
    assert hasattr(mod, "render_irrigation_what_if_page"), (
        "render_irrigation_what_if_page not found in module"
    )
    assert callable(mod.render_irrigation_what_if_page)
