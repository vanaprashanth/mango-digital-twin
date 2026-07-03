"""
Tests for app/sections/freshness.py

Covers the pure helper logic (no Streamlit rendering):
  - _latest_date_in_df: extracts correct latest date from a DataFrame
  - _latest_date_in_df: returns None for empty DataFrame
  - _latest_date_in_df: returns None when no 'date' column
  - _latest_date_in_df: ignores None/NaT values
  - _parse_iso: parses valid ISO timestamps
  - _parse_iso: returns None for None or malformed strings

We do NOT test the Streamlit rendering functions (show_freshness_indicator)
because they require a running Streamlit context.  The pure helpers are
imported directly and tested in isolation.
"""

import datetime as dt

import pandas as pd
import pytest

from app.sections.freshness import _latest_date_in_df, _parse_iso


# ---------------------------------------------------------------------------
# Tests: _latest_date_in_df
# ---------------------------------------------------------------------------

class TestLatestDateInDf:

    def test_returns_max_date_from_date_column(self):
        df = pd.DataFrame({
            "date": ["2025-01-01", "2025-06-15", "2025-03-10"],
            "value": [1, 2, 3],
        })
        result = _latest_date_in_df(df)
        assert result == dt.date(2025, 6, 15)

    def test_returns_none_for_none_dataframe(self):
        assert _latest_date_in_df(None) is None

    def test_returns_none_for_empty_dataframe(self):
        df = pd.DataFrame({"date": []})
        assert _latest_date_in_df(df) is None

    def test_returns_none_when_no_date_column(self):
        df = pd.DataFrame({"value": [1, 2, 3]})
        assert _latest_date_in_df(df) is None

    def test_ignores_nat_values(self):
        df = pd.DataFrame({
            "date": ["2025-01-01", None, "2025-06-01"],
            "value": [1, 2, 3],
        })
        result = _latest_date_in_df(df)
        assert result == dt.date(2025, 6, 1)

    def test_returns_none_when_all_dates_unparseable(self):
        df = pd.DataFrame({"date": ["not-a-date", "also-not-a-date"]})
        assert _latest_date_in_df(df) is None

    def test_handles_already_parsed_datetime_column(self):
        df = pd.DataFrame({
            "date": pd.to_datetime(["2025-02-01", "2025-08-31"]),
        })
        result = _latest_date_in_df(df)
        assert result == dt.date(2025, 8, 31)

    def test_single_row_dataframe(self):
        df = pd.DataFrame({"date": ["2025-12-31"]})
        assert _latest_date_in_df(df) == dt.date(2025, 12, 31)

    def test_dataframe_with_extra_columns(self):
        df = pd.DataFrame({
            "date": ["2025-01-10", "2025-07-04"],
            "rainfall_mm": [5.0, 0.0],
            "temperature_c": [28.0, 32.0],
        })
        assert _latest_date_in_df(df) == dt.date(2025, 7, 4)


# ---------------------------------------------------------------------------
# Tests: _parse_iso
# ---------------------------------------------------------------------------

class TestParseIso:

    def test_parses_valid_utc_timestamp(self):
        result = _parse_iso("2026-06-01T10:30:00Z")
        assert result == dt.datetime(2026, 6, 1, 10, 30, 0)

    def test_returns_none_for_none(self):
        assert _parse_iso(None) is None

    def test_returns_none_for_empty_string(self):
        assert _parse_iso("") is None

    def test_returns_none_for_malformed_string(self):
        assert _parse_iso("not-a-timestamp") is None

    def test_returns_none_for_wrong_format(self):
        # ISO with milliseconds — not the format we expect from metadata
        assert _parse_iso("2026-06-01T10:30:00.000Z") is None

    def test_midnight(self):
        result = _parse_iso("2025-01-01T00:00:00Z")
        assert result == dt.datetime(2025, 1, 1, 0, 0, 0)
