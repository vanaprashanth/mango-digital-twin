"""
tests/test_irrigation_events.py

Tests for the irrigation event loader and its integration with the FAO-56
water balance scripts.

Test inventory
--------------
1. load_irrigation_events: missing CSV → empty DataFrame with correct schema
2. load_irrigation_events: invalid dates and negative irrigation_mm rows are dropped
3. load_irrigation_events: duplicate dates are aggregated (sum mm, join unique text)
4. compute_water_balance: output columns unchanged when no irrigation events present
5. compute_water_balance: irrigation_mm and water_input_mm columns present with events
6. compute_water_balance: root-zone depletion is reduced on irrigation days vs rainfed
7. Dashboard import: app.sections.irrigation_events imports without error
8. append_irrigation_event: creates file with header if missing
9. append_irrigation_event: appends a valid event without corrupting existing rows
10. append_irrigation_event: rejects negative irrigation_mm and invalid dates
11. append_irrigation_event: preserves expected CSV columns
12. append_irrigation_event: multiple events append correctly
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure project root is on sys.path for all imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.irrigation.load_irrigation_events import (
    append_irrigation_event,
    load_irrigation_events,
)
from src.water_balance.fao56_water_balance import compute_water_balance, compute_et0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_csv(tmp_path: Path, content: str) -> Path:
    """Write a CSV string to a temp file and return its path."""
    p = tmp_path / "irrigation_events.csv"
    p.write_text(textwrap.dedent(content).strip(), encoding="utf-8")
    return p


def _minimal_feature_df(n_days: int = 10) -> pd.DataFrame:
    """
    Minimal combined-feature-table DataFrame to feed compute_water_balance.
    Uses fixed but plausible values for a South Indian orchard.
    """
    dates = pd.date_range("2025-03-01", periods=n_days, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "temperature_avg_c": [28.0] * n_days,
            "temperature_max_c": [34.0] * n_days,
            "temperature_min_c": [22.0] * n_days,
            "relative_humidity_percent": [65.0] * n_days,
            "solar_radiation_mj_m2": [18.0] * n_days,
            "wind_speed_m_s": [2.0] * n_days,
            "rainfall_mm": [0.0] * n_days,
            # SoilGrids soil properties required by _field_capacity_and_wilting_point
            "sand_percent": [40.0] * n_days,
            "clay_percent": [25.0] * n_days,
            "organic_carbon_g_kg": [12.0] * n_days,
        }
    )


# ---------------------------------------------------------------------------
# Test 1 — missing file returns empty DataFrame
# ---------------------------------------------------------------------------

def test_missing_file_returns_empty_dataframe(tmp_path):
    path = tmp_path / "does_not_exist.csv"
    df = load_irrigation_events(path)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert "date" in df.columns
    assert "irrigation_mm" in df.columns


# ---------------------------------------------------------------------------
# Test 2 — invalid rows (bad dates, negative mm) are silently dropped
# ---------------------------------------------------------------------------

def test_invalid_and_negative_rows_are_dropped(tmp_path):
    csv_content = """
    date,irrigation_mm,method,source,notes
    not-a-date,20.0,drip,farmer,bad date
    2025-03-05,-10.0,drip,farmer,negative mm
    2025-03-05,0.0,drip,farmer,zero mm
    2025-03-10,25.0,drip,farmer,valid row
    """
    path = _write_csv(tmp_path, csv_content)
    df = load_irrigation_events(path)

    assert len(df) == 1, f"Expected 1 valid row, got {len(df)}"
    assert df.iloc[0]["irrigation_mm"] == pytest.approx(25.0)
    assert df.iloc[0]["date"] == pd.Timestamp("2025-03-10")


# ---------------------------------------------------------------------------
# Test 3 — duplicate dates are aggregated correctly
# ---------------------------------------------------------------------------

def test_duplicate_dates_are_aggregated(tmp_path):
    csv_content = """
    date,irrigation_mm,method,source,notes
    2025-03-15,20.0,drip,farmer,morning
    2025-03-15,10.0,flood,agronomist,afternoon
    2025-03-20,30.0,drip,farmer,single event
    """
    path = _write_csv(tmp_path, csv_content)
    df = load_irrigation_events(path)

    assert len(df) == 2, f"Expected 2 aggregated rows, got {len(df)}"

    march_15 = df[df["date"] == pd.Timestamp("2025-03-15")].iloc[0]
    assert march_15["irrigation_mm"] == pytest.approx(30.0), "Sum should be 20+10=30"
    # Both methods should appear in the aggregated string
    assert "drip" in march_15["method"]
    assert "flood" in march_15["method"]

    march_20 = df[df["date"] == pd.Timestamp("2025-03-20")].iloc[0]
    assert march_20["irrigation_mm"] == pytest.approx(30.0)


# ---------------------------------------------------------------------------
# Test 4 — FAO-56 output columns unchanged without irrigation events
# ---------------------------------------------------------------------------

def test_fao56_output_unchanged_without_irrigation():
    df = _minimal_feature_df(n_days=10)
    et0 = compute_et0(df, latitude_deg=13.29, elevation_m=150, albedo=0.23)

    result = compute_water_balance(
        df, et0=et0, kc_constant=0.75, root_depth_m=1.2,
        depletion_fraction_p=0.50,
        irrigation_mm_arr=None,
    )

    # Core output columns must always be present
    required = [
        "date", "et0_mm", "etc_mm", "rainfall_mm",
        "root_zone_depletion_mm", "taw_mm", "raw_mm",
        "water_stress_coefficient_ks", "water_stress_level",
    ]
    for col in required:
        assert col in result.columns, f"Missing required column: {col}"

    # irrigation_mm and water_input_mm are now always present (both zero here)
    assert "irrigation_mm" in result.columns
    assert "water_input_mm" in result.columns
    assert result["irrigation_mm"].sum() == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Test 5 — FAO-56 output includes irrigation_mm and water_input_mm with events
# ---------------------------------------------------------------------------

def test_fao56_includes_irrigation_columns_with_events():
    n_days = 10
    df = _minimal_feature_df(n_days=n_days)
    irrigation = np.zeros(n_days)
    irrigation[3] = 25.0  # irrigation event on day 4

    et0 = compute_et0(df, latitude_deg=13.29, elevation_m=150, albedo=0.23)
    result = compute_water_balance(
        df, et0=et0, kc_constant=0.75, root_depth_m=1.2,
        depletion_fraction_p=0.50,
        irrigation_mm_arr=irrigation,
    )

    assert "irrigation_mm" in result.columns
    assert "water_input_mm" in result.columns
    assert result.iloc[3]["irrigation_mm"] == pytest.approx(25.0)
    assert result.iloc[3]["water_input_mm"] == pytest.approx(
        result.iloc[3]["rainfall_mm"] + 25.0
    )
    # Other days have zero irrigation
    assert result.iloc[0]["irrigation_mm"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Test 6 — depletion is reduced on irrigation days vs rainfed baseline
# ---------------------------------------------------------------------------

def test_depletion_reduced_on_irrigation_days():
    n_days = 10
    df = _minimal_feature_df(n_days=n_days)
    et0 = compute_et0(df, latitude_deg=13.29, elevation_m=150, albedo=0.23)

    # Rainfed baseline
    rainfed = compute_water_balance(
        df, et0=et0, kc_constant=0.75, root_depth_m=1.2,
        depletion_fraction_p=0.50,
        irrigation_mm_arr=None,
    )

    # With irrigation on day 5
    irrigation = np.zeros(n_days)
    irrigation[4] = 40.0
    irrigated = compute_water_balance(
        df, et0=et0, kc_constant=0.75, root_depth_m=1.2,
        depletion_fraction_p=0.50,
        irrigation_mm_arr=irrigation,
    )

    # From day 5 onward, irrigated depletion must be <= rainfed depletion
    # (irrigation reduces depletion; it cannot increase it)
    for i in range(5, n_days):
        assert irrigated.iloc[i]["root_zone_depletion_mm"] <= (
            rainfed.iloc[i]["root_zone_depletion_mm"] + 1e-6  # float tolerance
        ), (
            f"Day {i}: irrigated depletion {irrigated.iloc[i]['root_zone_depletion_mm']:.3f} "
            f"> rainfed {rainfed.iloc[i]['root_zone_depletion_mm']:.3f}"
        )


# ---------------------------------------------------------------------------
# Test 7 — dashboard page imports without error
# ---------------------------------------------------------------------------

def test_dashboard_import_succeeds():
    """Import app.sections.irrigation_events — must not raise."""
    import importlib
    mod = importlib.import_module("app.sections.irrigation_events")
    assert hasattr(mod, "render_irrigation_events_page"), (
        "render_irrigation_events_page function not found in module"
    )


# ---------------------------------------------------------------------------
# Test 8 — append_irrigation_event: creates file with header if missing
# ---------------------------------------------------------------------------

def test_append_creates_file_if_missing(tmp_path):
    path = tmp_path / "new_events.csv"
    assert not path.exists()

    append_irrigation_event(
        path=path,
        date="2025-05-01",
        irrigation_mm=20.0,
        method="drip",
        source="user_dashboard",
        notes="first event",
    )

    assert path.exists()
    df = load_irrigation_events(path)
    assert len(df) == 1
    assert df.iloc[0]["irrigation_mm"] == pytest.approx(20.0)
    assert df.iloc[0]["method"] == "drip"
    assert df.iloc[0]["source"] == "user_dashboard"


# ---------------------------------------------------------------------------
# Test 9 — append_irrigation_event: appends a valid event without corrupting
# existing rows
# ---------------------------------------------------------------------------

def test_append_valid_event_preserves_existing_rows(tmp_path):
    csv_content = """
    date,irrigation_mm,method,source,notes
    2025-03-10,25.0,drip,farmer,valid row
    """
    path = _write_csv(tmp_path, csv_content)

    append_irrigation_event(
        path=path,
        date="2025-05-01",
        irrigation_mm=15.0,
        method="sprinkler",
        source="user_dashboard",
        notes="second event",
    )

    df = load_irrigation_events(path)
    assert len(df) == 2
    assert df.iloc[0]["date"] == pd.Timestamp("2025-03-10")
    assert df.iloc[0]["irrigation_mm"] == pytest.approx(25.0)
    assert df.iloc[1]["date"] == pd.Timestamp("2025-05-01")
    assert df.iloc[1]["irrigation_mm"] == pytest.approx(15.0)
    assert df.iloc[1]["source"] == "user_dashboard"


# ---------------------------------------------------------------------------
# Test 10 — append_irrigation_event: rejects negative irrigation_mm
# ---------------------------------------------------------------------------

def test_append_rejects_negative_irrigation_mm(tmp_path):
    path = tmp_path / "events.csv"

    with pytest.raises(ValueError):
        append_irrigation_event(
            path=path,
            date="2025-05-01",
            irrigation_mm=-5.0,
            method="drip",
            source="user_dashboard",
            notes="invalid",
        )

    # No file should be created (or if created earlier, must remain unwritten)
    assert not path.exists()


def test_append_rejects_invalid_date(tmp_path):
    path = tmp_path / "events.csv"

    with pytest.raises(ValueError):
        append_irrigation_event(
            path=path,
            date="not-a-date",
            irrigation_mm=10.0,
            method="drip",
            source="user_dashboard",
            notes="invalid date",
        )

    assert not path.exists()


# ---------------------------------------------------------------------------
# Test 11 — append_irrigation_event: preserves expected CSV columns
# ---------------------------------------------------------------------------

def test_append_preserves_expected_columns(tmp_path):
    path = tmp_path / "events.csv"

    append_irrigation_event(
        path=path,
        date="2025-05-01",
        irrigation_mm=10.0,
        method="manual",
        source="user_dashboard",
        notes="",
    )

    header = path.read_text(encoding="utf-8").splitlines()[0]
    assert header == "date,irrigation_mm,method,source,notes"


# ---------------------------------------------------------------------------
# Test 12 — append_irrigation_event: multiple events append correctly
# ---------------------------------------------------------------------------

def test_append_multiple_events_accumulate(tmp_path):
    path = tmp_path / "events.csv"

    append_irrigation_event(path=path, date="2025-05-01", irrigation_mm=10.0, method="drip", source="user_dashboard", notes="e1")
    append_irrigation_event(path=path, date="2025-05-05", irrigation_mm=20.0, method="flood", source="user_dashboard", notes="e2")
    append_irrigation_event(path=path, date="2025-05-10", irrigation_mm=30.0, method="sprinkler", source="user_dashboard", notes="e3")

    df = load_irrigation_events(path)
    assert len(df) == 3
    assert list(df["irrigation_mm"]) == pytest.approx([10.0, 20.0, 30.0])
    assert df["source"].eq("user_dashboard").all()
