"""
Build one combined weather + soil + vegetation feature table.

WHAT THIS FILE DOES (and does NOT do):
  - Reads the existing processed historical weather/risk CSV, the daily
    Sentinel-2 vegetation CSV, and the raw SoilGrids CSV.
  - Joins them into a single tabular dataset: one row per historical
    weather date, with the closest available vegetation observation and
    the (constant) soil properties attached.
  - It does NOT call any external API, does NOT touch main.py, does NOT
    change the Streamlit dashboard, and does NOT download any satellite
    imagery. It only reads three CSVs that earlier standalone scripts
    already produced, and writes one new CSV.

WHY "NEAREST PREVIOUS" SENTINEL-2 OBSERVATION (not nearest future one)
  Sentinel-2 doesn't take a picture every day — usable cloud-free scenes
  are scattered across the date range (see the daily vegetation CSV: 54
  daily rows covering a date range with hundreds of calendar days). For
  every weather date we need to pick *some* vegetation reading to attach
  to it, but it would be misleading to use a satellite image taken
  *after* that weather date — that would let the model "see the future"
  (e.g. explaining a hot, dry week in early April using a satellite image
  taken in late April, after the orchard had already responded to that
  heat). Using only the most recent *previous* scene keeps the dataset
  honest: every row only uses information that was actually available by
  that date. This is the same reasoning a weather forecaster uses when
  backtesting a model — never let it peek at data from after the moment
  it's making a call about.

WHY A FRESHNESS FLAG
  Because Sentinel-2 doesn't image every day, "the nearest previous
  observation" might be from a few days ago (great) or several weeks ago
  (stale, vegetation conditions may have changed a lot since then). The
  `days_since_sentinel2_observation` and `vegetation_data_freshness`
  columns make that staleness visible in the data itself, instead of
  hiding it. Downstream analysis (or, much later, any modeling) can then
  choose to trust, down-weight, or ignore stale vegetation rows.

INPUTS
  data/processed/muthukur_weather_risk_scores.csv  (historical weather/risk)
  data/processed/muthukur_sentinel2_daily_indices.csv (daily vegetation)
  data/raw/muthukur_soilgrids.csv                  (static SoilGrids data)
  data/processed/muthukur_sentinel1_daily_indices.csv (optional SAR fallback)

OUTPUT
  data/processed/muthukur_combined_feature_table.csv

HOW TO USE THIS FILE
  Run after the historical risk engine, the Sentinel-2 daily aggregation
  step, and the SoilGrids fetch have all produced their CSVs at least
  once:

      python src/features/build_feature_table.py

  This is a standalone script only — it is not wired into main.py or the
  dashboard. Nothing downstream depends on it yet.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.soil_factor import calculate_soil_irrigation_factor
from src.utils.validation import (
    MissingColumnsError,
    validate_risk_data,
    validate_soil_data,
    validate_vegetation_data,
)

log = get_logger(__name__)

# Freshness thresholds, in days since the nearest previous Sentinel-2
# observation. Simple, fixed buckets so the freshness label is easy to
# scan in the output CSV — not a scientific standard.
FRESH_MAX_DAYS = 7
MODERATE_MAX_DAYS = 15

# Static soil properties we pull out of the SoilGrids long-format CSV and
# attach as their own named columns on every output row.
SOIL_OUTPUT_COLUMNS = {
    "sand": "sand_percent",
    "silt": "silt_percent",
    "clay": "clay_percent",
    "phh2o": "ph",
    "soc": "organic_carbon_g_kg",
    "bdod": "bulk_density_g_cm3",
    "cec": "cec_cmol_kg",
}

VEGETATION_OUTPUT_COLUMNS = [
    "sentinel2_date",
    "ndvi_mean",
    "ndwi_mean",
    "ndmi_mean",
    "ndre_mean",
    "ndvi_level",
    "moisture_level",
    "canopy_stress_level",
    "cloud_percentage",
    "scene_count",
]

# Sentinel-1 SAR columns added by the optional nearest-prior join.
# Kept separate so the S2 join logic is unchanged even when S1 is absent.
SENTINEL1_OUTPUT_COLUMNS = [
    "sentinel1_date",
    "vv_mean",
    "vh_mean",
    "vv_vh_ratio_mean",
    "orbit_pass",
    "scene_count_s1",  # renamed from scene_count to avoid collision with S2
]

# Freshness thresholds for Sentinel-1 (same bucket widths as S2 for consistency).
S1_FRESH_MAX_DAYS = 7
S1_MODERATE_MAX_DAYS = 15


def _freshness_label(days) -> str:
    """Turn days-since-observation into a beginner-friendly freshness label."""
    if days is None or days != days:  # NaN check without importing numpy here
        return "Missing"
    if days <= FRESH_MAX_DAYS:
        return "Fresh"
    if days <= MODERATE_MAX_DAYS:
        return "Moderate"
    return "Stale"


def _s1_freshness_label(days) -> str:
    """Turn days-since-Sentinel-1-observation into a freshness label."""
    if days is None or days != days:  # NaN check
        return "Missing"
    if days <= S1_FRESH_MAX_DAYS:
        return "Fresh"
    if days <= S1_MODERATE_MAX_DAYS:
        return "Moderate"
    return "Stale"


def _load_weather_risk(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Historical weather/risk file not found: {path}\n"
            "Run the main pipeline first (python main.py or "
            "python main.py --skip-fetch) to create it."
        )
    df = pd.read_csv(path)
    validate_risk_data(df)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def _load_vegetation(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Daily Sentinel-2 vegetation file not found: {path}\n"
            "Run python src/remote_sensing/build_sentinel2_index_timeseries.py "
            "and then python src/remote_sensing/aggregate_sentinel2_timeseries.py "
            "first to create it."
        )
    df = pd.read_csv(path)
    validate_vegetation_data(df)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def _load_soil_lookup(path: Path) -> dict:
    """
    Read the SoilGrids long-format CSV (one row per property x depth) and
    collapse it into one 0-30cm average value per property, the same
    "topsoil summary" approach already used on the dashboard's Soil
    Intelligence page, so the soil numbers shown everywhere in this
    project stay consistent.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"SoilGrids file not found: {path}\n"
            "Run python src/soil/fetch_soilgrids.py first to create it."
        )
    df = pd.read_csv(path)
    validate_soil_data(df)

    topsoil_summary = df.groupby("property", as_index=False).agg(
        average_0_30cm=("converted_value", "mean")
    )
    return dict(zip(topsoil_summary["property"], topsoil_summary["average_0_30cm"]))


def _load_sentinel1(path: Path) -> pd.DataFrame | None:
    """
    Load the daily Sentinel-1 SAR CSV. Returns None (with a warning) if the
    file does not exist — the S1 join is optional; the feature table can be
    built without it during cloudy periods or before the first SAR refresh.
    """
    if not path.exists():
        log.warning(
            "Sentinel-1 daily SAR file not found at %s — "
            "SAR columns will be omitted from the feature table. "
            "Run python src/remote_sensing/build_sentinel1_sar_timeseries.py "
            "followed by aggregate_sentinel1_timeseries.py to create it.",
            path,
        )
        return None
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        log.warning("Could not read Sentinel-1 SAR file %s: %s — skipping S1 join.", path, exc)
        return None

    required_s1_cols = ["date", "vv_mean", "vh_mean", "vv_vh_ratio_mean", "orbit_pass", "scene_count"]
    missing = [c for c in required_s1_cols if c not in df.columns]
    if missing:
        log.warning(
            "Sentinel-1 SAR file %s is missing columns %s — skipping S1 join.",
            path, missing,
        )
        return None

    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def build_feature_table() -> bool:
    """
    Join historical weather/risk, daily Sentinel-2 vegetation, and static
    SoilGrids soil data into one combined feature table CSV.

    Returns True on success, False if any input is missing/malformed —
    always with a clear, friendly explanation printed first.
    """

    config = get_config()

    weather_path = config.path("historical_risk_csv")
    vegetation_path = config.path("sentinel2_daily_csv")
    soil_path = config.path("soilgrids_csv")
    output_path = config.path("combined_feature_table_csv")
    sentinel1_path = config.path("sentinel1_daily_csv")

    try:
        weather_df = _load_weather_risk(weather_path)
    except (FileNotFoundError, MissingColumnsError) as exc:
        print()
        print(str(exc))
        return False

    try:
        vegetation_df = _load_vegetation(vegetation_path)
    except (FileNotFoundError, MissingColumnsError) as exc:
        print()
        print(str(exc))
        return False

    try:
        soil_lookup = _load_soil_lookup(soil_path)
    except (FileNotFoundError, MissingColumnsError) as exc:
        print()
        print(str(exc))
        return False

    sentinel1_df = _load_sentinel1(sentinel1_path)

    log.info("Loaded %d historical weather/risk rows from %s", len(weather_df), weather_path)
    log.info("Loaded %d daily vegetation rows from %s", len(vegetation_df), vegetation_path)
    log.info("Loaded soil properties for %d properties from %s", len(soil_lookup), soil_path)
    if sentinel1_df is not None:
        log.info("Loaded %d daily Sentinel-1 SAR rows from %s", len(sentinel1_df), sentinel1_path)
    else:
        log.info("Sentinel-1 SAR data not available — SAR columns will be omitted.")

    # Rename vegetation's "date" to "sentinel2_date" before the join, so the
    # output keeps both: the weather date (the row's own date) and the date
    # of the satellite observation actually used for that row.
    vegetation_for_merge = vegetation_df.rename(columns={"date": "sentinel2_date"})

    # The core join: for every weather date, attach the most recent
    # Sentinel-2 observation that happened on or before that date.
    # merge_asof with direction="backward" guarantees we only ever look
    # backward in time, never forward (see module docstring for why).
    combined = pd.merge_asof(
        weather_df,
        vegetation_for_merge,
        left_on="date",
        right_on="sentinel2_date",
        direction="backward",
    )

    combined["days_since_sentinel2_observation"] = (
        combined["date"] - combined["sentinel2_date"]
    ).dt.days

    combined["vegetation_data_freshness"] = combined["days_since_sentinel2_observation"].apply(
        _freshness_label
    )

    # Optional Sentinel-1 SAR nearest-prior join.
    # Same direction="backward" logic as S2: never let a row see a SAR
    # observation taken *after* its weather date.
    if sentinel1_df is not None:
        s1_for_merge = (
            sentinel1_df
            .rename(columns={
                "date": "sentinel1_date",
                "scene_count": "scene_count_s1",
            })
        )
        combined = pd.merge_asof(
            combined,
            s1_for_merge,
            left_on="date",
            right_on="sentinel1_date",
            direction="backward",
        )
        combined["days_since_sentinel1_observation"] = (
            combined["date"] - combined["sentinel1_date"]
        ).dt.days
        combined["sentinel1_freshness_level"] = (
            combined["days_since_sentinel1_observation"].apply(_s1_freshness_label)
        )
    else:
        # S1 not available: add placeholder columns so downstream code can
        # reference the column names without KeyError.
        for col in SENTINEL1_OUTPUT_COLUMNS:
            combined[col] = None
        combined["days_since_sentinel1_observation"] = None
        combined["sentinel1_freshness_level"] = "Missing"

    # Attach the constant (whole-study-area) soil properties to every row.
    for soilgrids_property, output_column in SOIL_OUTPUT_COLUMNS.items():
        combined[output_column] = soil_lookup.get(soilgrids_property)

    # Reuse the exact same shared soil-irrigation-factor calculation used
    # by both risk engines and the dashboard, so this column matches the
    # "soil_irrigation_factor" already present in the weather/risk input
    # (same soil values, same formula -> same number, just confirmed here
    # rather than recomputed differently).
    combined["soil_irrigation_factor"] = calculate_soil_irrigation_factor(soil_lookup)

    # Column order: original weather/risk columns first (unchanged), then
    # vegetation columns + freshness info, then the static soil columns.
    weather_columns = list(weather_df.columns)
    vegetation_columns = [c for c in VEGETATION_OUTPUT_COLUMNS if c in combined.columns]
    soil_columns = list(SOIL_OUTPUT_COLUMNS.values())

    sentinel1_columns = [c for c in SENTINEL1_OUTPUT_COLUMNS if c in combined.columns]
    s1_freshness_columns = [
        "days_since_sentinel1_observation",
        "sentinel1_freshness_level",
    ]

    ordered_columns = (
        weather_columns
        + vegetation_columns
        + ["days_since_sentinel2_observation", "vegetation_data_freshness"]
        + sentinel1_columns
        + s1_freshness_columns
        + soil_columns
    )
    combined = combined[ordered_columns]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_path, index=False)

    total_rows = len(combined)
    matched_rows = combined["sentinel2_date"].notna().sum()
    missing_rows = total_rows - matched_rows
    freshness_counts = combined["vegetation_data_freshness"].value_counts().to_dict()
    coverage_percent = (matched_rows / total_rows * 100) if total_rows else 0.0

    log.info("Combined feature table: %d output rows.", total_rows)
    log.info(
        "Vegetation match coverage: %d/%d rows (%.1f%%) have a matched Sentinel-2 observation.",
        matched_rows,
        total_rows,
        coverage_percent,
    )
    log.info("Freshness breakdown: %s", freshness_counts)
    log.info("Wrote combined feature table to %s", output_path)

    print()
    print(f"Weather/risk input rows:          {len(weather_df)}")
    print(f"Daily vegetation input rows:       {len(vegetation_df)}")
    print(f"Output rows:                       {total_rows}")
    print(
        f"Vegetation match coverage:        {matched_rows}/{total_rows} rows "
        f"({coverage_percent:.1f}%)"
    )
    print(f"Rows with no prior Sentinel-2 obs: {missing_rows}")
    print(f"Freshness breakdown:               {freshness_counts}")
    print(f"Saved combined feature table to: {output_path}")
    print()
    print("This is still a standalone file — not yet wired into main.py")
    print("or the dashboard.")
    return True


def main():
    log.info("Building combined weather + soil + vegetation feature table...")
    success = build_feature_table()

    if success:
        log.info("Combined feature table build completed successfully.")
    else:
        log.info("Combined feature table build did not complete. See messages above.")


if __name__ == "__main__":
    main()
