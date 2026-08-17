"""
Aggregate the Sentinel-1 SAR backscatter time series into one row per day.

WHAT THIS FILE DOES (and does NOT do):
  - Reads the image-level time series CSV that
    build_sentinel1_sar_timeseries.py produced (one row per Sentinel-1
    scene), and collapses any duplicate dates into a single daily row.
  - Adds two beginner-friendly interpretation columns (vv_level, vh_level)
    so the numbers are easier to read at a glance.
  - It does NOT talk to Earth Engine, download imagery, modify the
    dashboard, or touch main.py. Pure CSV-in, CSV-out.

WHY DUPLICATE DATES HAPPEN
  Sentinel-1 can produce more than one scene per calendar date if both
  ASCENDING and DESCENDING orbit passes cover the study area on the same
  day, or if adjacent bursts within the same pass overlap. This script
  collapses them into one daily average.

HOW DUPLICATES ARE COMBINED
  - vv_mean, vh_mean, vv_vh_ratio_mean: averaged across all scenes that day.
  - orbit_pass: the mode (most frequent) pass direction that day.
  - scene_count: number of scenes averaged for that date.
  - latitude, longitude, buffer_m: identical for every row; first value kept.

INTERPRETATION THRESHOLDS (proxy labels — rough guidance, NOT calibrated
field measurements; the real numeric values are also kept in the output):

  vv_level (surface/soil roughness proxy, dB):
    < -18 dB   -> "Low backscatter (smoother surface or dry soil)"
    -18 to -12 -> "Moderate backscatter"
    > -12 dB   -> "High backscatter (rougher surface or wet soil)"

  vh_level (vegetation volume proxy, dB):
    < -24 dB   -> "Low volume scattering (sparse canopy or dry conditions)"
    -24 to -18 -> "Moderate volume scattering"
    > -18 dB   -> "Higher volume scattering (denser canopy or wet conditions)"

  IMPORTANT: these thresholds are broad global proxies. They have NOT been
  calibrated against field observations at Muthukur or for mango orchards.
  Treat them as indicative directional signals, not precise measurements.

HOW TO USE THIS FILE
  Run after build_sentinel1_sar_timeseries.py has produced the image-level CSV:
      python src/remote_sensing/aggregate_sentinel1_timeseries.py

  No Earth Engine connection is needed — it only reads and reshapes the CSV.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.utils.logger import get_logger

log = get_logger(__name__)

INPUT_CSV_PATH = Path("data/processed/muthukur_sentinel1_sar_timeseries.csv")
OUTPUT_CSV_PATH = Path("data/processed/muthukur_sentinel1_daily_indices.csv")

REQUIRED_INPUT_COLUMNS = [
    "date",
    "image_id",
    "orbit_pass",
    "vv_mean",
    "vh_mean",
    "vv_vh_ratio_mean",
    "latitude",
    "longitude",
    "buffer_m",
]

# Thresholds for VV backscatter (dB) — surface/soil roughness proxy.
VV_MODERATE_THRESHOLD = -18.0
VV_HIGH_THRESHOLD = -12.0

# Thresholds for VH backscatter (dB) — vegetation volume proxy.
VH_MODERATE_THRESHOLD = -24.0
VH_HIGH_THRESHOLD = -18.0


def _vv_level(value) -> str:
    """Rough proxy label for VV backscatter (surface/soil roughness signal)."""
    if value is None or value != value:  # NaN check without numpy
        return "Unknown"
    if value < VV_MODERATE_THRESHOLD:
        return "Low backscatter (smoother surface or dry soil)"
    if value <= VV_HIGH_THRESHOLD:
        return "Moderate backscatter"
    return "High backscatter (rougher surface or wet soil)"


def _vh_level(value) -> str:
    """Rough proxy label for VH backscatter (vegetation volume signal)."""
    if value is None or value != value:
        return "Unknown"
    if value < VH_MODERATE_THRESHOLD:
        return "Low volume scattering (sparse canopy or dry conditions)"
    if value <= VH_HIGH_THRESHOLD:
        return "Moderate volume scattering"
    return "Higher volume scattering (denser canopy or wet conditions)"


def aggregate_timeseries() -> bool:
    """
    Read the image-level Sentinel-1 SAR CSV, collapse duplicate dates into
    one row per day, add interpretation columns, and write the daily CSV.

    Returns True on success, False if the input file is missing or malformed
    — always with a clear, friendly explanation printed first.
    """

    import pandas as pd

    if not INPUT_CSV_PATH.exists():
        print()
        print(f"Input file not found: {INPUT_CSV_PATH}")
        print("Run build_sentinel1_sar_timeseries.py first to create it.")
        return False

    try:
        df = pd.read_csv(INPUT_CSV_PATH)
    except Exception as exc:
        log.error("Could not read %s: %s", INPUT_CSV_PATH, exc)
        print()
        print(f"Could not read {INPUT_CSV_PATH}.")
        print(f"Details: {exc}")
        return False

    missing_columns = [col for col in REQUIRED_INPUT_COLUMNS if col not in df.columns]
    if missing_columns:
        print()
        print(f"Input file is missing expected columns: {missing_columns}")
        print(f"Found columns: {list(df.columns)}")
        print("Re-run build_sentinel1_sar_timeseries.py to regenerate the file.")
        return False

    input_rows = len(df)
    unique_dates = df["date"].nunique()
    duplicate_date_count = input_rows - unique_dates

    log.info(
        "Read %d image-level rows covering %d unique dates.", input_rows, unique_dates
    )
    log.info(
        "Dates with more than one scene (combined into one row): %d",
        duplicate_date_count,
    )

    daily = (
        df.groupby("date", as_index=False)
        .agg(
            vv_mean=("vv_mean", "mean"),
            vh_mean=("vh_mean", "mean"),
            vv_vh_ratio_mean=("vv_vh_ratio_mean", "mean"),
            orbit_pass=("orbit_pass", lambda x: x.mode()[0] if len(x) > 0 else "UNKNOWN"),
            scene_count=("image_id", "count"),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            buffer_m=("buffer_m", "first"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    daily["vv_level"] = daily["vv_mean"].apply(_vv_level)
    daily["vh_level"] = daily["vh_mean"].apply(_vh_level)

    try:
        OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        log.error(
            "Could not create output folder %s: %s", OUTPUT_CSV_PATH.parent, exc
        )
        print()
        print(f"Could not create the output folder: {OUTPUT_CSV_PATH.parent}")
        print(f"Details: {exc}")
        return False

    daily.to_csv(OUTPUT_CSV_PATH, index=False)

    output_rows = len(daily)
    log.info("Wrote %d daily rows to %s", output_rows, OUTPUT_CSV_PATH)

    print()
    print(f"Input rows (one per scene):      {input_rows}")
    print(f"Output rows (one per day):       {output_rows}")
    print(f"Dates with multiple scenes:      {duplicate_date_count}")
    print(f"Saved Sentinel-1 daily CSV to: {OUTPUT_CSV_PATH}")
    print()
    print("Reminder: VV/VH values are radar backscatter proxy signals (dB).")
    print("They are NOT calibrated field measurements or optical vegetation indices.")
    return True


def main():
    log.info(
        "Aggregating Sentinel-1 SAR backscatter time series into daily rows..."
    )
    success = aggregate_timeseries()

    if success:
        log.info("Sentinel-1 daily aggregation completed successfully.")
    else:
        log.info(
            "Sentinel-1 daily aggregation did not complete. See messages above."
        )


if __name__ == "__main__":
    main()
