"""
Tests for src/validation/compare_et0_openmeteo_vs_fao56.py

Covers:
  - Normal overlap: returns merged CSV with expected columns and statistics
  - No overlap: returns empty CSV and summary without crashing
  - Missing open_meteo_et0_mm column: handled gracefully, returns empty CSV
  - Missing date column: handled gracefully, returns empty CSV
  - Missing input files: handled gracefully, returns empty CSV
  - Correlation computed only when enough rows exist
  - difference_mm_day = open_meteo - fao56

All tests use temporary in-memory DataFrames written to tmp_path fixtures.
No real pipeline CSVs are read.
"""

import textwrap
from pathlib import Path

import pandas as pd
import pytest

from src.validation.compare_et0_openmeteo_vs_fao56 import build_et0_comparison


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_open_meteo(tmp_path: Path, rows: list[dict]) -> Path:
    df = pd.DataFrame(rows)
    p = tmp_path / "open_meteo.csv"
    df.to_csv(p, index=False)
    return p


def _write_fao56_wb(tmp_path: Path, rows: list[dict]) -> Path:
    df = pd.DataFrame(rows)
    p = tmp_path / "fao56_wb.csv"
    df.to_csv(p, index=False)
    return p


def _build(tmp_path: Path, om_path, wb_path):
    """Call build_et0_comparison with explicit paths and tmp output paths."""
    csv_out = tmp_path / "et0_comparison.csv"
    md_out = tmp_path / "et0_summary.md"
    build_et0_comparison(
        open_meteo_path=om_path,
        fao56_wb_path=wb_path,
        output_csv_path=csv_out,
        output_summary_path=md_out,
    )
    return csv_out, md_out


# ---------------------------------------------------------------------------
# Tests: normal overlap
# ---------------------------------------------------------------------------

class TestNormalOverlap:
    """Two sources with 5 overlapping days."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        om_rows = [
            {"date": "2025-06-01", "openmeteo_et0_mm": 5.0},
            {"date": "2025-06-02", "openmeteo_et0_mm": 6.0},
            {"date": "2025-06-03", "openmeteo_et0_mm": 4.5},
            {"date": "2025-06-04", "openmeteo_et0_mm": 5.5},
            {"date": "2025-06-05", "openmeteo_et0_mm": 7.0},
        ]
        wb_rows = [
            {"date": "2025-06-01", "et0_mm": 4.8},
            {"date": "2025-06-02", "et0_mm": 5.5},
            {"date": "2025-06-03", "et0_mm": 4.2},
            {"date": "2025-06-04", "et0_mm": 5.0},
            {"date": "2025-06-05", "et0_mm": 6.8},
            # extra FAO-56 only date (should not appear in output)
            {"date": "2025-05-31", "et0_mm": 3.0},
        ]
        om_path = _write_open_meteo(tmp_path, om_rows)
        wb_path = _write_fao56_wb(tmp_path, wb_rows)
        self.csv_out, self.md_out = _build(tmp_path, om_path, wb_path)
        self.df = pd.read_csv(self.csv_out)

    def test_output_csv_exists(self):
        assert self.csv_out.exists()

    def test_output_md_exists(self):
        assert self.md_out.exists()

    def test_row_count_equals_overlap(self):
        assert len(self.df) == 5

    def test_expected_columns(self):
        for col in [
            "date",
            "open_meteo_et0_mm_day",
            "fao56_et0_mm_day",
            "difference_mm_day",
            "absolute_difference_mm_day",
        ]:
            assert col in self.df.columns, f"Missing column: {col}"

    def test_difference_sign(self):
        # difference = open_meteo - fao56
        row = self.df[self.df["date"] == "2025-06-01"].iloc[0]
        expected_diff = round(5.0 - 4.8, 4)
        assert abs(row["difference_mm_day"] - expected_diff) < 1e-3

    def test_absolute_difference_non_negative(self):
        assert (self.df["absolute_difference_mm_day"] >= 0).all()

    def test_summary_contains_matched_days(self):
        text = self.md_out.read_text(encoding="utf-8")
        assert "5" in text
        assert "Matched days" in text or "matched days" in text.lower()

    def test_summary_contains_no_overlap_section_absent(self):
        text = self.md_out.read_text(encoding="utf-8")
        assert "No overlapping dates" not in text

    def test_correlation_in_summary_when_enough_rows(self):
        text = self.md_out.read_text(encoding="utf-8")
        assert "correlation" in text.lower()


# ---------------------------------------------------------------------------
# Tests: no overlapping dates
# ---------------------------------------------------------------------------

class TestNoOverlap:
    """Open-Meteo has future dates; FAO-56 has past dates — no intersection."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        om_rows = [
            {"date": "2026-07-01", "openmeteo_et0_mm": 5.0},
            {"date": "2026-07-02", "openmeteo_et0_mm": 5.5},
        ]
        wb_rows = [
            {"date": "2025-01-01", "et0_mm": 3.0},
            {"date": "2025-01-02", "et0_mm": 3.2},
        ]
        om_path = _write_open_meteo(tmp_path, om_rows)
        wb_path = _write_fao56_wb(tmp_path, wb_rows)
        self.csv_out, self.md_out = _build(tmp_path, om_path, wb_path)
        self.df = pd.read_csv(self.csv_out)

    def test_output_csv_exists_and_empty(self):
        assert self.csv_out.exists()
        assert len(self.df) == 0

    def test_output_md_exists(self):
        assert self.md_out.exists()

    def test_summary_reports_no_overlap(self):
        text = self.md_out.read_text(encoding="utf-8")
        assert "No overlapping dates" in text

    def test_does_not_crash(self):
        # Reaching this line means no exception was raised
        assert True


# ---------------------------------------------------------------------------
# Tests: missing ET0 column in Open-Meteo CSV
# ---------------------------------------------------------------------------

class TestMissingOpenMeteoEt0Column:
    """Open-Meteo CSV exists but lacks openmeteo_et0_mm."""

    def test_graceful_fallback_to_empty_csv(self, tmp_path):
        om_rows = [{"date": "2025-06-01", "some_other_col": 5.0}]
        wb_rows = [{"date": "2025-06-01", "et0_mm": 4.8}]
        om_path = _write_open_meteo(tmp_path, om_rows)
        wb_path = _write_fao56_wb(tmp_path, wb_rows)
        csv_out, _ = _build(tmp_path, om_path, wb_path)
        df = pd.read_csv(csv_out)
        assert len(df) == 0  # no data but no crash


# ---------------------------------------------------------------------------
# Tests: missing date column in FAO-56 CSV
# ---------------------------------------------------------------------------

class TestMissingFao56DateColumn:
    """FAO-56 CSV lacks date column."""

    def test_graceful_fallback_to_empty_csv(self, tmp_path):
        om_rows = [{"date": "2025-06-01", "openmeteo_et0_mm": 5.0}]
        wb_rows = [{"no_date_col": "2025-06-01", "et0_mm": 4.8}]
        om_path = _write_open_meteo(tmp_path, om_rows)
        wb_path = _write_fao56_wb(tmp_path, wb_rows)
        csv_out, _ = _build(tmp_path, om_path, wb_path)
        df = pd.read_csv(csv_out)
        assert len(df) == 0


# ---------------------------------------------------------------------------
# Tests: missing input files
# ---------------------------------------------------------------------------

class TestMissingInputFiles:
    def test_missing_open_meteo_file(self, tmp_path):
        wb_rows = [{"date": "2025-06-01", "et0_mm": 4.8}]
        wb_path = _write_fao56_wb(tmp_path, wb_rows)
        om_path = tmp_path / "nonexistent_open_meteo.csv"
        csv_out, md_out = _build(tmp_path, om_path, wb_path)
        assert csv_out.exists()
        df = pd.read_csv(csv_out)
        assert len(df) == 0
        assert md_out.exists()

    def test_missing_fao56_file(self, tmp_path):
        om_rows = [{"date": "2025-06-01", "openmeteo_et0_mm": 5.0}]
        om_path = _write_open_meteo(tmp_path, om_rows)
        wb_path = tmp_path / "nonexistent_fao56.csv"
        csv_out, md_out = _build(tmp_path, om_path, wb_path)
        assert csv_out.exists()
        df = pd.read_csv(csv_out)
        assert len(df) == 0
        assert md_out.exists()

    def test_both_files_missing(self, tmp_path):
        om_path = tmp_path / "nonexistent_om.csv"
        wb_path = tmp_path / "nonexistent_wb.csv"
        csv_out, md_out = _build(tmp_path, om_path, wb_path)
        assert csv_out.exists()
        assert md_out.exists()


# ---------------------------------------------------------------------------
# Tests: partial overlap (only some dates match)
# ---------------------------------------------------------------------------

class TestPartialOverlap:
    def test_only_overlapping_dates_included(self, tmp_path):
        om_rows = [
            {"date": "2025-06-01", "openmeteo_et0_mm": 5.0},
            {"date": "2025-06-02", "openmeteo_et0_mm": 6.0},
            {"date": "2025-07-01", "openmeteo_et0_mm": 7.0},  # no match
        ]
        wb_rows = [
            {"date": "2025-06-01", "et0_mm": 4.8},
            {"date": "2025-06-02", "et0_mm": 5.5},
            {"date": "2025-05-15", "et0_mm": 3.0},  # no match
        ]
        om_path = _write_open_meteo(tmp_path, om_rows)
        wb_path = _write_fao56_wb(tmp_path, wb_rows)
        csv_out, _ = _build(tmp_path, om_path, wb_path)
        df = pd.read_csv(csv_out)
        assert len(df) == 2
        dates = set(df["date"])
        assert "2025-06-01" in dates
        assert "2025-06-02" in dates
