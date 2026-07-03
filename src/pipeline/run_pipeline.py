"""
Single pipeline runner for the Sensor-Free Mango Digital Twin.

This runner has two layers, run in this order every time:

LAYER 1 — core fetch + risk steps (unchanged behavior from before this
milestone). Runs every fetcher/risk-engine in strict order; stops on the
first failure, exactly like before:

  1. NASA POWER historical weather       -> src/weather/fetch_weather.py
  2. SoilGrids soil intelligence         -> src/soil/fetch_soilgrids.py
  3. Historical mango risk engine        -> src/risk/historical_risk_engine.py
  4. Open-Meteo recent/forecast weather  -> src/weather/fetch_open_meteo.py
  5. Forecast mango risk engine          -> src/risk/open_meteo_risk_engine.py

  Steps 1+2 must finish before step 3 (the historical risk engine needs both
  raw weather and soil data). Step 4 must finish before step 5. Step 2 also
  feeds step 5, since the forecast engine applies the same soil-adjusted
  irrigation factor.

  With `--skip-fetch`, only steps 3 and 5 run (recompute risk from cached
  raw data).

  With `--skip-soil-fetch`, step 2 (SoilGrids) is omitted and the cached
  soil CSV on disk is reused. Steps 1, 3, 4, and 5 run normally. This is
  safe for automated daily refresh because SoilGrids data is static/slow-
  changing and the API is occasionally slow or unavailable. The cached CSV
  must already exist on disk; if it does not, the pipeline fails clearly
  before running any steps.

LAYER 2 — freshness-aware downstream steps (new this milestone). These wrap
the existing standalone build scripts (Sentinel-2 daily aggregation,
combined feature table, mango phenology calendar, constant-Kc FAO-56,
phenology-aware FAO-56, FAO-56 model comparison) as first-class pipeline
steps, so `python main.py --skip-fetch` regenerates every downstream output
that depends on already-available cached/raw data -- not just the two risk
engines.

No scientific/model logic is duplicated here -- each step calls the build
script's own existing function. This module only adds:
  - dependency-aware ordering (each step's required inputs are config path
    keys, checked before the step runs),
  - freshness-aware skip logic: if a step's output already exists and is
    newer than every one of its required inputs, the step is skipped with a
    clear message instead of re-running for nothing,
  - graceful handling of missing inputs: a downstream step whose required
    input doesn't exist yet is skipped with a clear warning, not treated as
    a pipeline failure, and the rest of the pipeline still runs,
  - a per-step RUN / SKIP / FAILED result that is written into
    data/processed/pipeline_run_metadata.json alongside the existing
    freshness metadata.

Layer 2 always runs after layer 1, even if layer 1 reported a failure --
each layer-2 step only depends on its own required *files* existing, not on
whether this specific run's fetch/risk steps succeeded, so a failed fetch
should not block regenerating downstream outputs from data that is already
cached on disk.

Usage:
    python src/pipeline/run_pipeline.py
    python src/pipeline/run_pipeline.py --skip-fetch        # reuse cached raw data, just recompute risk + downstream
    python src/pipeline/run_pipeline.py --skip-soil-fetch   # fetch weather but reuse cached soil CSV
"""

import argparse
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.weather import fetch_weather, fetch_open_meteo
from src.soil import fetch_soilgrids
from src.risk import historical_risk_engine, open_meteo_risk_engine
from src.remote_sensing import aggregate_sentinel2_timeseries as sentinel2_aggregation_script
from src.features import build_feature_table as feature_table_script
from src.phenology import mango_phenology_calendar as phenology_calendar_script
from src.water_balance import fao56_water_balance as constant_kc_script
from src.water_balance import fao56_phenology_water_balance as phenology_kc_script
from src.validation import compare_fao56_models as model_comparison_script
from src.advisory import forecast_aware_irrigation as advisory_script
from src.water_balance import fao56_interpolated_kc_water_balance as interpolated_kc_script
from src.validation import fao56_sensitivity_analysis as sensitivity_analysis_script
from src.validation import compare_et0_openmeteo_vs_fao56 as et0_comparison_script
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.pipeline_metadata import (
    build_pipeline_metadata,
    write_metadata_json,
    utc_now,
)

log = get_logger(__name__)


# =======================================================================
# Layer 1 — core fetch + risk steps (unchanged behavior)
# =======================================================================

PIPELINE_STEPS = [
    ("NASA POWER historical weather", fetch_weather.main),
    ("SoilGrids soil intelligence", fetch_soilgrids.main),
    ("Historical mango risk engine", historical_risk_engine.main),
    ("Open-Meteo recent/forecast weather", fetch_open_meteo.main),
    ("Forecast mango risk engine", open_meteo_risk_engine.main),
]

# --skip-soil-fetch: fetch weather + run risk engines, but skip the live
# SoilGrids API call and reuse the cached soil CSV on disk instead.
SKIP_SOIL_STEPS = [
    ("NASA POWER historical weather", fetch_weather.main),
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


# =======================================================================
# Layer 2 — freshness-aware downstream steps (new this milestone)
# =======================================================================

@dataclass
class FreshnessAwareStep:
    """
    A downstream pipeline step that wraps an existing standalone script's
    own build function.

    name:        human-readable step name, used in logs/console output.
    build_fn:    the existing script's own callable (e.g.
                 build_feature_table) -- returns True/False. No scientific
                 logic lives here; this only decides WHETHER to call it.
    input_keys:  configs/config.yaml `paths` keys this step reads. If any
                 of these files don't exist yet, the step is skipped with a
                 warning instead of failing the pipeline.
    output_keys: configs/config.yaml `paths` keys this step writes. If every
                 output already exists and is newer than every input, the
                 step is skipped as already up to date.
    """

    name: str
    build_fn: Callable[[], bool]
    input_keys: list[str]
    output_keys: list[str]


# Dependency order matters here: each step's inputs must already be
# produced by an earlier step in this list (or already cached on disk from
# a previous run).
FRESHNESS_AWARE_STEPS = [
    FreshnessAwareStep(
        name="Sentinel-2 daily aggregation",
        build_fn=sentinel2_aggregation_script.aggregate_timeseries,
        input_keys=["sentinel2_timeseries_csv"],
        output_keys=["sentinel2_daily_csv"],
    ),
    FreshnessAwareStep(
        name="Combined feature table",
        build_fn=feature_table_script.build_feature_table,
        input_keys=["historical_risk_csv", "sentinel2_daily_csv", "soilgrids_csv"],
        output_keys=["combined_feature_table_csv"],
    ),
    FreshnessAwareStep(
        name="Mango phenology calendar",
        build_fn=phenology_calendar_script.build_mango_phenology_calendar,
        input_keys=["combined_feature_table_csv"],
        output_keys=["mango_phenology_calendar_csv"],
    ),
    FreshnessAwareStep(
        name="Constant-Kc FAO-56 water balance",
        build_fn=constant_kc_script.build_fao56_water_balance,
        input_keys=["combined_feature_table_csv"],
        output_keys=["fao56_water_balance_csv"],
    ),
    FreshnessAwareStep(
        name="Phenology-aware FAO-56 water balance",
        build_fn=phenology_kc_script.build_fao56_phenology_water_balance,
        input_keys=["combined_feature_table_csv", "mango_phenology_calendar_csv"],
        output_keys=["fao56_phenology_water_balance_csv"],
    ),
    FreshnessAwareStep(
        name="Interpolated-Kc FAO-56 water balance",
        build_fn=interpolated_kc_script.build_fao56_interpolated_kc_water_balance,
        input_keys=["combined_feature_table_csv", "mango_phenology_calendar_csv"],
        output_keys=["fao56_interpolated_kc_water_balance_csv"],
    ),
    FreshnessAwareStep(
        name="FAO-56 model comparison",
        build_fn=model_comparison_script.build_fao56_model_comparison,
        input_keys=["fao56_water_balance_csv", "fao56_phenology_water_balance_csv"],
        output_keys=["fao56_model_comparison_csv", "fao56_model_comparison_summary_md"],
    ),
    FreshnessAwareStep(
        name="FAO-56 sensitivity analysis",
        build_fn=sensitivity_analysis_script.build_fao56_sensitivity_analysis,
        input_keys=["combined_feature_table_csv", "mango_phenology_calendar_csv"],
        output_keys=["fao56_sensitivity_analysis_csv", "fao56_sensitivity_summary_md"],
    ),
    FreshnessAwareStep(
        name="Forecast-aware irrigation advisory",
        build_fn=advisory_script.run_forecast_aware_advisory,
        input_keys=["fao56_interpolated_kc_water_balance_csv", "forecast_risk_csv"],
        output_keys=["forecast_aware_irrigation_advisory_csv"],
    ),
    FreshnessAwareStep(
        name="ET0 source comparison (Open-Meteo vs FAO-56)",
        build_fn=et0_comparison_script.build_et0_comparison,
        input_keys=["open_meteo_csv", "fao56_water_balance_csv"],
        output_keys=["et0_comparison_csv", "et0_comparison_summary_md"],
    ),
]


@dataclass
class StepResult:
    name: str
    status: str  # "RUN" | "SKIP_FRESH" | "SKIP_MISSING_INPUT" | "FAILED"
    detail: str


def _existing_mtimes(paths: list[Path]) -> list[float]:
    return [p.stat().st_mtime for p in paths if p.exists()]


def run_freshness_aware_step(step: FreshnessAwareStep) -> StepResult:
    """
    Decide whether to run, skip, or fail a single freshness-aware step, and
    do it. Never raises -- any exception from the underlying build function
    is caught and reported as a FAILED result so the rest of the pipeline
    (and metadata writing) can continue.
    """
    config = get_config()
    input_paths = [config.path(key) for key in step.input_keys]
    output_paths = [config.path(key) for key in step.output_keys]

    missing_inputs = [p for p in input_paths if not p.exists()]
    if missing_inputs:
        detail = "missing required input(s): " + ", ".join(str(p) for p in missing_inputs)
        print(f"SKIP: {step.name}")
        print(f"  Reason: {detail}")
        log.warning("Step '%s' skipped: %s", step.name, detail)
        return StepResult(step.name, "SKIP_MISSING_INPUT", detail)

    missing_outputs = [p for p in output_paths if not p.exists()]
    if not missing_outputs:
        newest_input_mtime = max(_existing_mtimes(input_paths))
        oldest_output_mtime = min(_existing_mtimes(output_paths))
        if oldest_output_mtime >= newest_input_mtime:
            detail = "output already up to date with all required inputs"
            print(f"SKIP: {step.name}")
            print(f"  Reason: {detail}")
            log.info("Step '%s' skipped: %s", step.name, detail)
            return StepResult(step.name, "SKIP_FRESH", detail)

    print(f"RUN: {step.name}")
    log.info("Step '%s' starting (output missing or stale).", step.name)
    start_time = time.time()

    try:
        success = step.build_fn()
    except Exception as exc:
        elapsed = time.time() - start_time
        detail = f"raised {type(exc).__name__}: {exc}"
        print(f"FAILED: {step.name} (after {elapsed:.1f}s)")
        print(f"  Error: {detail}")
        log.error("Step '%s' failed after %.1fs: %s", step.name, elapsed, detail)
        traceback.print_exc()
        return StepResult(step.name, "FAILED", detail)

    elapsed = time.time() - start_time
    if success:
        detail = f"completed in {elapsed:.1f}s"
        log.info("Step '%s' succeeded in %.1fs", step.name, elapsed)
        return StepResult(step.name, "RUN", detail)

    detail = "build function reported failure (see messages above)"
    print(f"FAILED: {step.name} (after {elapsed:.1f}s)")
    print(f"  Reason: {detail}")
    log.warning("Step '%s' reported failure after %.1fs", step.name, elapsed)
    return StepResult(step.name, "FAILED", detail)


def run_freshness_aware_steps(steps: list[FreshnessAwareStep]) -> list[StepResult]:
    """Run every freshness-aware step in order, regardless of individual outcomes."""

    results = []
    for step_number, step in enumerate(steps, start=1):
        print("=" * 70)
        print(f"Step {step_number}/{len(steps)} (freshness-aware): {step.name}")
        print("=" * 70)
        results.append(run_freshness_aware_step(step))
        print()
    return results


# =======================================================================
# Metadata + entry point
# =======================================================================

def write_pipeline_metadata(
    run_started_at,
    run_completed_at,
    pipeline_mode: str,
    status: str,
    step_results: list[StepResult] | None = None,
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

        step_results = step_results or []
        step_results_payload = [
            {"name": result.name, "status": result.status, "detail": result.detail}
            for result in step_results
        ]
        extra_warnings = [
            f"Step '{result.name}' {result.status}: {result.detail}"
            for result in step_results
            if result.status in ("SKIP_MISSING_INPUT", "FAILED")
        ]

        metadata = build_pipeline_metadata(
            run_started_at=run_started_at,
            run_completed_at=run_completed_at,
            pipeline_mode=pipeline_mode,
            status=status,
            step_results=step_results_payload,
            extra_warnings=extra_warnings,
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
        help="Skip all network fetch steps and only recompute risk scores and downstream outputs from cached raw data.",
    )
    parser.add_argument(
        "--skip-soil-fetch",
        action="store_true",
        help=(
            "Skip the SoilGrids API fetch and reuse the cached soil CSV on disk. "
            "NASA POWER and Open-Meteo are still fetched. "
            "Fails clearly if no cached soil CSV exists. "
            "Recommended for automated daily refresh (GitHub Actions) to avoid "
            "transient SoilGrids API timeouts."
        ),
    )
    args = parser.parse_args()

    if args.skip_fetch and args.skip_soil_fetch:
        print("Error: --skip-fetch and --skip-soil-fetch cannot be used together.")
        sys.exit(1)

    if args.skip_fetch:
        steps = RISK_ONLY_STEPS
        mode_label = "risk-engines only (cached raw data)"
    elif args.skip_soil_fetch:
        # Guard: cached soil CSV must already exist — fail fast and clearly if not.
        config = get_config()
        soil_csv = config.path("soilgrids_csv")
        if not soil_csv.exists():
            print(
                f"Error: --skip-soil-fetch requires a cached soil CSV at:\n"
                f"  {soil_csv}\n"
                f"Run without --skip-soil-fetch first to fetch and cache the soil data."
            )
            log.error("--skip-soil-fetch used but no cached soil CSV at %s", soil_csv)
            sys.exit(1)
        log.info("--skip-soil-fetch: reusing cached soil CSV at %s", soil_csv)
        print(f"Soil fetch skipped — reusing cached CSV: {soil_csv}")
        steps = SKIP_SOIL_STEPS
        mode_label = "weather fetch + risk engines (cached soil data)"
    else:
        steps = PIPELINE_STEPS
        mode_label = "full pipeline"

    log.info("Pipeline run starting. Mode: %s", mode_label)
    print("Sensor-Free Mango Digital Twin — pipeline run")
    print(f"Mode: {mode_label}")
    print()

    run_started_at = utc_now()
    success = run_steps(steps)

    print("=" * 70)
    print("Freshness-aware downstream steps")
    print("=" * 70)
    print(
        "These steps regenerate Sentinel-2 aggregation, the combined feature "
        "table, the phenology calendar, both FAO-56 water-balance models, "
        "the interpolated-Kc water balance, the model comparison, the "
        "FAO-56 sensitivity analysis, and the forecast-aware irrigation "
        "advisory whenever their required inputs are newer than their last "
        "output -- or skip cleanly if everything is already current or a "
        "required input is still missing."
    )
    print()
    step_results = run_freshness_aware_steps(FRESHNESS_AWARE_STEPS)

    run_completed_at = utc_now()

    print("=" * 70)
    if success:
        log.info("Pipeline finished successfully.")
        print("Core pipeline (fetch/risk) finished successfully.")
    else:
        log.error("Pipeline stopped early due to an error.")
        print("Core pipeline (fetch/risk) stopped early due to an error. See traceback above.")

    failed_steps = [r for r in step_results if r.status == "FAILED"]
    skipped_steps = [r for r in step_results if r.status == "SKIP_MISSING_INPUT"]
    if failed_steps:
        print(f"{len(failed_steps)} freshness-aware step(s) FAILED -- see warnings above and in pipeline_run_metadata.json.")
    if skipped_steps:
        print(f"{len(skipped_steps)} freshness-aware step(s) SKIPPED due to missing input(s).")
    if not failed_steps and not skipped_steps:
        print("All freshness-aware downstream steps ran or were already up to date.")

    print()
    print("Run the dashboard with: streamlit run app/streamlit_app.py")

    write_pipeline_metadata(
        run_started_at=run_started_at,
        run_completed_at=run_completed_at,
        pipeline_mode=mode_label,
        status="success" if success else "failed",
        step_results=step_results,
    )

    if not success:
        sys.exit(1)
    if failed_steps:
        sys.exit(1)


if __name__ == "__main__":
    main()
