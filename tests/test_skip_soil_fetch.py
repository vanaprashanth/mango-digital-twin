"""
Tests for the --skip-soil-fetch pipeline flag.

These tests do NOT call any real network APIs and do NOT run the full
pipeline. They only verify:
  - SKIP_SOIL_STEPS contains the expected steps (no SoilGrids, has weather)
  - PIPELINE_STEPS contains SoilGrids
  - The no-cache guard fires with SystemExit when no soil CSV exists
  - The no-cache guard does NOT fire when a soil CSV exists
  - --skip-fetch and --skip-soil-fetch together are rejected
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the project root is on sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ---------------------------------------------------------------------------
# Step list membership
# ---------------------------------------------------------------------------

class TestStepLists:
    def test_full_pipeline_includes_soilgrids(self):
        from src.pipeline.run_pipeline import PIPELINE_STEPS
        names = [name for name, _ in PIPELINE_STEPS]
        assert "SoilGrids soil intelligence" in names

    def test_skip_soil_steps_excludes_soilgrids(self):
        from src.pipeline.run_pipeline import SKIP_SOIL_STEPS
        names = [name for name, _ in SKIP_SOIL_STEPS]
        assert "SoilGrids soil intelligence" not in names

    def test_skip_soil_steps_includes_nasa_power(self):
        from src.pipeline.run_pipeline import SKIP_SOIL_STEPS
        names = [name for name, _ in SKIP_SOIL_STEPS]
        assert "NASA POWER historical weather" in names

    def test_skip_soil_steps_includes_open_meteo(self):
        from src.pipeline.run_pipeline import SKIP_SOIL_STEPS
        names = [name for name, _ in SKIP_SOIL_STEPS]
        assert "Open-Meteo recent/forecast weather" in names

    def test_skip_soil_steps_includes_both_risk_engines(self):
        from src.pipeline.run_pipeline import SKIP_SOIL_STEPS
        names = [name for name, _ in SKIP_SOIL_STEPS]
        assert "Historical mango risk engine" in names
        assert "Forecast mango risk engine" in names

    def test_risk_only_steps_excludes_soilgrids(self):
        from src.pipeline.run_pipeline import RISK_ONLY_STEPS
        names = [name for name, _ in RISK_ONLY_STEPS]
        assert "SoilGrids soil intelligence" not in names
        assert "NASA POWER historical weather" not in names


# ---------------------------------------------------------------------------
# No-cache guard: SystemExit when soil CSV is missing
# ---------------------------------------------------------------------------

class TestNoCacheGuard:
    def test_exits_when_no_cached_soil_csv(self, tmp_path):
        """--skip-soil-fetch must fail clearly when no cached CSV exists."""
        from src.pipeline.run_pipeline import main

        # Point config at a temp dir that has no soil CSV
        fake_config = MagicMock()
        fake_config.path.return_value = tmp_path / "missing_soilgrids.csv"

        with patch("src.pipeline.run_pipeline.get_config", return_value=fake_config):
            with patch("sys.argv", ["run_pipeline.py", "--skip-soil-fetch"]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
        assert exc_info.value.code != 0

    def test_does_not_exit_when_cached_soil_csv_exists(self, tmp_path):
        """--skip-soil-fetch must not exit early when the cached CSV exists."""
        from src.pipeline.run_pipeline import main

        # Create a dummy soil CSV
        soil_csv = tmp_path / "soilgrids.csv"
        soil_csv.write_text("sand,silt,clay\n30,30,40\n")

        fake_config = MagicMock()
        fake_config.path.return_value = soil_csv

        # We only want to test the guard, not run the real pipeline steps.
        # Patch run_steps to return True immediately and run_freshness_aware_steps
        # to return an empty list, and write_pipeline_metadata to no-op.
        with patch("src.pipeline.run_pipeline.get_config", return_value=fake_config):
            with patch("src.pipeline.run_pipeline.run_steps", return_value=True):
                with patch("src.pipeline.run_pipeline.run_freshness_aware_steps", return_value=[]):
                    with patch("src.pipeline.run_pipeline.write_pipeline_metadata"):
                        with patch("sys.argv", ["run_pipeline.py", "--skip-soil-fetch"]):
                            # Should not raise SystemExit
                            main()

    def test_both_flags_together_are_rejected(self):
        """--skip-fetch and --skip-soil-fetch together must be rejected."""
        from src.pipeline.run_pipeline import main

        with patch("sys.argv", ["run_pipeline.py", "--skip-fetch", "--skip-soil-fetch"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# Open-Meteo cached fallback in fetch_open_meteo.py
# ---------------------------------------------------------------------------

class TestOpenMeteoCachedFallback:
    """
    Tests for the cached-CSV fallback in fetch_open_meteo.main().
    No real network calls are made.
    """

    def test_returns_without_raising_when_cached_csv_exists(self, tmp_path):
        """
        If the fetch fails but a cached CSV exists, main() should log a
        warning and return without raising.
        """
        import pandas as pd
        from unittest.mock import patch, MagicMock
        from src.weather.fetch_open_meteo import main as open_meteo_main

        # Write a minimal cached CSV
        cached_csv = tmp_path / "open_meteo.csv"
        df = pd.DataFrame({"date": ["2026-01-01"], "openmeteo_temperature_avg_c": [25.0]})
        df.to_csv(cached_csv, index=False)

        fake_config = MagicMock()
        fake_config.path.return_value = cached_csv
        fake_config.latitude = 13.3
        fake_config.longitude = 78.6
        fake_config.study_area.name = "Test"
        fake_config.study_area.district = "Test"
        fake_config.forecast_weather = {"past_days": 7, "forecast_days": 7, "timezone": "UTC"}

        def raise_timeout(*args, **kwargs):
            raise RuntimeError("Simulated Open-Meteo timeout")

        with patch("src.weather.fetch_open_meteo.get_config", return_value=fake_config):
            with patch("src.weather.fetch_open_meteo.fetch_open_meteo_weather", side_effect=raise_timeout):
                # Should NOT raise — cached CSV exists
                open_meteo_main()

    def test_raises_when_no_cached_csv_and_fetch_fails(self, tmp_path):
        """
        If the fetch fails and no cached CSV exists, main() must re-raise.
        """
        from unittest.mock import patch, MagicMock
        from src.weather.fetch_open_meteo import main as open_meteo_main

        missing_csv = tmp_path / "missing_open_meteo.csv"

        fake_config = MagicMock()
        fake_config.path.return_value = missing_csv
        fake_config.latitude = 13.3
        fake_config.longitude = 78.6
        fake_config.study_area.name = "Test"
        fake_config.study_area.district = "Test"
        fake_config.forecast_weather = {"past_days": 7, "forecast_days": 7, "timezone": "UTC"}

        def raise_timeout(*args, **kwargs):
            raise RuntimeError("Simulated Open-Meteo timeout")

        with patch("src.weather.fetch_open_meteo.get_config", return_value=fake_config):
            with patch("src.weather.fetch_open_meteo.fetch_open_meteo_weather", side_effect=raise_timeout):
                with pytest.raises(RuntimeError, match="Simulated Open-Meteo timeout"):
                    open_meteo_main()
