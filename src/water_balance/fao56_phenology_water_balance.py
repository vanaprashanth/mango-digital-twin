"""
Standalone, PHENOLOGY-AWARE FAO-56 soil-water balance script.

WHAT THIS FILE DOES (and does NOT do):
  - Reads the existing combined weather + soil + vegetation feature table
    (data/processed/muthukur_combined_feature_table.csv).
  - Reads the existing standalone mango phenology calendar
    (data/processed/muthukur_mango_phenology_calendar.csv).
  - Joins the two tables on `date`, so every day gets both its weather/soil
    inputs AND its mango growth stage for that calendar date.
  - Looks up a crop coefficient (Kc) PER GROWTH STAGE instead of using one
    constant Kc for the whole date range.
  - Runs the same FAO-56 reference evapotranspiration (ET0) and root-zone
    soil-water depletion balance logic as the existing standalone script
    (src/water_balance/fao56_water_balance.py) — re-using its functions
    directly by importing them, instead of copy-pasting the math, so both
    scripts always agree on ET0/depletion mechanics.
  - Writes one NEW CSV:
    data/processed/muthukur_fao56_phenology_water_balance.csv
  - It does NOT overwrite or modify the existing
    data/processed/muthukur_fao56_water_balance.csv file, does NOT modify
    src/water_balance/fao56_water_balance.py, does NOT touch main.py, and
    does NOT change the Streamlit dashboard. It only reads two CSVs that
    earlier standalone scripts already produced, and writes one new CSV.

IMPORTANT — BEGINNER-FRIENDLY NOTE ABOUT Kc VALUES
  The six stage-based Kc values below (configs/config.yaml ->
  fao56.phenology_kc_stages) are FIRST-PASS ASSUMPTIONS, based on general
  mango/FAO-56 crop-coefficient guidance (FAO-56 Table 12 lists mango Kc
  roughly in the 0.5-0.85 range across the season). They are:
    - NOT field-calibrated for this specific orchard.
    - NOT cultivar-specific (e.g. Banganapalli vs. Totapuri vs. Alphonso
      can bloom/fruit at different times and may need different Kc).
    - NOT validated against any measured soil-moisture or sap-flow data.
  Treat the output of this script as a directional, exploratory signal —
  "Kc probably looks something like this across the season" — not a precise
  irrigation prescription. Refining these values (e.g. from local
  agronomic literature or field measurements) is expected future work.

WHY A SEPARATE SCRIPT INSTEAD OF EDITING THE EXISTING ONE
  The existing fao56_water_balance.py is left completely untouched on
  purpose. This lets the project compare "constant Kc=0.75" results against
  "stage-aware Kc" results side by side later, and means nothing that
  already works (including the dashboard's Water Balance page) is put at
  risk while this stage-aware approach is still experimental.

JOIN LOGIC
  The combined feature table and the phenology calendar can have slightly
  different date ranges (the phenology calendar is a generic calendar that
  may extend further into the future or past than the actual weather
  record). This script does an INNER join on `date` — only dates present in
  BOTH tables are kept — so every output row always has both a real
  weather-driven ET0/ETc AND a known growth stage. Dates that fail to match
  are dropped silently from the join itself, but the row counts of each
  input table and the final joined table are logged and printed so it's
  obvious if the overlap was smaller than expected.

REFERENCE
  Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). "Crop
  Evapotranspiration - Guidelines for computing crop water requirements."
  FAO Irrigation and Drainage Paper No. 56. Same equations as used by
  src/water_balance/fao56_water_balance.py (ET0 = eq 6; TAW/RAW/depletion =
  eq 82-85) — see that file's docstring for the full equation-by-equation
  explanation. This file only changes STEP 2 (ETc = ET0 * Kc): Kc is now
  looked up per day based on that day's mango_stage, instead of being one
  constant for every day.

INPUT
  data/processed/muthukur_combined_feature_table.csv
  data/processed/muthukur_mango_phenology_calendar.csv

OUTPUT
  data/processed/muthukur_fao56_phenology_water_balance.csv

HOW TO USE THIS FILE
  Run after BOTH the combined feature table and the phenology calendar have
  already been built at least once:

      python src/features/build_feature_table.py
      python src/phenology/mango_phenology_calendar.py
      python src/water_balance/fao56_phenology_water_balance.py

  This is a standalone script only — it is not wired into main.py or the
  dashboard. Nothing downstream depends on it yet.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validation import (
    MissingColumnsError,
    validate_fao56_input,
    validate_fao56_phenology_output,
    validate_phenology_output,
)

# Re-use the existing FAO-56 script's ET0 math and soil pedotransfer function
# directly, instead of duplicating it here. This guarantees both the
# constant-Kc script and this phenology-aware script compute ET0/TAW/RAW
# identically — only the Kc lookup and the resulting ETc/depletion differ.
from src.water_balance.fao56_water_balance import (
    REFERENCE_ALBEDO_DEFAULT,
    _field_capacity_and_wilting_point,
    _water_stress_label,
    compute_et0,
)

log = get_logger(__name__)


def _load_combined_feature_table(path: Path) -> pd.DataFrame:
    """Load and validate the combined weather/soil/vegetation feature table."""
    if not path.exists():
        raise FileNotFoundError(
            f"Combined feature table not found: {path}\n"
            "Run python src/features/build_feature_table.py first to create it."
        )
    df = pd.read_csv(path)
    # Re-use the existing FAO-56 input validator: it checks for the
    # temperature/humidity/rainfall/solar/wind/soil columns this script's
    # ET0 and water-balance math needs.
    validate_fao56_input(df)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def _load_phenology_calendar(path: Path) -> pd.DataFrame:
    """Load and validate the standalone mango phenology calendar."""
    if not path.exists():
        raise FileNotFoundError(
            f"Mango phenology calendar not found: {path}\n"
            "Run python src/phenology/mango_phenology_calendar.py first to create it."
        )
    df = pd.read_csv(path)
    validate_phenology_output(df)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def _kc_lookup_series(mango_stage: pd.Series, phenology_kc_stages: dict) -> pd.Series:
    """
    Map each row's mango_stage string to a Kc value using the
    configs/config.yaml -> fao56.phenology_kc_stages dictionary.

    Raises a clear, beginner-friendly error if a stage name shows up in the
    phenology calendar that this dictionary doesn't have a Kc value for —
    this should not normally happen since both files come from this same
    project, but it's checked explicitly rather than silently filling in a
    default, since silently guessing a Kc would be misleading.
    """
    unknown_stages = sorted(set(mango_stage.unique()) - set(phenology_kc_stages.keys()))
    if unknown_stages:
        raise MissingColumnsError(
            f"Mango phenology calendar contains stage name(s) with no configured "
            f"Kc value: {unknown_stages}.\n"
            f"Known stages in configs/config.yaml -> fao56.phenology_kc_stages: "
            f"{sorted(phenology_kc_stages.keys())}.\n"
            "Update configs/config.yaml -> fao56.phenology_kc_stages to add the "
            "missing stage(s), or check that the phenology calendar script "
            "hasn't introduced a renamed/new stage label."
        )
    return mango_stage.map(phenology_kc_stages)


def compute_phenology_water_balance(
    joined_df: pd.DataFrame,
    et0: pd.Series,
    kc: pd.Series,
    root_depth_m: float,
    depletion_fraction_p: float,
) -> pd.DataFrame:
    """
    Compute ETc and the daily root-zone soil-water balance using a
    PER-DAY Kc (one value per row, looked up from that day's mango growth
    stage), instead of one constant Kc for every day.

    This mirrors src/water_balance/fao56_water_balance.py's
    compute_water_balance() function as closely as possible — same TAW/RAW/
    depletion/Ks equations (FAO-56 eq 82-85) — the only difference is that
    `kc` is a per-row Series here instead of a single float.
    """

    etc = et0 * kc  # ETc = ET0 * Kc(stage), per day (FAO-56 eq for ETc)

    theta_fc, theta_wp = _field_capacity_and_wilting_point(
        sand_percent=joined_df["sand_percent"].iloc[0],
        clay_percent=joined_df["clay_percent"].iloc[0],
        organic_carbon_g_kg=joined_df["organic_carbon_g_kg"].iloc[0],
    )

    taw_mm = 1000 * (theta_fc - theta_wp) * root_depth_m  # eq 82
    raw_mm = depletion_fraction_p * taw_mm  # eq 83

    rainfall = joined_df["rainfall_mm"].fillna(0).to_numpy()
    etc_values = etc.to_numpy()

    # Same day-by-day running depletion balance as the existing script:
    # depletion increases with ETc, decreases with rainfall, and is clamped
    # to [0, TAW] (no irrigation events tracked — see the existing script's
    # docstring for the full list of simplifications, which all still apply
    # here unchanged).
    depletion = np.zeros(len(joined_df))
    previous_depletion = 0.0  # assume the soil starts at field capacity
    for i in range(len(joined_df)):
        current_depletion = previous_depletion - rainfall[i] + etc_values[i]
        current_depletion = max(0.0, min(current_depletion, taw_mm))
        depletion[i] = current_depletion
        previous_depletion = current_depletion

    ks = np.where(
        depletion > raw_mm,
        (taw_mm - depletion) / max(taw_mm - raw_mm, 1e-9),
        1.0,
    )  # eq 84
    ks = np.clip(ks, 0.0, 1.0)

    # water_stress_score is just "1 - Ks": 0.0 means no stress, 1.0 means
    # maximum stress. This is the same information as Ks, just flipped so
    # "higher score = more stress", which some readers find more intuitive
    # than "higher Ks = less stress".
    water_stress_score = 1.0 - ks

    out = pd.DataFrame(
        {
            "date": joined_df["date"],
            "mango_stage": joined_df["mango_stage"],
            "kc": kc.to_numpy(),
            "et0_mm_day": et0.to_numpy(),
            "etc_mm_day": etc_values,
            "rainfall_mm": rainfall,
            "root_zone_depletion_mm": depletion,
            "taw_mm": taw_mm,
            "raw_mm": raw_mm,
            "ks": ks,
            "water_stress_score": water_stress_score,
        }
    )
    out["water_stress_level"] = out["ks"].apply(_water_stress_label)

    # Keep useful context columns if they're already available in the
    # combined feature table — these are NOT required, so missing ones are
    # simply skipped rather than causing an error.
    optional_context_columns = [
        "ndvi_mean",
        "ndmi_mean",
        "vegetation_data_freshness",
        "soil_irrigation_factor",
    ]
    for col in optional_context_columns:
        if col in joined_df.columns:
            out[col] = joined_df[col].to_numpy()

    return out


def build_fao56_phenology_water_balance() -> bool:
    """
    Build the phenology-aware (stage-based Kc) daily ET0/ETc/water-balance
    table by joining the combined feature table with the mango phenology
    calendar.

    Returns True on success, False if an input is missing/malformed —
    always with a clear, friendly explanation printed first.
    """

    config = get_config()
    feature_table_path = config.path("combined_feature_table_csv")
    phenology_path = config.path("mango_phenology_calendar_csv")
    output_path = config.path("fao56_phenology_water_balance_csv")

    try:
        feature_df = _load_combined_feature_table(feature_table_path)
    except (FileNotFoundError, MissingColumnsError) as exc:
        print()
        print(str(exc))
        return False

    try:
        phenology_df = _load_phenology_calendar(phenology_path)
    except (FileNotFoundError, MissingColumnsError) as exc:
        print()
        print(str(exc))
        return False

    log.info("Loaded %d combined feature table rows from %s", len(feature_df), feature_table_path)
    log.info("Loaded %d phenology calendar rows from %s", len(phenology_df), phenology_path)

    # Inner join on date: keep only dates that exist in BOTH input files, so
    # every output row has both real weather inputs and a known growth
    # stage. See the module docstring's "JOIN LOGIC" section.
    joined_df = feature_df.merge(
        phenology_df[["date", "mango_stage"]],
        on="date",
        how="inner",
    ).sort_values("date").reset_index(drop=True)

    if joined_df.empty:
        print()
        print(
            "No overlapping dates found between the combined feature table "
            f"({feature_df['date'].min().date()} to {feature_df['date'].max().date()}) "
            f"and the phenology calendar "
            f"({phenology_df['date'].min().date()} to {phenology_df['date'].max().date()}). "
            "Nothing to compute."
        )
        return False

    log.info(
        "Joined table has %d rows (inner join on date, out of %d feature-table rows "
        "and %d phenology rows).",
        len(joined_df), len(feature_df), len(phenology_df),
    )

    fao56_settings = config._raw.get("fao56", {})
    elevation_m = fao56_settings.get("elevation_m", 150)
    root_depth_m = fao56_settings.get("root_depth_m", 1.2)
    depletion_fraction_p = fao56_settings.get("depletion_fraction_p", 0.50)
    albedo = fao56_settings.get("albedo", REFERENCE_ALBEDO_DEFAULT)
    phenology_kc_stages = fao56_settings.get("phenology_kc_stages", {})

    if not phenology_kc_stages:
        print()
        print(
            "configs/config.yaml is missing the fao56.phenology_kc_stages section. "
            "Add stage-to-Kc mappings there before running this script."
        )
        return False

    try:
        kc = _kc_lookup_series(joined_df["mango_stage"], phenology_kc_stages)
    except MissingColumnsError as exc:
        print()
        print(str(exc))
        return False

    et0 = compute_et0(joined_df, latitude_deg=config.latitude, elevation_m=elevation_m, albedo=albedo)

    result = compute_phenology_water_balance(
        joined_df,
        et0=et0,
        kc=kc,
        root_depth_m=root_depth_m,
        depletion_fraction_p=depletion_fraction_p,
    )

    # Validate our own output before writing it, so a typo in a column name
    # above is caught here with a clear message instead of surfacing later
    # as a confusing KeyError somewhere downstream.
    validate_fao56_phenology_output(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)

    stage_counts = result["mango_stage"].value_counts().to_dict()
    stress_counts = result["water_stress_level"].value_counts().to_dict()
    kc_by_stage = result.groupby("mango_stage")["kc"].first().to_dict()

    log.info("Computed phenology-aware FAO-56 water balance for %d days.", len(result))
    log.info(
        "TAW=%.1f mm, RAW=%.1f mm (root depth=%.2f m, depletion fraction p=%.2f)",
        result["taw_mm"].iloc[0],
        result["raw_mm"].iloc[0],
        root_depth_m,
        depletion_fraction_p,
    )
    log.info("Mango stage day counts in joined range: %s", stage_counts)
    log.info("Kc used per stage: %s", kc_by_stage)
    log.info("Water stress level breakdown: %s", stress_counts)
    log.info("Wrote phenology-aware FAO-56 water balance table to %s", output_path)

    print()
    print(f"Combined feature table rows:   {len(feature_df)}")
    print(f"Phenology calendar rows:       {len(phenology_df)}")
    print(f"Joined (output) rows:          {len(result)}")
    print(f"Mean ET0 (mm/day):             {result['et0_mm_day'].mean():.2f}")
    print(f"Mean ETc (mm/day):             {result['etc_mm_day'].mean():.2f}")
    print(f"TAW (total available water):   {result['taw_mm'].iloc[0]:.1f} mm")
    print(f"RAW (readily available):       {result['raw_mm'].iloc[0]:.1f} mm")
    print(f"Mango stage day counts:        {stage_counts}")
    print(f"Kc used per stage:             {kc_by_stage}")
    print(f"Water stress level breakdown:  {stress_counts}")
    print(f"Saved phenology-aware FAO-56 water balance table to: {output_path}")
    print()
    print("Reminder: the Kc-per-stage values above are first-pass assumptions,")
    print("not field-calibrated or cultivar-specific yet (see this script's")
    print("module docstring). The original constant-Kc file")
    print("(muthukur_fao56_water_balance.csv) was NOT modified or overwritten.")
    print("This is still a standalone file — not yet wired into main.py")
    print("or the dashboard.")
    return True


def main():
    log.info("Building phenology-aware FAO-56 soil-water balance...")
    success = build_fao56_phenology_water_balance()

    if success:
        log.info("Phenology-aware FAO-56 water balance build completed successfully.")
    else:
        log.info("Phenology-aware FAO-56 water balance build did not complete. See messages above.")


if __name__ == "__main__":
    main()
