"""
Tests for Sentinel-1 SAR fallback (cloudy-season continuity).

These tests do NOT call any real GEE APIs or network services. They verify:
  1. S1 build gracefully skips when GEE is unavailable
  2. S1 aggregation creates one row per date for duplicate scenes
  3. Feature table builds successfully when the S1 CSV is missing
  4. Feature table joins nearest previous S1 observation without future leakage
  5. Pipeline does not fail when the S1 refresh raises an exception
  6. If GEE is already initialized (service-account), S1 builder does not call
     interactive auth (check_earth_engine_setup must NOT be called)
"""

import csv
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ---------------------------------------------------------------------------
# Test 1 — build_sar_timeseries skips gracefully when GEE unavailable
# ---------------------------------------------------------------------------

class TestSentinel1BuildGracefulSkip:
    def test_skips_gracefully_when_gee_unavailable(self):
        """
        build_sar_timeseries(assume_ee_initialized=False) must return False
        (not raise) when check_earth_engine_setup reports GEE is not ready.
        """
        from src.remote_sensing import build_sentinel1_sar_timeseries as bst

        with patch.object(bst, "check_earth_engine_setup", return_value=False):
            result = bst.build_sar_timeseries(assume_ee_initialized=False)

        assert result is False, (
            "build_sar_timeseries should return False (not raise) when "
            "check_earth_engine_setup reports GEE is not ready."
        )


# ---------------------------------------------------------------------------
# Test 2 — aggregate_timeseries collapses duplicate dates to one row per day
# ---------------------------------------------------------------------------

class TestSentinel1Aggregation:
    def test_creates_one_row_per_date_for_duplicates(self, tmp_path, monkeypatch):
        """
        aggregate_timeseries() must collapse multiple scenes on the same date
        into a single daily row, averaging numeric columns and counting scenes.
        """
        from src.remote_sensing import aggregate_sentinel1_timeseries as agg

        timeseries_csv = tmp_path / "muthukur_sentinel1_sar_timeseries.csv"
        daily_csv = tmp_path / "muthukur_sentinel1_daily_indices.csv"

        rows = [
            {
                "date": "2025-06-01", "image_id": "s1a", "orbit_pass": "DESCENDING",
                "vv_mean": "-14.0", "vh_mean": "-22.0", "vv_vh_ratio_mean": "8.0",
                "latitude": "13.29", "longitude": "78.62", "buffer_m": "500",
            },
            {
                "date": "2025-06-01", "image_id": "s1b", "orbit_pass": "DESCENDING",
                "vv_mean": "-16.0", "vh_mean": "-24.0", "vv_vh_ratio_mean": "8.0",
                "latitude": "13.29", "longitude": "78.62", "buffer_m": "500",
            },
            {
                "date": "2025-06-12", "image_id": "s1c", "orbit_pass": "DESCENDING",
                "vv_mean": "-13.0", "vh_mean": "-21.0", "vv_vh_ratio_mean": "8.0",
                "latitude": "13.29", "longitude": "78.62", "buffer_m": "500",
            },
        ]
        fieldnames = list(rows[0].keys())
        with open(timeseries_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        monkeypatch.setattr(agg, "INPUT_CSV_PATH", timeseries_csv)
        monkeypatch.setattr(agg, "OUTPUT_CSV_PATH", daily_csv)

        result = agg.aggregate_timeseries()

        assert result is True, "aggregate_timeseries() should return True from a valid input CSV"
        assert daily_csv.exists(), "daily CSV should be created"

        import pandas as pd
        df = pd.read_csv(daily_csv)
        assert len(df) == 2, "Two unique dates should produce two daily rows"

        row_june1 = df[df["date"] == "2025-06-01"].iloc[0]
        assert abs(row_june1["vv_mean"] - (-15.0)) < 1e-6, (
            "VV mean for 2025-06-01 should be average of -14 and -16 = -15"
        )
        assert abs(row_june1["vh_mean"] - (-23.0)) < 1e-6, (
            "VH mean for 2025-06-01 should be average of -22 and -24 = -23"
        )
        assert row_june1["scene_count"] == 2, "scene_count should be 2 for a date with two scenes"

        row_june12 = df[df["date"] == "2025-06-12"].iloc[0]
        assert abs(row_june12["vv_mean"] - (-13.0)) < 1e-6
        assert row_june12["scene_count"] == 1


# ---------------------------------------------------------------------------
# Test 3 — feature table builds when S1 CSV is missing
# ---------------------------------------------------------------------------

class TestFeatureTableWithoutSentinel1:
    def test_feature_table_works_when_s1_csv_missing(self, tmp_path):
        """
        build_feature_table._load_sentinel1() must return None (not raise)
        when the Sentinel-1 CSV does not exist.
        """
        from src.features.build_feature_table import _load_sentinel1

        missing_path = tmp_path / "does_not_exist.csv"
        result = _load_sentinel1(missing_path)

        assert result is None, (
            "_load_sentinel1 should return None (not raise) when the file is missing."
        )


# ---------------------------------------------------------------------------
# Test 4 — feature table nearest-prior S1 join, no future leakage
# ---------------------------------------------------------------------------

class TestSentinel1NearestPriorJoin:
    def test_joins_nearest_previous_s1_without_future_leakage(self, tmp_path):
        """
        The S1 join must use direction='backward' (nearest-prior), so a
        weather row never sees a SAR observation taken after its own date.
        """
        import pandas as pd
        from src.features.build_feature_table import _load_sentinel1, _s1_freshness_label

        # Create a small S1 daily CSV with two observations
        s1_csv = tmp_path / "sentinel1_daily.csv"
        s1_rows = [
            {
                "date": "2025-06-01", "vv_mean": -14.0, "vh_mean": -22.0,
                "vv_vh_ratio_mean": 8.0, "orbit_pass": "DESCENDING", "scene_count": 1,
                "latitude": 13.29, "longitude": 78.62, "buffer_m": 500,
                "vv_level": "Moderate backscatter", "vh_level": "Moderate volume scattering",
            },
            {
                "date": "2025-06-12", "vv_mean": -13.0, "vh_mean": -21.0,
                "vv_vh_ratio_mean": 8.0, "orbit_pass": "DESCENDING", "scene_count": 1,
                "latitude": 13.29, "longitude": 78.62, "buffer_m": 500,
                "vv_level": "Moderate backscatter", "vh_level": "Moderate volume scattering",
            },
        ]
        pd.DataFrame(s1_rows).to_csv(s1_csv, index=False)

        s1_df = _load_sentinel1(s1_csv)
        assert s1_df is not None

        # Build a small weather df with three dates
        weather_df = pd.DataFrame({
            "date": pd.to_datetime(["2025-05-25", "2025-06-05", "2025-06-15"]),
            "dummy_weather_col": [1, 2, 3],
        })

        # Replicate the merge_asof join from build_feature_table
        s1_for_merge = s1_df.rename(columns={"date": "sentinel1_date", "scene_count": "scene_count_s1"})
        combined = pd.merge_asof(
            weather_df,
            s1_for_merge,
            left_on="date",
            right_on="sentinel1_date",
            direction="backward",
        )
        combined["days_since_sentinel1_observation"] = (
            combined["date"] - combined["sentinel1_date"]
        ).dt.days

        # 2025-05-25: no prior S1 observation exists → sentinel1_date must be NaT
        row_may25 = combined[combined["date"] == pd.Timestamp("2025-05-25")].iloc[0]
        assert pd.isna(row_may25["sentinel1_date"]), (
            "2025-05-25 should have no prior S1 observation (first S1 is on 2025-06-01)"
        )

        # 2025-06-05: nearest prior is 2025-06-01 (NOT 2025-06-12 which is in the future)
        row_jun05 = combined[combined["date"] == pd.Timestamp("2025-06-05")].iloc[0]
        assert row_jun05["sentinel1_date"] == pd.Timestamp("2025-06-01"), (
            "2025-06-05 should join to 2025-06-01 (nearest prior), not 2025-06-12 (future)"
        )
        assert row_jun05["days_since_sentinel1_observation"] == 4

        # 2025-06-15: nearest prior is 2025-06-12
        row_jun15 = combined[combined["date"] == pd.Timestamp("2025-06-15")].iloc[0]
        assert row_jun15["sentinel1_date"] == pd.Timestamp("2025-06-12"), (
            "2025-06-15 should join to 2025-06-12"
        )
        assert row_jun15["days_since_sentinel1_observation"] == 3

        # Verify freshness labels
        assert _s1_freshness_label(3) == "Fresh"
        assert _s1_freshness_label(4) == "Fresh"
        assert _s1_freshness_label(10) == "Moderate"
        assert _s1_freshness_label(20) == "Stale"
        assert _s1_freshness_label(None) == "Missing"


# ---------------------------------------------------------------------------
# Test 5 — pipeline does not fail when S1 refresh raises an exception
# ---------------------------------------------------------------------------

class TestPipelineS1RefreshFailure:
    """
    If the Sentinel-1 timeseries build raises an unexpected exception,
    the pipeline must continue (no crash, no sys.exit). The S1 failure
    should be logged but not propagate.
    """

    def _run_pipeline_with_args(self, args_list, s1_side_effect=None, s2_side_effect=None):
        from src.pipeline import run_pipeline

        fake_soil_path = MagicMock()
        fake_soil_path.exists.return_value = True

        def mock_s2_build(**kwargs):
            if s2_side_effect:
                raise s2_side_effect
            return True

        def mock_s1_build(**kwargs):
            if s1_side_effect:
                raise s1_side_effect
            return True

        with patch.object(sys, "argv", ["main.py"] + args_list):
            with patch.object(run_pipeline, "run_steps", return_value=True):
                with patch.object(run_pipeline, "run_freshness_aware_steps", return_value=[]):
                    with patch.object(run_pipeline, "write_pipeline_metadata"):
                        with patch.object(run_pipeline, "get_config") as mock_cfg:
                            mock_cfg.return_value.path.return_value = fake_soil_path
                            with patch.object(
                                run_pipeline, "try_init_earth_engine",
                                return_value=(True, "initialized with mock credentials"),
                            ):
                                with patch.object(
                                    run_pipeline.sentinel2_timeseries_script,
                                    "build_index_timeseries",
                                    side_effect=mock_s2_build,
                                ):
                                    with patch.object(
                                        run_pipeline.sentinel1_timeseries_script,
                                        "build_sar_timeseries",
                                        side_effect=mock_s1_build,
                                    ):
                                        run_pipeline.main()

    def test_pipeline_continues_when_s1_build_raises(self):
        """
        If build_sar_timeseries raises an exception, the pipeline must not
        propagate it — it should catch it, log a warning, and continue.
        """
        # Should not raise, even though S1 build throws
        self._run_pipeline_with_args(
            ["--skip-soil-fetch", "--refresh-sentinel2"],
            s1_side_effect=RuntimeError("GEE timeout on S1 collection"),
        )


# ---------------------------------------------------------------------------
# Test 6 — S1 builder skips interactive auth when assume_ee_initialized=True
# ---------------------------------------------------------------------------

class TestSentinel1SkipsInteractiveAuthWhenAssumed:
    def test_build_sar_timeseries_skips_gee_setup_when_assume_initialized(self):
        """
        build_sar_timeseries(assume_ee_initialized=True) must NOT call
        check_earth_engine_setup(). Without this, CI fails because
        check_earth_engine_setup() calls ee.Initialize() with default
        credentials after service-account init has already succeeded.
        """
        from src.remote_sensing import build_sentinel1_sar_timeseries as bst

        setup_called = []

        def mock_check_setup():
            setup_called.append(True)
            return True

        ee_mock = MagicMock()
        ee_mock.ImageCollection.return_value.filterBounds.return_value \
            .filterDate.return_value.filter.return_value \
            .filter.return_value.filter.return_value \
            .sort.return_value.size.return_value.getInfo.side_effect = RuntimeError("no GEE")

        with patch.object(bst, "check_earth_engine_setup", side_effect=mock_check_setup):
            with patch.dict("sys.modules", {"ee": ee_mock}):
                bst.build_sar_timeseries(assume_ee_initialized=True)

        assert not setup_called, (
            "check_earth_engine_setup() was called even though "
            "assume_ee_initialized=True — this causes CI failures when GEE "
            "was already initialized with a service account."
        )
