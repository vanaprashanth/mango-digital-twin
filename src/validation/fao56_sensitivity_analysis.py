"""
Standalone FAO-56 sensitivity analysis script.

PURPOSE
-------
The FAO-56 phenology-aware water balance depends on several parameters whose
values are ASSUMED, not field-measured:

  • root_depth_m       — effective root-zone depth of a mature mango tree
  • depletion_fraction_p — soil-water depletion fraction at which water stress
                           begins (FAO-56 Table 22 typical value for fruit trees)
  • Kc (crop coefficient) — per-stage Kc values from general FAO-56 / mango
                           guidance, not calibrated to this specific orchard

This script tests how sensitive the FAO-56 outputs are to each of these
assumptions by running the water balance across a FULL FACTORIAL grid of
parameter values:

  root_depth_m         : 0.8, 1.0, 1.2 (baseline), 1.5  m
  depletion_fraction_p : 0.40, 0.50 (baseline), 0.60
  kc_multiplier        : 0.90, 1.00 (baseline), 1.10

This gives 4 × 3 × 3 = 36 parameter combinations (scenarios).  For each
scenario, summary statistics are computed over the full shared date range and
compared against a clearly-identified baseline scenario.

BASELINE
--------
  root_depth_m = configs/config.yaml -> fao56.root_depth_m  (1.2 by default)
  depletion_fraction_p = configs/config.yaml -> fao56.depletion_fraction_p
  kc_multiplier = 1.00  (applies no scaling to the configured stage Kc values)

OUTPUTS
-------
  data/processed/muthukur_fao56_sensitivity_analysis.csv
    One row per scenario (36 rows).  Columns:
      scenario_id            — integer 1-36
      root_depth_m           — root depth used (m)
      depletion_fraction_p   — depletion fraction used
      kc_multiplier          — Kc multiplier applied to all stage Kc values
      is_baseline            — True if this row is the baseline scenario
      mean_et0_mm_day        — mean ET0 across the date range (ET0 is identical
                               across all scenarios since it does not depend on
                               Kc, root depth, or p)
      mean_etc_mm_day        — mean ETc (= ET0 × Kc × multiplier)
      mean_depletion_mm      — mean daily root-zone depletion
      max_depletion_mm       — maximum root-zone depletion reached
      taw_mm                 — total available water (depends on root_depth_m)
      raw_mm                 — readily available water (= p × TAW)
      n_days_high_stress     — number of days with water_stress_level = "High"
      n_days_medium_stress   — number of days with water_stress_level = "Medium"
      n_days_low_stress      — number of days with water_stress_level = "Low"
      pct_days_high_stress   — percentage of days with High stress
      delta_mean_etc         — mean ETc minus baseline mean ETc (mm/day)
      delta_mean_depletion   — mean depletion minus baseline mean depletion (mm)
      delta_n_high_stress    — High-stress days minus baseline High-stress days

  data/processed/muthukur_fao56_sensitivity_summary.md
    Human-readable markdown summary with: key findings, extreme-scenario
    comparisons, per-parameter impact tables, and interpretation notes.

WHAT THIS FILE DOES NOT DO
---------------------------
  • Does NOT modify main.py, run_pipeline.py, or the Streamlit dashboard.
  • Does NOT overwrite any existing water-balance CSV.
  • Does NOT use the interpolated-Kc output from
    fao56_interpolated_kc_water_balance.py — this script runs the stage-based
    step-function Kc (same as fao56_phenology_water_balance.py) to match the
    baseline that the project currently uses, then scales it by kc_multiplier.

INPUTS
------
  data/processed/muthukur_combined_feature_table.csv
  data/processed/muthukur_mango_phenology_calendar.csv

HOW TO RUN
----------
  python src/validation/fao56_sensitivity_analysis.py

REFERENCE
---------
Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). "Crop Evapotranspiration
— Guidelines for computing crop water requirements." FAO Irrigation and Drainage
Paper No. 56.
"""

import sys
from itertools import product
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validation import MissingColumnsError, validate_fao56_input, validate_phenology_output
from src.water_balance.fao56_water_balance import (
    REFERENCE_ALBEDO_DEFAULT,
    _field_capacity_and_wilting_point,
    _water_stress_label,
    compute_et0,
)

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Parameter grid
# ---------------------------------------------------------------------------
ROOT_DEPTH_VALUES = [0.8, 1.0, 1.2, 1.5]   # metres
DEPLETION_P_VALUES = [0.40, 0.50, 0.60]
KC_MULTIPLIER_VALUES = [0.90, 1.00, 1.10]


# ---------------------------------------------------------------------------
# Core water-balance runner for one scenario
# ---------------------------------------------------------------------------

def _run_scenario(
    et0: np.ndarray,
    kc_per_day: np.ndarray,
    rainfall: np.ndarray,
    sand_pct: float,
    clay_pct: float,
    org_carbon: float,
    root_depth_m: float,
    depletion_fraction_p: float,
    kc_multiplier: float,
) -> dict:
    """
    Run a single FAO-56 water-balance scenario with given parameters and
    return summary statistics.

    All physics are identical to fao56_phenology_water_balance.py — only the
    three sensitivity parameters (root_depth_m, p, kc_multiplier) change
    across scenarios.
    """
    scaled_kc = kc_per_day * kc_multiplier
    etc = et0 * scaled_kc

    theta_fc, theta_wp = _field_capacity_and_wilting_point(
        sand_percent=sand_pct,
        clay_percent=clay_pct,
        organic_carbon_g_kg=org_carbon,
    )
    taw_mm = 1000.0 * (theta_fc - theta_wp) * root_depth_m
    raw_mm = depletion_fraction_p * taw_mm

    n = len(et0)
    depletion = np.zeros(n)
    prev = 0.0
    for i in range(n):
        dep = prev - rainfall[i] + etc[i]
        dep = max(0.0, min(dep, taw_mm))
        depletion[i] = dep
        prev = dep

    ks = np.where(
        depletion > raw_mm,
        (taw_mm - depletion) / max(taw_mm - raw_mm, 1e-9),
        1.0,
    )
    ks = np.clip(ks, 0.0, 1.0)
    stress_labels = [_water_stress_label(k) for k in ks]

    n_high = sum(1 for s in stress_labels if s == "High")
    n_med = sum(1 for s in stress_labels if s == "Medium")
    n_low = sum(1 for s in stress_labels if s == "Low")

    return {
        "mean_et0_mm_day": float(np.mean(et0)),
        "mean_etc_mm_day": float(np.mean(etc)),
        "mean_depletion_mm": float(np.mean(depletion)),
        "max_depletion_mm": float(np.max(depletion)),
        "taw_mm": float(taw_mm),
        "raw_mm": float(raw_mm),
        "n_days_high_stress": n_high,
        "n_days_medium_stress": n_med,
        "n_days_low_stress": n_low,
        "pct_days_high_stress": round(100.0 * n_high / n, 2) if n > 0 else 0.0,
    }


# ---------------------------------------------------------------------------
# Markdown summary builder
# ---------------------------------------------------------------------------

def _build_markdown_summary(
    results_df: pd.DataFrame,
    baseline_row: pd.Series,
    date_range: str,
    n_days: int,
) -> str:
    """Build a human-readable markdown sensitivity report."""

    def fmt_delta(val: float, unit: str = "") -> str:
        sign = "+" if val >= 0 else ""
        return f"{sign}{val:.2f}{unit}"

    lines = [
        "# FAO-56 Sensitivity Analysis — Summary",
        "",
        "> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, "
        "not field-calibrated to this specific orchard or cultivar. This sensitivity "
        "analysis shows how output metrics change when those assumptions are varied — "
        "it does not identify which scenario is 'correct'. Use it to understand the "
        "uncertainty band around the baseline estimates.",
        "",
        "---",
        "",
        "## Overview",
        "",
        f"- **Date range analysed:** {date_range}",
        f"- **Number of days:** {n_days}",
        f"- **Parameter grid:** {len(ROOT_DEPTH_VALUES)} root-depth × "
        f"{len(DEPLETION_P_VALUES)} depletion-fraction × "
        f"{len(KC_MULTIPLIER_VALUES)} Kc-multiplier = "
        f"**{len(results_df)} scenarios**",
        "",
        "### Baseline scenario",
        "",
        f"| Parameter | Baseline value |",
        f"|---|---|",
        f"| Root depth | {baseline_row['root_depth_m']:.1f} m |",
        f"| Depletion fraction *p* | {baseline_row['depletion_fraction_p']:.2f} |",
        f"| Kc multiplier | {baseline_row['kc_multiplier']:.2f} |",
        f"| TAW | {baseline_row['taw_mm']:.1f} mm |",
        f"| RAW | {baseline_row['raw_mm']:.1f} mm |",
        f"| Mean ET0 | {baseline_row['mean_et0_mm_day']:.2f} mm/day |",
        f"| Mean ETc | {baseline_row['mean_etc_mm_day']:.2f} mm/day |",
        f"| Mean root-zone depletion | {baseline_row['mean_depletion_mm']:.1f} mm |",
        f"| High-stress days | {baseline_row['n_days_high_stress']} ({baseline_row['pct_days_high_stress']:.1f}%) |",
        f"| Medium-stress days | {baseline_row['n_days_medium_stress']} |",
        f"| Low-stress days | {baseline_row['n_days_low_stress']} |",
        "",
        "---",
        "",
        "## Sensitivity to root depth",
        "",
        "_Depletion fraction p and Kc multiplier held at baseline._",
        "",
    ]

    # --- root depth table -------------------------------------------------
    rd_df = results_df[
        (results_df["depletion_fraction_p"] == baseline_row["depletion_fraction_p"])
        & (results_df["kc_multiplier"] == baseline_row["kc_multiplier"])
    ].sort_values("root_depth_m")

    lines += [
        "| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | "
        "Mean depletion (mm) | High-stress days | Δ High-stress days |",
        "|---|---|---|---|---|---|---|",
    ]
    for _, row in rd_df.iterrows():
        lines.append(
            f"| **{row['root_depth_m']:.1f}** | {row['taw_mm']:.0f} | {row['raw_mm']:.0f} | "
            f"{row['mean_etc_mm_day']:.2f} | {row['mean_depletion_mm']:.1f} | "
            f"{row['n_days_high_stress']} ({row['pct_days_high_stress']:.1f}%) | "
            f"{fmt_delta(row['delta_n_high_stress'])} |"
        )

    lines += [
        "",
        "_Interpretation: larger root depth → higher TAW → soil holds more water → "
        "fewer High-stress days, but root depth is an assumption for this prototype "
        "and has not been measured at the study site._",
        "",
        "---",
        "",
        "## Sensitivity to depletion fraction *p*",
        "",
        "_Root depth and Kc multiplier held at baseline._",
        "",
    ]

    # --- depletion fraction table -----------------------------------------
    p_df = results_df[
        (results_df["root_depth_m"] == baseline_row["root_depth_m"])
        & (results_df["kc_multiplier"] == baseline_row["kc_multiplier"])
    ].sort_values("depletion_fraction_p")

    lines += [
        "| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | "
        "High-stress days | Δ High-stress days |",
        "|---|---|---|---|---|",
    ]
    for _, row in p_df.iterrows():
        lines.append(
            f"| **{row['depletion_fraction_p']:.2f}** | {row['raw_mm']:.0f} | "
            f"{row['mean_depletion_mm']:.1f} | "
            f"{row['n_days_high_stress']} ({row['pct_days_high_stress']:.1f}%) | "
            f"{fmt_delta(row['delta_n_high_stress'])} |"
        )

    lines += [
        "",
        "_Interpretation: higher p → higher RAW → stress threshold is harder to "
        "reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for "
        "fruit trees, but the true value for this orchard is unknown._",
        "",
        "---",
        "",
        "## Sensitivity to Kc multiplier",
        "",
        "_Root depth and depletion fraction held at baseline._",
        "",
    ]

    # --- Kc multiplier table ----------------------------------------------
    kc_df = results_df[
        (results_df["root_depth_m"] == baseline_row["root_depth_m"])
        & (results_df["depletion_fraction_p"] == baseline_row["depletion_fraction_p"])
    ].sort_values("kc_multiplier")

    lines += [
        "| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | "
        "High-stress days | Δ High-stress days |",
        "|---|---|---|---|---|---|",
    ]
    for _, row in kc_df.iterrows():
        lines.append(
            f"| **{row['kc_multiplier']:.2f}** | {row['mean_etc_mm_day']:.2f} | "
            f"{fmt_delta(row['delta_mean_etc'], ' mm/d')} | "
            f"{row['mean_depletion_mm']:.1f} | "
            f"{row['n_days_high_stress']} ({row['pct_days_high_stress']:.1f}%) | "
            f"{fmt_delta(row['delta_n_high_stress'])} |"
        )

    lines += [
        "",
        "_Interpretation: higher Kc → higher ETc → faster depletion → more "
        "High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the "
        "calibration uncertainty of the stage Kc values in this prototype._",
        "",
        "---",
        "",
        "## Most and least conservative scenarios",
        "",
    ]

    most_stress = results_df.loc[results_df["n_days_high_stress"].idxmax()]
    least_stress = results_df.loc[results_df["n_days_high_stress"].idxmin()]

    lines += [
        "### Worst case (most High-stress days)",
        "",
        f"- Root depth: {most_stress['root_depth_m']:.1f} m  |  "
        f"p: {most_stress['depletion_fraction_p']:.2f}  |  "
        f"Kc ×{most_stress['kc_multiplier']:.2f}",
        f"- High-stress days: **{most_stress['n_days_high_stress']}** "
        f"({most_stress['pct_days_high_stress']:.1f}%)",
        f"- Mean ETc: {most_stress['mean_etc_mm_day']:.2f} mm/day",
        f"- Mean depletion: {most_stress['mean_depletion_mm']:.1f} mm",
        "",
        "### Best case (fewest High-stress days)",
        "",
        f"- Root depth: {least_stress['root_depth_m']:.1f} m  |  "
        f"p: {least_stress['depletion_fraction_p']:.2f}  |  "
        f"Kc ×{least_stress['kc_multiplier']:.2f}",
        f"- High-stress days: **{least_stress['n_days_high_stress']}** "
        f"({least_stress['pct_days_high_stress']:.1f}%)",
        f"- Mean ETc: {least_stress['mean_etc_mm_day']:.2f} mm/day",
        f"- Mean depletion: {least_stress['mean_depletion_mm']:.1f} mm",
        "",
        "---",
        "",
        "## Full scenario table",
        "",
        "| Scenario | Root (m) | *p* | Kc× | Baseline? | "
        "Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for _, row in results_df.sort_values("scenario_id").iterrows():
        bl = "✓" if row["is_baseline"] else ""
        lines.append(
            f"| {int(row['scenario_id'])} | {row['root_depth_m']:.1f} | "
            f"{row['depletion_fraction_p']:.2f} | {row['kc_multiplier']:.2f} | "
            f"{bl} | {row['mean_etc_mm_day']:.2f} | {row['mean_depletion_mm']:.1f} | "
            f"{row['n_days_high_stress']} | {row['pct_days_high_stress']:.1f}% | "
            f"{fmt_delta(row['delta_mean_etc'])} | {fmt_delta(row['delta_mean_depletion'])} | "
            f"{fmt_delta(row['delta_n_high_stress'])} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Limitations and next steps",
        "",
        "- All parameters varied here are assumed, not measured at this orchard.",
        "- The water balance is rainfed-only — no irrigation events are tracked.",
        "- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates, "
        "  not measured profiles; this is a separate source of uncertainty not "
        "  explored in this analysis.",
        "- ET0 is the same across all scenarios (it does not depend on Kc, root "
        "  depth, or p), so ET0 sensitivity is not analysed here.",
        "- Suggested next steps: field measurement of root depth and soil-moisture "
        "  profiles; local agronomic literature on mango Kc for the Andhra Pradesh "
        "  region; cross-validation of stress periods against visible crop stress "
        "  indicators in the field.",
        "",
        "_Generated by src/validation/fao56_sensitivity_analysis.py._",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def build_fao56_sensitivity_analysis() -> bool:
    """
    Run the full FAO-56 sensitivity analysis and write outputs.

    Returns True on success, False if inputs are missing or malformed.
    """
    config = get_config()
    feature_table_path = config.path("combined_feature_table_csv")
    phenology_path = config.path("mango_phenology_calendar_csv")
    out_csv_path = config.path("fao56_sensitivity_analysis_csv")
    out_md_path = config.path("fao56_sensitivity_summary_md")

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

    log.info("Loaded %d feature-table rows, %d phenology rows.", len(feature_df), len(phenology_df))

    # --- join on date (inner) ---------------------------------------------
    joined_df = feature_df.merge(
        phenology_df[["date", "mango_stage"]],
        on="date",
        how="inner",
    ).sort_values("date").reset_index(drop=True)

    if joined_df.empty:
        print("\nNo overlapping dates — cannot run sensitivity analysis.")
        return False

    # --- read FAO-56 config -----------------------------------------------
    fao56_cfg = config._raw.get("fao56", {})
    baseline_root_depth = fao56_cfg.get("root_depth_m", 1.2)
    baseline_p = fao56_cfg.get("depletion_fraction_p", 0.50)
    elevation_m = fao56_cfg.get("elevation_m", 150)
    albedo = fao56_cfg.get("albedo", REFERENCE_ALBEDO_DEFAULT)
    phenology_kc_stages: dict = fao56_cfg.get("phenology_kc_stages", {})

    if not phenology_kc_stages:
        print("\nconfigs/config.yaml is missing fao56.phenology_kc_stages.")
        return False

    unknown = sorted(set(joined_df["mango_stage"].unique()) - set(phenology_kc_stages.keys()))
    if unknown:
        print(f"\nPhenology calendar has unmapped stage(s): {unknown}")
        return False

    # --- precompute shared arrays (fixed across all scenarios) ------------
    kc_per_day = joined_df["mango_stage"].map(phenology_kc_stages).to_numpy(dtype=float)
    et0_arr = compute_et0(
        joined_df,
        latitude_deg=config.latitude,
        elevation_m=elevation_m,
        albedo=albedo,
    ).to_numpy()
    rainfall_arr = joined_df["rainfall_mm"].fillna(0.0).to_numpy()

    sand_pct = joined_df["sand_percent"].iloc[0]
    clay_pct = joined_df["clay_percent"].iloc[0]
    org_carbon = joined_df["organic_carbon_g_kg"].iloc[0]

    n_days = len(joined_df)
    date_range_str = (
        f"{joined_df['date'].iloc[0].date()} - {joined_df['date'].iloc[-1].date()}"
    )

    log.info("Running %d scenarios over %d days (%s).",
             len(ROOT_DEPTH_VALUES) * len(DEPLETION_P_VALUES) * len(KC_MULTIPLIER_VALUES),
             n_days, date_range_str)

    # --- run full factorial -----------------------------------------------
    scenario_rows = []
    scenario_id = 1
    for root_d, dep_p, kc_mult in product(ROOT_DEPTH_VALUES, DEPLETION_P_VALUES, KC_MULTIPLIER_VALUES):
        stats = _run_scenario(
            et0=et0_arr,
            kc_per_day=kc_per_day,
            rainfall=rainfall_arr,
            sand_pct=sand_pct,
            clay_pct=clay_pct,
            org_carbon=org_carbon,
            root_depth_m=root_d,
            depletion_fraction_p=dep_p,
            kc_multiplier=kc_mult,
        )
        is_baseline = (
            abs(root_d - baseline_root_depth) < 1e-9
            and abs(dep_p - baseline_p) < 1e-9
            and abs(kc_mult - 1.0) < 1e-9
        )
        row = {
            "scenario_id": scenario_id,
            "root_depth_m": root_d,
            "depletion_fraction_p": dep_p,
            "kc_multiplier": kc_mult,
            "is_baseline": is_baseline,
        }
        row.update(stats)
        scenario_rows.append(row)
        scenario_id += 1

    results_df = pd.DataFrame(scenario_rows)

    # --- compute deltas from baseline ------------------------------------
    bl = results_df[results_df["is_baseline"]].iloc[0]
    results_df["delta_mean_etc"] = (results_df["mean_etc_mm_day"] - bl["mean_etc_mm_day"]).round(4)
    results_df["delta_mean_depletion"] = (results_df["mean_depletion_mm"] - bl["mean_depletion_mm"]).round(2)
    results_df["delta_n_high_stress"] = (
        results_df["n_days_high_stress"] - bl["n_days_high_stress"]
    ).astype(int)

    # --- write CSV --------------------------------------------------------
    out_csv_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(out_csv_path, index=False)
    log.info("Wrote sensitivity analysis CSV: %s (%d rows)", out_csv_path, len(results_df))

    # --- write markdown ---------------------------------------------------
    md_text = _build_markdown_summary(results_df, bl, date_range_str, n_days)
    out_md_path.write_text(md_text, encoding="utf-8")
    log.info("Wrote sensitivity summary markdown: %s", out_md_path)

    # --- console summary --------------------------------------------------
    stress_range = (
        results_df["n_days_high_stress"].min(),
        results_df["n_days_high_stress"].max(),
    )
    etc_range = (
        results_df["mean_etc_mm_day"].min(),
        results_df["mean_etc_mm_day"].max(),
    )
    dep_range = (
        results_df["mean_depletion_mm"].min(),
        results_df["mean_depletion_mm"].max(),
    )

    print()
    print("=" * 62)
    print("FAO-56 Sensitivity Analysis - console summary")
    print("=" * 62)
    print(f"  Date range:         {date_range_str}")
    print(f"  Days analysed:      {n_days}")
    print(f"  Scenarios run:      {len(results_df)}")
    print(f"  (root_depth x p x kc_mult = "
          f"{len(ROOT_DEPTH_VALUES)}x{len(DEPLETION_P_VALUES)}x{len(KC_MULTIPLIER_VALUES)})")
    print()
    print("  Baseline scenario:")
    print(f"    root_depth_m={baseline_root_depth}, p={baseline_p}, kc_mult=1.00")
    print(f"    Mean ETc:      {bl['mean_etc_mm_day']:.2f} mm/day")
    print(f"    Mean depletion:{bl['mean_depletion_mm']:.1f} mm")
    print(f"    High-stress:   {bl['n_days_high_stress']} days ({bl['pct_days_high_stress']:.1f}%)")
    print()
    print("  Range across all 36 scenarios:")
    print(f"    Mean ETc:      {etc_range[0]:.2f} - {etc_range[1]:.2f} mm/day")
    print(f"    Mean depletion:{dep_range[0]:.1f} - {dep_range[1]:.1f} mm")
    print(f"    High-stress:   {stress_range[0]} - {stress_range[1]} days")
    print()
    print("  Most conservative (most stress):")
    worst = results_df.loc[results_df["n_days_high_stress"].idxmax()]
    print(f"    root={worst['root_depth_m']:.1f}m, p={worst['depletion_fraction_p']:.2f}, "
          f"kc x{worst['kc_multiplier']:.2f} -> "
          f"{worst['n_days_high_stress']} High-stress days ({worst['pct_days_high_stress']:.1f}%)")
    print()
    print("  Least conservative (least stress):")
    best = results_df.loc[results_df["n_days_high_stress"].idxmin()]
    print(f"    root={best['root_depth_m']:.1f}m, p={best['depletion_fraction_p']:.2f}, "
          f"kc x{best['kc_multiplier']:.2f} -> "
          f"{best['n_days_high_stress']} High-stress days ({best['pct_days_high_stress']:.1f}%)")
    print()
    print("  Outputs:")
    print(f"    {out_csv_path}")
    print(f"    {out_md_path}")
    print("=" * 62)

    return True


def main() -> None:
    log.info("Running FAO-56 sensitivity analysis …")
    success = build_fao56_sensitivity_analysis()
    if success:
        log.info("FAO-56 sensitivity analysis completed successfully.")
    else:
        log.error("FAO-56 sensitivity analysis did not complete — see messages above.")


if __name__ == "__main__":
    main()
