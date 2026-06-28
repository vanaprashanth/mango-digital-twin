"""
Single pipeline runner for the Sensor-Free Mango Digital Twin.

Runs every data fetcher and risk engine in the correct dependency order:

  1. NASA POWER historical weather       -> src/weather/fetch_weather.py
  2. SoilGrids soil intelligence         -> src/soil/fetch_soilgrids.py
  3. Historical mango risk engine        -> src/risk/historical_risk_engine.py
  4. Open-Meteo recent/forecast weather  -> src/weather/fetch_open_meteo.py
  5. Forecast mango risk engine          -> src/risk/open_meteo_risk_engine.py

Steps 1+2 must finish before step 3 (the historical risk engine needs both
raw weather and soil data). Step 4 must finish before step 5. Step 2 also
feeds step 5, since the forecast engine applies the same soil-adjusted
irrigation factor.

Usage:
    python src/pipeline/run_pipeline.py
    python src/pipeline/run_pipeline.py --skip-fetch   # reuse cached raw data, just recompute risk
"""

import argparse
import sys
import time
import traceback
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.weather import fetch_weather, fetch_open_meteo
from src.soil import fetch_soilgrids
from src.risk import historical_risk_engine, open_meteo_risk_engine
from src.utils.logger import get_logger

log = get_logger(__name__)


PIPELINE_STEPS = [
    ("NASA POWER historical weather", fetch_weather.main),
    ("SoilGrids soil intelligence", fetch_soilgrids.main),
    ("Historical mango risk engine", historical_risk_engine.main),
    ("Open-Meteo recent/forecast weather", fetch_open_meteo.main),
    ("Forecast mango risk engine", open_meteo_risk_engine.main),
]

RISK_ONLY_STEPS = [
    ("Historical mango risk engine", historical_risk_engine.main),
    ("Forecast mango risk engine", open_meteo_risk_engine.main),
]


def run_steps(steps: list[tuple[str, callable]]) -> bool:
    """Run pipeline steps in order. Stop and report on the first failure."""

    for step_number, (step_name, step_fn) in enumerate(steps, start=1):
        print("=" * 70)
        print(f"Step {step_number}/{len(steps)}: {step_name}")
        print("=" * 70)
        log.info("Step %d/%d STARTING: %s", step_number, len(steps), step_name)

        start_time = time.time()

        try:
            step_fn()
        except Exception as exc:
            elapsed = time.time() - start_time
            log.error("Step %d/%d FAILED after %.1fs: %s -> %s", step_number, len(steps), elapsed, step_name, exc)
            print()
            print(f"FAILED after {elapsed:.1f}s: {step_name}")
            print(f"Error: {exc}")
            traceback.print_exc()
            return False

        elapsed = time.time() - start_time
        log.info("Step %d/%d SUCCEEDED in %.1fs: %s", step_number, len(steps), elapsed, step_name)
        print()
        print(f"Completed in {elapsed:.1f}s")
        print()

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Run the Sensor-Free Mango Digital Twin data pipeline."
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip the network fetch steps and only recompute risk scores from cached raw data.",
    )
    args = parser.parse_args()

    steps = RISK_ONLY_STEPS if args.skip_fetch else PIPELINE_STEPS

    mode_label = "risk-engines only (cached raw data)" if args.skip_fetch else "full pipeline"
    log.info("Pipeline run starting. Mode: %s", mode_label)
    print("Sensor-Free Mango Digital Twin — pipeline run")
    print(f"Mode: {mode_label}")
    print()

    success = run_steps(steps)

    print("=" * 70)
    if success:
        log.info("Pipeline finished successfully.")
        print("Pipeline finished successfully.")
        print("Run the dashboard with: streamlit run app/streamlit_app.py")
    else:
        log.error("Pipeline stopped early due to an error.")
        print("Pipeline stopped early due to an error. See traceback above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
