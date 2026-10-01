"""
tests/test_irrigation_impact.py

Tests for the Irrigation Impact Summary feature:
  app.sections.irrigation_events.build_irrigation_impact_table

This is a pure function (no Streamlit dependency, no file writes) that
joins recorded irrigation events with FAO-56 (interpolated-Kc) water
balance output to show how each event affected root-zone depletion.

Test inventory
--------------
1. Empty/None irrigation_df returns an empty DataFrame with the correct schema
2. Full join: event date and prior day both present in fao56_df ->
   depletion_before/on_event/reduction, stress level, and Ks are populated
3. Event date NOT present in fao56_df -> in_water_balance=False and the
   depletion/stress columns are NaN/None (pipeline needs to be rerun)
4. Event date present but prior day missing -> depletion_before is NaN,
   so depletion_reduction is also NaN, but depletion_on_event/stress/Ks
   are still populated
5. fao56_df is None -> every row returned with in_water_balance=False
6. Multiple events resolve independently and the result is sorted by date
7. Dashboard import (app.sections.irrigation_events) still works
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.sections.irrigation_events import build_irrigation_impact_table


def _irrigation_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def _fao56_df(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ---------------------------------------------------------------------------
# Test 1 — empty/None irrigation_df
# ---------------------------------------------------------------------------

def test_empty_irrigation_df_returns_empty_schema():
    result = build_irrigation_impact_table(None, None)
    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert "depletion_reduction_mm" in result.columns
    assert "in_water_balance" in result.columns

    result2 = build_irrigation_impact_table(pd.DataFrame(columns=["date", "irrigation_mm"]), None)
    assert result2.empty


# ---------------------------------------------------------------------------
# Test 2 — full join: prior day + event date both present
# ---------------------------------------------------------------------------

def test_full_join_populates_all_fields():
    irrigation_df = _irrigation_df(
        [{"date": "2025-03-15", "irrigation_mm": 25.0, "method": "drip", "source": "farmer", "notes": "top-up"}]
    )
    fao56_df = _fao56_df(
        [
            {"date": "2025-03-14", "root_zone_depletion_mm": 60.0, "water_stress_level": "Medium", "ks": 0.75},
            {"date": "2025-03-15", "root_zone_depletion_mm": 35.0, "water_stress_level": "Low", "ks": 1.0},
        ]
    )

    result = build_irrigation_impact_table(irrigation_df, fao56_df)

    assert len(result) == 1
    row = result.iloc[0]
    assert bool(row["in_water_balance"]) is True
    assert row["depletion_before_mm"] == pytest.approx(60.0)
    assert row["depletion_on_event_mm"] == pytest.approx(35.0)
    assert row["depletion_reduction_mm"] == pytest.approx(25.0)
    assert row["water_stress_level"] == "Low"
    assert row["ks"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Test 3 — event date not yet in fao56_df (pipeline needs rerun)
# ---------------------------------------------------------------------------

def test_event_date_missing_from_fao56_marks_not_in_balance():
    irrigation_df = _irrigation_df(
        [{"date": "2025-06-01", "irrigation_mm": 20.0, "method": "drip", "source": "user_dashboard", "notes": ""}]
    )
    fao56_df = _fao56_df(
        [{"date": "2025-05-01", "root_zone_depletion_mm": 40.0, "water_stress_level": "Low", "ks": 1.0}]
    )

    result = build_irrigation_impact_table(irrigation_df, fao56_df)

    assert len(result) == 1
    row = result.iloc[0]
    assert bool(row["in_water_balance"]) is False
    assert pd.isna(row["depletion_on_event_mm"])
    assert pd.isna(row["depletion_reduction_mm"])
    assert row["water_stress_level"] is None


# ---------------------------------------------------------------------------
# Test 4 — event date present but prior day missing from fao56_df
# ---------------------------------------------------------------------------

def test_missing_prior_day_leaves_before_and_reduction_nan():
    irrigation_df = _irrigation_df(
        [{"date": "2025-01-01", "irrigation_mm": 10.0, "method": "manual", "source": "farmer", "notes": ""}]
    )
    # Only the event date itself is present — no "2024-12-31" row.
    fao56_df = _fao56_df(
        [{"date": "2025-01-01", "root_zone_depletion_mm": 12.0, "water_stress_level": "Low", "ks": 1.0}]
    )

    result = build_irrigation_impact_table(irrigation_df, fao56_df)

    row = result.iloc[0]
    assert bool(row["in_water_balance"]) is True
    assert pd.isna(row["depletion_before_mm"])
    assert row["depletion_on_event_mm"] == pytest.approx(12.0)
    assert pd.isna(row["depletion_reduction_mm"])
    assert row["water_stress_level"] == "Low"


# ---------------------------------------------------------------------------
# Test 5 — fao56_df is None
# ---------------------------------------------------------------------------

def test_fao56_df_none_marks_all_rows_not_in_balance():
    irrigation_df = _irrigation_df(
        [
            {"date": "2025-03-15", "irrigation_mm": 25.0, "method": "drip", "source": "farmer", "notes": ""},
            {"date": "2025-04-02", "irrigation_mm": 30.0, "method": "flood", "source": "farmer", "notes": ""},
        ]
    )

    result = build_irrigation_impact_table(irrigation_df, None)

    assert len(result) == 2
    assert (~result["in_water_balance"]).all()
    assert result["depletion_on_event_mm"].isna().all()


# ---------------------------------------------------------------------------
# Test 6 — multiple events resolve independently, sorted by date
# ---------------------------------------------------------------------------

def test_multiple_events_resolve_independently_and_sorted():
    irrigation_df = _irrigation_df(
        [
            {"date": "2025-04-02", "irrigation_mm": 30.0, "method": "flood", "source": "farmer", "notes": ""},
            {"date": "2025-03-15", "irrigation_mm": 25.0, "method": "drip", "source": "farmer", "notes": ""},
        ]
    )
    fao56_df = _fao56_df(
        [
            {"date": "2025-03-14", "root_zone_depletion_mm": 60.0, "water_stress_level": "Medium", "ks": 0.75},
            {"date": "2025-03-15", "root_zone_depletion_mm": 35.0, "water_stress_level": "Low", "ks": 1.0},
            # 2025-04-01 and 2025-04-02 intentionally absent -> second event unresolved
        ]
    )

    result = build_irrigation_impact_table(irrigation_df, fao56_df)

    assert len(result) == 2
    # sorted by date ascending
    assert list(result["date"]) == sorted(result["date"])
    first, second = result.iloc[0], result.iloc[1]
    assert first["date"] == pd.Timestamp("2025-03-15")
    assert bool(first["in_water_balance"]) is True
    assert second["date"] == pd.Timestamp("2025-04-02")
    assert bool(second["in_water_balance"]) is False


# ---------------------------------------------------------------------------
# Test 7 — dashboard import
# ---------------------------------------------------------------------------

def test_dashboard_import_still_works():
    mod = importlib.import_module("app.sections.irrigation_events")
    assert hasattr(mod, "render_irrigation_events_page")
    assert hasattr(mod, "build_irrigation_impact_table")
    assert callable(mod.render_irrigation_events_page)
    assert callable(mod.build_irrigation_impact_table)
