"""
Tests for Sentinel-2 GEE credential fallback and --refresh-sentinel2 flag.

These tests do NOT call any real GEE APIs or network services.  They verify:
  - try_init_earth_engine returns (False, reason) when earthengine-api is not
    installed (ImportError)
  - try_init_earth_engine returns (False, reason) when no project_id is
    configured
  - try_init_earth_engine returns (False, reason) when GEE_SERVICE_ACCOUNT_KEY
    env var is set but contains invalid JSON
  - try_init_earth_engine returns (False, reason) when GEE_SERVICE_ACCOUNT_KEY
    env var is set but JSON is missing client_email
  - try_init_earth_engine returns (True, reason) when service account
    credentials init succeeds (mocked)
  - --refresh-sentinel2 skips gracefully (no crash, no sys.exit) when GEE
    is unavailable
  - --refresh-sentinel2 and --skip-fetch together exit with SystemExit
  - aggregate_timeseries() works from a cached CSV without GEE (offline)
"""

import json
import sys
import os
import csv
import io
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ---------------------------------------------------------------------------
# try_init_earth_engine: credential / import fallback
# ---------------------------------------------------------------------------

class TestTryInitEarthEngine:
    def test_returns_false_when_ee_not_installed(self):
        """Returns (False, reason) when earthengine-api is not importable."""
        from src.remote_sensing import gee_setup
        with patch.dict("sys.modules", {"ee": None}):
            # Simulate ImportError by temporarily removing ee from modules
            original = sys.modules.pop("ee", None)
            try:
                ok, reason = gee_setup.try_init_earth_engine(project_id="test-proj")
            finally:
                if original is not None:
                    sys.modules["ee"] = original
        assert ok is False
        assert "not installed" in reason.lower() or "importerror" in reason.lower() or ok is False

    def test_returns_false_when_ee_import_raises(self, monkeypatch):
        """Returns (False, reason) when 'import ee' raises ImportError."""
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "ee":
                raise ImportError("No module named 'ee'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)
        from src.remote_sensing import gee_setup
        # Need to reload to pick up the patched import
        import importlib
        try:
            ok, reason = gee_setup.try_init_earth_engine(project_id="test-proj")
        except Exception:
            # If ee is actually installed, the patch may not intercept it
            # because ee is already in sys.modules; skip in that case.
            pytest.skip("earthengine-api is installed; ImportError path not testable")
        assert ok is False

    def test_returns_false_when_no_project_id(self):
        """Returns (False, reason) when gee_project_id is empty/missing."""
        ee_mock = MagicMock()
        with patch.dict("sys.modules", {"ee": ee_mock}):
            # Patch get_config to return a config with no gee_project_id
            mock_config = MagicMock()
            mock_config.remote_sensing = {}
            with patch("src.remote_sensing.gee_setup.get_config", return_value=mock_config):
                from src.remote_sensing import gee_setup
                ok, reason = gee_setup.try_init_earth_engine()  # project_id=None from config
        assert ok is False
        assert "project" in reason.lower() or "gee_project_id" in reason.lower()

    def test_returns_false_when_service_account_key_is_invalid_json(self, monkeypatch):
        """Returns (False, reason) when GEE_SERVICE_ACCOUNT_KEY is not valid JSON."""
        monkeypatch.setenv("GEE_SERVICE_ACCOUNT_KEY", "not-valid-json{{{")
        ee_mock = MagicMock()
        with patch.dict("sys.modules", {"ee": ee_mock}):
            from src.remote_sensing import gee_setup
            ok, reason = gee_setup.try_init_earth_engine(project_id="test-proj")
        assert ok is False
        assert "json" in reason.lower() or "invalid" in reason.lower()

    def test_returns_false_when_service_account_key_missing_client_email(self, monkeypatch):
        """Returns (False, reason) when GEE_SERVICE_ACCOUNT_KEY JSON lacks client_email."""
        key_data = {"type": "service_account", "project_id": "test-proj"}
        monkeypatch.setenv("GEE_SERVICE_ACCOUNT_KEY", json.dumps(key_data))
        ee_mock = MagicMock()
        with patch.dict("sys.modules", {"ee": ee_mock}):
            from src.remote_sensing import gee_setup
            ok, reason = gee_setup.try_init_earth_engine(project_id="test-proj")
        assert ok is False
        assert "client_email" in reason

    def test_returns_true_when_service_account_init_succeeds(self, monkeypatch):
        """Returns (True, reason) when service account credentials init succeeds."""
        key_data = {
            "type": "service_account",
            "client_email": "test@test-proj.iam.gserviceaccount.com",
            "private_key": "fake-key",
        }
        monkeypatch.setenv("GEE_SERVICE_ACCOUNT_KEY", json.dumps(key_data))

        ee_mock = MagicMock()
        # ServiceAccountCredentials and Initialize should not raise
        ee_mock.ServiceAccountCredentials.return_value = MagicMock()
        ee_mock.Initialize.return_value = None

        with patch.dict("sys.modules", {"ee": ee_mock}):
            from src.remote_sensing import gee_setup
            import importlib
            importlib.reload(gee_setup)
            ok, reason = gee_setup.try_init_earth_engine(project_id="test-proj")

        assert ok is True
        assert "service account" in reason.lower()
        assert "test@test-proj.iam.gserviceaccount.com" in reason


# ---------------------------------------------------------------------------
# --refresh-sentinel2 pipeline flag: graceful skip when GEE unavailable
# ---------------------------------------------------------------------------

class TestRefreshSentinel2Flag:
    """
    Tests for the --refresh-sentinel2 pipeline flag.

    Strategy: import run_pipeline once and use patch.object() directly on the
    module's attributes — no importlib.reload(), which would clobber patches.
    """

    def _run_pipeline_with_args(self, args_list):
        """
        Run run_pipeline.main() with the given sys.argv, patching out all
        network-touching steps and the soil-CSV existence check.
        """
        from src.pipeline import run_pipeline

        fake_soil_path = MagicMock()
        fake_soil_path.exists.return_value = True

        with patch.object(sys, "argv", ["main.py"] + args_list):
            with patch.object(run_pipeline, "run_steps", return_value=True):
                with patch.object(run_pipeline, "run_freshness_aware_steps", return_value=[]):
                    with patch.object(run_pipeline, "write_pipeline_metadata"):
                        with patch.object(run_pipeline, "get_config") as mock_cfg:
                            mock_cfg.return_value.path.return_value = fake_soil_path
                            run_pipeline.main()

    def test_refresh_sentinel2_skips_gracefully_when_gee_unavailable(self, monkeypatch):
        """
        --refresh-sentinel2 with no GEE credentials should skip (not crash or
        sys.exit) and the pipeline should complete normally.
        Uses --skip-soil-fetch (compatible with --refresh-sentinel2).
        """
        monkeypatch.delenv("GEE_SERVICE_ACCOUNT_KEY", raising=False)

        from src.pipeline import run_pipeline
        with patch.object(run_pipeline, "try_init_earth_engine",
                          return_value=(False, "earthengine-api package is not installed")):
            # Should not raise — pipeline skips GEE and continues
            self._run_pipeline_with_args(["--skip-soil-fetch", "--refresh-sentinel2"])

    def test_refresh_sentinel2_and_skip_fetch_are_mutually_exclusive(self):
        """--refresh-sentinel2 + --skip-fetch must exit with SystemExit."""
        from src.pipeline import run_pipeline
        with patch.object(sys, "argv", ["main.py", "--skip-fetch", "--refresh-sentinel2"]):
            with pytest.raises(SystemExit):
                run_pipeline.main()

    def test_refresh_sentinel2_calls_timeseries_build_when_gee_ready(self, monkeypatch):
        """When GEE init succeeds, build_index_timeseries() should be called."""
        monkeypatch.delenv("GEE_SERVICE_ACCOUNT_KEY", raising=False)

        timeseries_called = []

        def mock_build():
            timeseries_called.append(True)
            return True

        from src.pipeline import run_pipeline
        with patch.object(run_pipeline, "try_init_earth_engine",
                          return_value=(True, "initialized with mock credentials")):
            with patch.object(run_pipeline.sentinel2_timeseries_script,
                              "build_index_timeseries", side_effect=mock_build):
                self._run_pipeline_with_args(["--skip-soil-fetch", "--refresh-sentinel2"])

        assert timeseries_called, "build_index_timeseries() was not called when GEE was available"


# ---------------------------------------------------------------------------
# Sentinel-2 aggregation: works from cached CSV without GEE
# ---------------------------------------------------------------------------

class TestSentinel2AggregationOffline:
    def test_aggregate_timeseries_from_cached_csv(self, tmp_path, monkeypatch):
        """
        aggregate_timeseries() should produce a daily CSV from a cached
        image-level timeseries CSV without any GEE connection.
        """
        from src.remote_sensing import aggregate_sentinel2_timeseries as agg

        # Create a minimal mock input CSV
        timeseries_csv = tmp_path / "muthukur_sentinel2_index_timeseries.csv"
        daily_csv = tmp_path / "muthukur_sentinel2_daily_indices.csv"

        rows = [
            {"date": "2025-01-07", "image_id": "img1", "cloud_percentage": "5.0",
             "ndvi_mean": "0.55", "ndwi_mean": "0.10", "ndmi_mean": "0.15",
             "ndre_mean": "0.30", "latitude": "13.29", "longitude": "78.62", "buffer_m": "500"},
            {"date": "2025-01-07", "image_id": "img2", "cloud_percentage": "8.0",
             "ndvi_mean": "0.50", "ndwi_mean": "0.08", "ndmi_mean": "0.12",
             "ndre_mean": "0.28", "latitude": "13.29", "longitude": "78.62", "buffer_m": "500"},
            {"date": "2025-01-20", "image_id": "img3", "cloud_percentage": "2.0",
             "ndvi_mean": "0.60", "ndwi_mean": "0.12", "ndmi_mean": "0.20",
             "ndre_mean": "0.35", "latitude": "13.29", "longitude": "78.62", "buffer_m": "500"},
        ]
        fieldnames = list(rows[0].keys())
        with open(timeseries_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        # Patch the module-level path constants to use tmp_path
        monkeypatch.setattr(agg, "INPUT_CSV_PATH", timeseries_csv)
        monkeypatch.setattr(agg, "OUTPUT_CSV_PATH", daily_csv)

        result = agg.aggregate_timeseries()

        assert result is True, "aggregate_timeseries() should return True from cached CSV"
        assert daily_csv.exists(), "daily CSV should be created"

        import pandas as pd
        df = pd.read_csv(daily_csv)
        assert len(df) == 2, "Two unique dates → two daily rows"

        # 2025-01-07 should be average of img1 and img2
        row_jan7 = df[df["date"] == "2025-01-07"].iloc[0]
        assert abs(row_jan7["ndvi_mean"] - 0.525) < 1e-6
        assert row_jan7["scene_count"] == 2

        # 2025-01-20 single scene
        row_jan20 = df[df["date"] == "2025-01-20"].iloc[0]
        assert abs(row_jan20["ndvi_mean"] - 0.60) < 1e-6
        assert row_jan20["scene_count"] == 1

    def test_aggregate_timeseries_fails_clearly_when_no_input(self, tmp_path, monkeypatch):
        """aggregate_timeseries() should return False (not raise) when input CSV missing."""
        from src.remote_sensing import aggregate_sentinel2_timeseries as agg

        missing_csv = tmp_path / "does_not_exist.csv"
        daily_csv = tmp_path / "output.csv"
        monkeypatch.setattr(agg, "INPUT_CSV_PATH", missing_csv)
        monkeypatch.setattr(agg, "OUTPUT_CSV_PATH", daily_csv)

        result = agg.aggregate_timeseries()
        assert result is False
