"""
Standalone, INTERPOLATED-Kc FAO-56 soil-water balance script.

PURPOSE
-------
The existing phenology-aware FAO-56 script (fao56_phenology_water_balance.py)
assigns one Kc value per mango growth stage — a step function: Kc jumps abruptly
at stage boundaries.  This is a scientifically acceptable starting point but is
less realistic: in the field, a mango tree's water demand (and hence its Kc)
changes gradually as it moves from one growth stage to the next, not
instantaneously overnight.

This script produces an alternative water-balance output in which Kc transitions
smoothly between stages.  The same six per-stage Kc anchors from
configs/config.yaml -> fao56.phenology_kc_stages are used as target values:

  Flower induction / pre-flowering : Kc = 0.65
  Flowering                        : Kc = 0.75
  Fruit set                        : Kc = 0.85
  Fruit development                : Kc = 0.90
  Maturity / harvest               : Kc = 0.80
  Rest / vegetative phase          : Kc = 0.60

INTERPOLATION METHOD — "stage-midpoint linear" interpolation
-------------------------------------------------------------
For each contiguous block of days that share the same mango growth stage, the
MIDPOINT day of that block is treated as the anchor where Kc reaches its full
stage value.  Between consecutive stage midpoints, Kc is linearly interpolated.
This means:

  • Within a stage Kc rises toward its target during the first half and then
    stays near target (or gently adjusts toward the next stage) in the second
    half.
  • At stage boundaries themselves, Kc is between the two adjacent stages,
    i.e. the abrupt step-function jump is replaced by a smooth transition.
  • Before the first anchor and after the last anchor, Kc is held constant at
    the first / last anchor value (no extrapolation beyond the data range).

The output includes both the original step-function `stage_kc` column (for
direct comparison with fao56_phenology_water_balance.py) and the new
`interpolated_kc` column used for ETc and depletion in this script.

IMPORTANT CAVEAT
----------------
Both the stage Kc anchors and the interpolation itself are STILL ASSUMPTION-
BASED and NOT field-calibrated.  The smooth curve is more physically
plausible than a step function, but it does not capture real Kc dynamics
(which depend on phenological timing, canopy size, cultivar, local micro-
climate, and irrigation practices).  The output is a directional, exploratory
signal — not a precise irrigation prescription.  This is documented in the
`interpolation_method` column: "stage_anchor" marks the anchor days, and
"linear_midpoint" marks linearly interpolated days.

WHAT THIS FILE DOES NOT DO
---------------------------
  • Does NOT overwrite or modify any existing CSV (constant-Kc or stage-Kc
    phenology balance CSV are untouched).
  • Does NOT modify main.py, run_pipeline.py, or the Streamlit dashboard.
  • Does NOT call any external API.

INPUTS
------
  data/processed/muthukur_combined_feature_table.csv
  data/processed/muthukur_mango_phenology_calendar.csv

OUTPUT
------
  data/processed/muthukur_fao56_interpolated_kc_water_balance.csv

COLUMNS
-------
  date                   — calendar date (YYYY-MM-DD)
  mango_stage            — growth stage name from the phenology calendar
  stage_kc               — step-function Kc for this stage (same as phenology
                           water balance script; provided for comparison)
  interpolated_kc        — smoothly interpolated Kc used for ETc / depletion
                           in this output (see INTERPOLATION METHOD above)
  et0_mm_day             — FAO-56 Penman-Monteith reference ET (mm/day)
  etc_mm_day             — crop ET = ET0 × interpolated_kc (mm/day)
  root_zone_depletion_mm — running root-zone depletion (mm); initialised at 0
                           (field capacity), driven by ETc − rainfall
  taw_mm                 — total available water in the root zone (mm)
  raw_mm                 — readily available water (depletion at which stress
                           begins); = p × TAW
  ks                     — FAO-56 water-stress coefficient (1.0 = no stress)
  water_stress_level     — "Low" / "Medium" / "High" (same thresholds as all
                           other FAO-56 scripts in this project)
  interpolation_method   — "stage_anchor" (midpoint of a stage block) or
                           "linear_midpoint" (interpolated day)

HOW TO RUN
----------
  # Build inputs first if they don't exist:
  python src/features/build_feature_table.py
  python src/phenology/mango_phenology_calendar.py

  # Then run this script:
  python src/water_balance/fao56_interpolated_kc_water_balance.py

REFERENCE
---------
Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). "Crop Evapotranspiration
— Guidelines for computing crop water requirements." FAO Irrigation and Drainage
Paper No. 56.  ET0 eq 6; TAW/RAW/depletion eq 82-85; same equations as all other
FAO-56 scripts in this project.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validation import MissingColumnsError, validate_fao56_input, validate_phenology_output

# Re-use ET0 and soil functions directly from the base FAO-56 script to avoid
# duplicating the physics — both scripts remain mathematically identical in
# how they compute ET0, TAW, RAW, and the running depletion balance.
from src.water_balance.fao56_water_balance import (
    REFERENCE_ALBEDO_DEFAULT,
    _field_capacity_and_wilting_point,
    _water_stress_label,
    compute_et0,
)

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Kc interpolation
# ---------------------------------------------------------------------------

def _compute_interpolated_kc(
    stage_kc_values: np.ndarray,
) -> tuple[np.ndarray, list[str]]:
    """
    Produce a smoothly interpolated Kc series from a step-function Kc array.

    Algorithm — "stage-midpoint linear":
      1. Identify every contiguous block of identical Kc values (i.e. one
         growth stage run).
      2. The midpoint index of each block is the *anchor*: Kc reaches its
         full stage value there.
      3. Between consecutive anchors, np.interp performs linear interpolation.
      4. Before the first anchor / after the last anchor, Kc is held constant
         at the first / last anchor value (no extrapolation).

    Parameters
    ----------
    stage_kc_values : np.ndarray of shape (n,)
        The step-function per-day Kc values (one float per stage block).

    Returns
    -------
    interpolated_kc : np.ndarray of shape (n,)
        Smoothly interpolated Kc values.
    method_labels : list[str] of length n
        "stage_anchor" for the midpoint days; "linear_midpoint" elsewhere.
    """
    n = len(stage_kc_values)
    all_indices = np.arange(n, dtype=float)

    # --- step 1: find contiguous stage blocks ---------------------
    blocks: list[tuple[int, int, float]] = []  # (start_idx, end_idx, kc)
    start = 0
    for i in range(1, n):
        if stage_kc_values[i] != stage_kc_values[i - 1]:
            blocks.append((start, i - 1, stage_kc_values[start]))
            start = i
    blocks.append((start, n - 1, stage_kc_values[start]))

    # --- step 2: compute anchor indices (midpoints) ---------------
    anchor_indices: list[float] = []
    anchor_kc: list[float] = []
    for (blk_start, blk_end, kc) in blocks:
        mid = (blk_start + blk_end) / 2.0
        anchor_indices.append(mid)
        anchor_kc.append(kc)

    # --- step 3: interpolate (clamp at boundary values outside range) ---
    anchor_arr = np.array(anchor_indices, dtype=float)
    kc_arr = np.array(anchor_kc, dtype=float)
    interpolated = np.interp(all_indices, anchor_arr, kc_arr)

    # --- step 4: label anchor vs. interpolated days ---------------
    # A day is labelled "stage_anchor" if it is the integer midpoint of a block.
    anchor_int_set: set[int] = {int(round(idx)) for idx in anchor_indices}
    method_labels = [
        "stage_anchor" if i in anchor_int_set else "linear_midpoint"
        for i in range(n)
    ]

    return interpolated, method_labels


# ---------------------------------------------------------------------------
# Water balance with interpolated Kc
# ---------------------------------------------------------------------------

def compute_interpolated_kc_water_balance(
    joined_df: pd.DataFrame,
    et0: pd.Series,
    stage_kc: np.ndarray,
    interpolated_kc: np.ndarray,
    method_labels: list[str],
    root_depth_m: float,
    depletion_fraction_p: float,
) -> pd.DataFrame:
    """
    Compute ETc and the daily root-zone soil-water balance using the smoothly
    *interpolated* Kc (not the step-function stage Kc).

    The depletion / Ks equations are identical to fao56_phenology_water_balance.py
    (FAO-56 eq 82-85).  Only the Kc driving ETc changes.

    Returns a DataFrame with all output columns specified in the module docstring.
    """
    etc_values = et0.to_numpy() * interpolated_kc  # ETc = ET0 × interpolated Kc

    theta_fc, theta_wp = _field_capacity_and_wilting_point(
        sand_percent=joined_df["sand_percent"].iloc[0],
        clay_percent=joined_df["clay_percent"].iloc[0],
        organic_carbon_g_kg=joined_df["organic_carbon_g_kg"].iloc[0],
    )

    taw_mm = 1000.0 * (theta_fc - theta_wp) * root_depth_m  # eq 82
    raw_mm = depletion_fraction_p * taw_mm                   # eq 83

    rainfall = joined_df["rainfall_mm"].fillna(0.0).to_numpy()

    # Running depletion balance (eq 85 simplified): start at field capacity
    n = len(joined_df)
    depletion = np.zeros(n)
    prev_dep = 0.0
    for i in range(n):
        dep = prev_dep - rainfall[i] + etc_values[i]
        dep = max(0.0, min(dep, taw_mm))
        depletion[i] = dep
        prev_dep = dep

    ks = np.where(
        depletion > raw_mm,
        (taw_mm - depletion) / max(taw_mm - raw_mm, 1e-9),
        1.0,
    )  # eq 84
    ks = np.clip(ks, 0.0, 1.0)

    out = pd.DataFrame(
        {
            "date": joined_df["date"].to_numpy(),
            "mango_stage": joined_df["mango_stage"].to_numpy(),
            "stage_kc": stage_kc,
            "interpolated_kc": np.round(interpolated_kc, 5),
            "et0_mm_day": np.round(et0.to_numpy(), 4),
            "etc_mm_day": np.round(etc_values, 4),
            "root_zone_depletion_mm": np.round(depletion, 3),
            "taw_mm": taw_mm,
            "raw_mm": raw_mm,
            "ks": np.round(ks, 4),
            "water_stress_level": [_water_stress_label(k) for k in ks],
            "interpolation_method": method_labels,
        }
    )
    return out


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_fao56_interpolated_kc_water_balance() -> bool:
    """
    Build the interpolated-Kc FAO-56 water-balance CSV.

    Returns True on success, False if an input is missing or malformed,
    always with a plain-English explanation printed to stdout first.
    """
    config = get_config()
    feature_table_path = config.path("combined_feature_table_csv")
    phenology_path = config.path("mango_phenology_calendar_csv")
    output_path = config.path("fao56_interpolated_kc_water_balance_csv")

    # --- load inputs -------------------------------------------------------
    if not feature_table_path.exists():
        print(
            f"\nCombined feature table not found: {feature_table_path}\n"
            "Run python src/features/build_feature_table.py first."
        )
        return False
    if not phenology_path.exists():
        print(
            f"\nMango phenology calendar not found: {phenology_path}\n"
            "Run python src/phenology/mango_phenology_calendar.py first."
        )
        return False

    feature_df = pd.read_csv(feature_table_path)
    try:
        validate_fao56_input(feature_df)
    except MissingColumnsError as exc:
        print(f"\n{exc}")
        return False
    feature_df["date"] = pd.to_datetime(feature_df["date"])
    feature_df = feature_df.sort_values("date").reset_index(drop=True)

    phenology_df = pd.read_csv(phenology_path)
    try:
        validate_phenology_output(phenology_df)
    except MissingColumnsError as exc:
        print(f"\n{exc}")
        return False
    phenology_df["date"] = pd.to_datetime(phenology_df["date"])
    phenology_df = phenology_df.sort_values("date").reset_index(drop=True)

    log.info("Loaded %d feature-table rows from %s", len(feature_df), feature_table_path)
    log.info("Loaded %d phenology rows from %s", len(phenology_df), phenology_path)

    # --- inner join on date ------------------------------------------------
    joined_df = feature_df.merge(
        phenology_df[["date", "mango_stage"]],
        on="date",
        how="inner",
    ).sort_values("date").reset_index(drop=True)

    if joined_df.empty:
        print(
            "\nNo overlapping dates between the combined feature table "
            f"({feature_df['date'].min().date()} – {feature_df['date'].max().date()}) "
            f"and the phenology calendar "
            f"({phenology_df['date'].min().date()} – {phenology_df['date'].max().date()}). "
            "Nothing to compute."
        )
        return False

    log.info(
        "Joined table: %d rows (inner join on date, %d feature + %d phenology rows).",
        len(joined_df), len(feature_df), len(phenology_df),
    )

    # --- FAO-56 settings from config ---------------------------------------
    fao56_cfg = config._raw.get("fao56", {})
    elevation_m = fao56_cfg.get("elevation_m", 150)
    root_depth_m = fao56_cfg.get("root_depth_m", 1.2)
    depletion_fraction_p = fao56_cfg.get("depletion_fraction_p", 0.50)
    albedo = fao56_cfg.get("albedo", REFERENCE_ALBEDO_DEFAULT)
    phenology_kc_stages: dict = fao56_cfg.get("phenology_kc_stages", {})

    if not phenology_kc_stages:
        print(
            "\nconfigs/config.yaml is missing fao56.phenology_kc_stages.\n"
            "Add stage-to-Kc mappings before running this script."
        )
        return False

    # --- Kc lookup (step function, same as phenology script) ---------------
    unknown = sorted(set(joined_df["mango_stage"].unique()) - set(phenology_kc_stages.keys()))
    if unknown:
        print(
            f"\nPhenology calendar has stage(s) with no configured Kc: {unknown}\n"
            f"Known stages in config: {sorted(phenology_kc_stages.keys())}"
        )
        return False

    stage_kc = joined_df["mango_stage"].map(phenology_kc_stages).to_numpy(dtype=float)

    # --- smooth interpolation of Kc ----------------------------------------
    interpolated_kc, method_labels = _compute_interpolated_kc(stage_kc)

    # --- ET0 (identical physics to all other FAO-56 scripts) ---------------
    et0 = compute_et0(
        joined_df,
        latitude_deg=config.latitude,
        elevation_m=elevation_m,
        albedo=albedo,
    )

    # --- full water balance with interpolated Kc ---------------------------
    result = compute_interpolated_kc_water_balance(
        joined_df=joined_df,
        et0=et0,
        stage_kc=stage_kc,
        interpolated_kc=interpolated_kc,
        method_labels=method_labels,
        root_depth_m=root_depth_m,
        depletion_fraction_p=depletion_fraction_p,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)

    # --- console summary ---------------------------------------------------
    n_anchor = sum(1 for m in method_labels if m == "stage_anchor")
    n_interp = len(method_labels) - n_anchor
    stage_kc_diff = np.abs(result["interpolated_kc"] - result["stage_kc"])
    stress_counts = result["water_stress_level"].value_counts().to_dict()
    kc_range = (result["interpolated_kc"].min(), result["interpolated_kc"].max())

    log.info("Interpolated-Kc FAO-56 water balance: %d rows.", len(result))
    log.info(
        "TAW=%.1f mm, RAW=%.1f mm (root depth=%.2f m, p=%.2f)",
        result["taw_mm"].iloc[0], result["raw_mm"].iloc[0], root_depth_m, depletion_fraction_p,
    )
    log.info("Kc range: %.3f – %.3f", kc_range[0], kc_range[1])
    log.info("Stage-anchor days: %d; linear-midpoint days: %d", n_anchor, n_interp)
    log.info("Water stress level breakdown: %s", stress_counts)
    log.info("Wrote interpolated-Kc water balance to %s", output_path)

    print()
    print("=" * 60)
    print("Interpolated-Kc FAO-56 Water Balance — summary")
    print("=" * 60)
    print(f"  Input rows (feature table):   {len(feature_df)}")
    print(f"  Input rows (phenology cal.):  {len(phenology_df)}")
    print(f"  Joined / output rows:         {len(result)}")
    print(f"  Date range:                   {result['date'].iloc[0].date()} – {result['date'].iloc[-1].date()}")
    print(f"  Root depth:                   {root_depth_m} m")
    print(f"  Depletion fraction p:         {depletion_fraction_p}")
    print(f"  TAW:                          {result['taw_mm'].iloc[0]:.1f} mm")
    print(f"  RAW:                          {result['raw_mm'].iloc[0]:.1f} mm")
    print()
    print("  Kc statistics:")
    print(f"    Stage-anchor days:          {n_anchor}")
    print(f"    Linear-midpoint days:       {n_interp}")
    print(f"    interpolated_kc range:      {kc_range[0]:.4f} – {kc_range[1]:.4f}")
    print(f"    Mean |interpolated – stage|:{stage_kc_diff.mean():.4f}")
    print(f"    Max  |interpolated – stage|:{stage_kc_diff.max():.4f}")
    print()
    print("  Water-balance statistics:")
    print(f"    Mean ET0 (mm/day):          {result['et0_mm_day'].mean():.2f}")
    print(f"    Mean ETc (mm/day):          {result['etc_mm_day'].mean():.2f}")
    print(f"    Water stress breakdown:     {stress_counts}")
    print()
    print("  Output file:")
    print(f"    {output_path}")
    print()
    print("NOTE: Interpolated Kc is still assumption-based and not field-")
    print("calibrated.  Both stage_kc (step function) and interpolated_kc")
    print("(smooth) are in the CSV for direct comparison.  The existing")
    print("constant-Kc and stage-Kc water balance CSVs are untouched.")
    print("=" * 60)
    return True


def main() -> None:
    log.info("Building interpolated-Kc FAO-56 soil-water balance …")
    success = build_fao56_interpolated_kc_water_balance()
    if success:
        log.info("Interpolated-Kc FAO-56 water balance build completed successfully.")
    else:
        log.error("Interpolated-Kc FAO-56 water balance build did not complete — see messages above.")


if __name__ == "__main__":
    main()
