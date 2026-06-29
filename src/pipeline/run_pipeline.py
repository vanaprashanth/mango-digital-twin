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
from src.water_balance import fao56_phenology_water_balance
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.pipeline_metadata import (
    build_pipeline_metadata,
    write_metadata_json,
    utc_now,
)

log = get_logger(__name__)


def run_phenology_aware_fao56_step() -> None:
    """
    Optional pipeline step: regenerate the phenology-aware FAO-56 water
    balance CSV (data/processed/muthukur_fao56_phenology_water_balance.csv)
    by re-using the existing standalone script's function -- no FAO-56 or Kc
    math is duplicated here.

    This step only runs if BOTH of its required inputs already exist:
      - data/processed/muthukur_combined_feature_table.csv
      - data/processed/muthukur_mango_phenology_calendar.csv

    Those two files are still produced by their own standalone scripts
    (src/features/build_feature_table.py and
    src/phenology/mango_phenology_calendar.py respectively) -- this pipeline
    does not build them. If either is missing, this step prints a clear
    explanation and returns without raising, so a missing optional input
    never stops the rest of the pipeline (the existing constant-Kc FAO-56
    behavior and every other step are unaffected either way).
    """
    config = get_config()
    feature_table_path = config.path("combined_feature_table_csv")
    phenology_calendar_path = config.path("mango_phenology_calendar_csv")
    output_path = config.path("fao56_phenology_water_balance_csv")

    print(f"Required input 1 (combined feature table): {feature_table_path}")
    print(f"Required input 2 (mango phenology calendar): {phenology_calendar_path}")
    print(f"Output:                                      {output_path}")
    print()

    missing = [p for p in (feature_table_path, phenology_calendar_path) if not p.exists()]
    if missing:
        print("Skipping phenology-aware FAO-56 water balance step.")
        print("Missing required input file(s):")
        for path in missing:
            print(f"  - {path}")
        print("Build the missing input(s) first, then re-run this step:")
        print("  python src/features/build_feature_table.py")
        print("  python src/phenology/mango_phenology_calendar.py")
        log.warning("Phenology-aware FAO-56 step skipped: missing input(s) %s", missing)
        return

    success = fao56_phenology_water_balance.build_fao56_phenology_water_balance()
    if success:
        print(f"Phenology-aware FAO-56 water balance written to: {output_path}")
        log.info("Phenology-aware FAO-56 water balance step succeeded.")
    else:
        print("Phenology-aware FAO-56 water balance step did not complete successfully.")
        print("See the messages above for details. The rest of the pipeline will continue.")
        log.warning("Phenology-aware FAO-56 water balance step reported failure (see messages above).")


PIPELINE_STEPS = [
    ("NASA POWER historical weather", fetch_weather.main),
    ("SoilGrids soil intelligence", fetch_soilgrids.main),
    ("Historical mango risk engine", historical_risk_engine.main),
    ("Open-Meteo recent/forecast weather", fetch_open_meteo.main),
    ("Forecast mango risk engine", open_meteo_risk_engine.main),
    ("Phenology-aware FAO-56 water balance (optional)", run_phenology_aware_fao56_step),
]

RISK_ONLY_STEPS = [
    ("Historical mango risk engine", historical_risk_engine.main),
    ("Forecast mango risk engine", open_meteo_risk_engine.main),
    ("Phenology-aware FAO-56 water balance (optional)", run_phenology_aware_fao56_step),
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


def write_pipeline_metadata(
    run_started_at,
    run_completed_at,
    pipeline_mode: str,
    status: str,
) -> None:
    """
    Build and write data/processed/pipeline_run_metadata.json after a
    pipeline run, whether it succeeded or failed. This is best-effort: if
    metadata collection itself raises for any reason, it is logged as a
    warning and swallowed so a metadata problem never turns a successful
    (or already-failed) pipeline run into a crashed one.
    """
    try:
        config = get_config()
        metadata = build_pipeline_metadata(
            run_started_at=run_started_at,
            run_completed_at=run_completed_at,
            pipeline_mode=pipeline_mode,
            status=status,
        )
        output_path = config.path("pipeline_run_metadata_json")
        write_metadata_json(metadata, output_path)
        print(f"Pipeline run metadata written to: {output_path}")
        log.info("Pipeline run metadata written to %s", output_path)
    except Exception as exc:
        log.warning("Could not write pipeline run metadata: %s", exc)
        print(f"Warning: could not write pipeline run metadata ({exc}).")


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

    run_started_at = utc_now()
    success = run_steps(steps)
    run_completed_at = utc_now()

    print("=" * 70)
    if success:
        log.info("Pipeline finished successfully.")
        print("Pipeline finished successfully.")
        print("Run the dashboard with: streamlit run app/streamlit_app.py")
    else:
        log.error("Pipeline stopped early due to an error.")
        print("Pipeline stopped early due to an error. See traceback above.")

    write_pipeline_metadata(
        run_started_at=run_started_at,
        run_completed_at=run_completed_at,
        pipeline_mode=mode_label,
        status="success" if success else "failed",
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
