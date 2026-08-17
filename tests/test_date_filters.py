"""
Tests for app/utils/date_filters.py.

All tests are offline — no Streamlit session, no network, no real data files.
The render_date_range_selector function is NOT tested here because it calls
st.selectbox and requires a running Streamlit session.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.utils.date_filters import (
    DATE_RANGE_OPTIONS,
    filter_by_date_range,
    get_date_range_options,
)


# ---------------------------------------------------------------------------
# Test 1 — "Max" returns all rows unchanged
# ---------------------------------------------------------------------------

class TestMaxReturnsAllRows:
    def test_max_returns_all_rows(self):
        """filter_by_date_range("Max") must return every row in the input."""
        df = pd.DataFrame({
            "date": pd.to_datetime(["2024-01-01", "2024-06-01", "2025-01-01"]),
            "value": [1, 2, 3],
        })
        result = filter_by_date_range(df, selected_range="Max")
        assert len(result) == len(df), "Max should return all rows"

    def test_max_preserves_row_content(self):
        df = pd.DataFrame({
            "date": pd.to_datetime(["2024-01-01", "2024-06-01"]),
            "value": [10, 20],
        })
        result = filter_by_date_range(df, selected_range="Max")
        assert list(result["value"]) == [10, 20]


# ---------------------------------------------------------------------------
# Test 2 — "1 week" uses max date in data, not system today
# ---------------------------------------------------------------------------

class TestWeekUsesDataMaxNotToday:
    def test_1_week_reference_is_data_max_not_today(self):
        """
        "1 week" must look back 7 days from the MAXIMUM date in the
        DataFrame, not from today.  If it used today, a DataFrame with
        old dates would return 0 rows — but here it must return at least
        the rows within 7 days of 2024-01-10.
        """
        # All dates are in January 2024 — clearly in the past, but the
        # latest is 2024-01-10.  A "1 week" window from 2024-01-10 should
        # include 2024-01-04 onward.
        df = pd.DataFrame({
            "date": pd.to_datetime([
                "2024-01-01",  # 9 days before max → outside 1-week window
                "2024-01-04",  # 6 days before max → inside
                "2024-01-07",  # 3 days before max → inside
                "2024-01-10",  # max date itself → inside
            ]),
            "value": [1, 2, 3, 4],
        })
        result = filter_by_date_range(df, selected_range="1 week")
        assert len(result) == 3, (
            "Should include 2024-01-04, 2024-01-07, 2024-01-10 (all within 7 days "
            "of the max date 2024-01-10), but not 2024-01-01."
        )
        assert "2024-01-01" not in result["date"].astype(str).values

    def test_reference_date_override(self):
        """When reference_date is given, it is used instead of data max."""
        df = pd.DataFrame({
            "date": pd.to_datetime(["2024-01-01", "2024-01-05", "2024-01-10"]),
            "value": [1, 2, 3],
        })
        # reference_date = 2024-01-07 → only rows >= 2023-12-31 (7 days back)
        # that is, >= 2023-12-31, so all three rows should be included
        result = filter_by_date_range(
            df, selected_range="1 week", reference_date="2024-01-07"
        )
        # 2024-01-01 is 6 days before 2024-01-07 → included
        # 2024-01-10 is 3 days AFTER 2024-01-07 → also included (>= cutoff)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Test 3 — Empty or missing date column handled safely
# ---------------------------------------------------------------------------

class TestEmptyAndMissingDate:
    def test_empty_dataframe_returns_empty(self):
        df = pd.DataFrame({"date": pd.Series([], dtype="datetime64[ns]"), "value": []})
        result = filter_by_date_range(df, selected_range="1 year")
        assert result.empty

    def test_none_dataframe_returns_empty(self):
        result = filter_by_date_range(None, selected_range="1 year")
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_missing_date_column_returns_df_unchanged(self):
        """If date_col is absent, the function returns the DataFrame unchanged."""
        df = pd.DataFrame({"value": [1, 2, 3]})
        result = filter_by_date_range(df, date_col="date", selected_range="1 year")
        assert len(result) == 3, "Should return all rows when date column is missing"

    def test_all_nat_dates_returns_all_rows(self):
        """All-NaT date column: can't determine reference, return all rows."""
        df = pd.DataFrame({
            "date": pd.to_datetime([None, None, None]),
            "value": [1, 2, 3],
        })
        result = filter_by_date_range(df, selected_range="1 year")
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Test 4 — Filtering preserves expected rows
# ---------------------------------------------------------------------------

class TestFilteringPreservesExpectedRows:
    def _make_df(self):
        return pd.DataFrame({
            "date": pd.to_datetime([
                "2024-01-01",
                "2024-06-01",
                "2024-09-01",
                "2024-12-01",
                "2025-01-01",
            ]),
            "value": [1, 2, 3, 4, 5],
        })

    def test_6_months_includes_correct_rows(self):
        df = self._make_df()
        # max date is 2025-01-01; 6 months back = 2024-07-06
        result = filter_by_date_range(df, selected_range="6 months")
        dates = set(result["date"].dt.strftime("%Y-%m-%d"))
        assert "2025-01-01" in dates
        assert "2024-09-01" in dates
        assert "2024-12-01" in dates
        # 2024-06-01 is more than 180 days before 2025-01-01 → excluded
        assert "2024-06-01" not in dates
        assert "2024-01-01" not in dates

    def test_1_year_includes_correct_rows(self):
        df = self._make_df()
        # max is 2025-01-01; 1 year back = 2024-01-02 → excludes 2024-01-01
        result = filter_by_date_range(df, selected_range="1 year")
        dates = set(result["date"].dt.strftime("%Y-%m-%d"))
        assert "2025-01-01" in dates
        assert "2024-06-01" in dates
        assert "2024-09-01" in dates
        assert "2024-12-01" in dates
        assert "2024-01-01" not in dates

    def test_row_order_preserved(self):
        df = self._make_df()
        result = filter_by_date_range(df, selected_range="1 year")
        assert list(result["value"]) == sorted(result["value"]), (
            "Rows should remain in their original (ascending date) order."
        )

    def test_unrecognised_range_treated_as_max(self):
        df = self._make_df()
        result = filter_by_date_range(df, selected_range="unknown_option")
        assert len(result) == len(df), "Unrecognised range should return all rows (Max behaviour)"


# ---------------------------------------------------------------------------
# Test 5 — Dashboard import still works after adding the helper
# ---------------------------------------------------------------------------

class TestDashboardImportIntegrity:
    def test_date_filters_module_importable(self):
        """app.utils.date_filters must be importable with no side effects."""
        import importlib
        mod = importlib.import_module("app.utils.date_filters")
        assert hasattr(mod, "filter_by_date_range")
        assert hasattr(mod, "render_date_range_selector")
        assert hasattr(mod, "get_date_range_options")
        assert hasattr(mod, "DATE_RANGE_OPTIONS")

    def test_get_date_range_options_returns_correct_list(self):
        options = get_date_range_options()
        assert isinstance(options, list)
        assert "Max" in options
        assert "1 year" in options
        assert "1 week" in options
        assert options[-1] == "Max", "Max should be the last option"

    def test_historical_risk_module_importable(self):
        """Check that patched section modules compile cleanly."""
        import importlib
        mod = importlib.import_module("app.sections.historical_risk")
        assert hasattr(mod, "render_historical_risk_page")

    def test_water_balance_module_importable(self):
        import importlib
        mod = importlib.import_module("app.sections.water_balance")
        assert hasattr(mod, "render_water_balance_page")

    def test_vegetation_health_module_importable(self):
        import importlib
        mod = importlib.import_module("app.sections.vegetation_health")
        assert hasattr(mod, "render_vegetation_health_page")

    def test_combined_intelligence_module_importable(self):
        import importlib
        mod = importlib.import_module("app.sections.combined_intelligence")
        assert hasattr(mod, "render_combined_intelligence_page")

    def test_forecast_risk_module_importable(self):
        import importlib
        mod = importlib.import_module("app.sections.forecast_risk")
        assert hasattr(mod, "render_forecast_risk_page")

    def test_et0_validation_module_importable(self):
        import importlib
        mod = importlib.import_module("app.sections.et0_validation")
        assert hasattr(mod, "render_et0_validation_page")

    def test_fao56_comparison_module_importable(self):
        import importlib
        mod = importlib.import_module("app.sections.fao56_model_comparison")
        assert hasattr(mod, "render_fao56_model_comparison_page")
