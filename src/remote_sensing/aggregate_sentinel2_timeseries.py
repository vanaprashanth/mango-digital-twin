"""
Aggregate the Sentinel-2 vegetation index time series into one row per day.

WHAT THIS FILE DOES (and does NOT do):
  - Reads the image-level time series CSV that
    build_sentinel2_index_timeseries.py produced (one row per Sentinel-2
    scene), and collapses any duplicate dates into a single daily row.
  - Adds three beginner-friendly interpretation columns (ndvi_level,
    moisture_level, canopy_stress_level) so the numbers are easier to read
    at a glance.
  - It does NOT talk to Earth Engine, download imagery, modify the
    dashboard, or touch main.py. It is a pure CSV-in, CSV-out script.

WHY DUPLICATE DATES HAPPEN
  Sentinel-2 satellites fly in overlapping orbital tiles, so the same
  calendar date can produce more than one scene over the study area (you
  can see this in the time series CSV — e.g. two rows for 2025-01-07).
  build_sentinel2_index_timeseries.py deliberately kept those as separate
  rows. This script is where they get combined into one daily value.

HOW DUPLICATES ARE COMBINED
  - ndvi_mean, ndwi_mean, ndmi_mean, ndre_mean: averaged (mean) across all
    scenes for that date.
  - cloud_percentage: also averaged (mean), not the minimum. Reasoning: the
    index values above are themselves an average across every scene that
    day, so the cloud_percentage should describe the same set of scenes
    those indices came from. Reporting only the single clearest scene's
    cloud cover (the minimum) would describe a different, smaller slice of
    the data than what the averaged indices represent — that would be
    misleading. Mean keeps the cloud-cover number honest about the whole
    day's contributing scenes.
  - scene_count: how many scenes were averaged together for that date, so
    you can see at a glance which days are based on one scene vs. several.
  - latitude, longitude, buffer_m: identical for every row already (same
    study area), so the first value is kept.

INTERPRETATION THRESHOLDS (beginner-friendly, not a scientific standard —
just a simple way to label the numbers; the real numeric values are kept
too, so nothing is hidden):
  ndvi_level:
    < 0.20            -> "Low vegetation greenness"
    0.20 to 0.45       -> "Moderate vegetation greenness"
    > 0.45            -> "High vegetation greenness"
  moisture_level (based on NDMI):
    < -0.20           -> "Dry vegetation / moisture stress"
    -0.20 to 0.10      -> "Moderate moisture"
    > 0.10            -> "Good moisture"
  canopy_stress_level (based on NDRE):
    < 0.10            -> "Possible low chlorophyll / canopy stress"
    0.10 to 0.25       -> "Moderate canopy condition"
    > 0.25            -> "Stronger canopy / chlorophyll signal"

HOW TO USE THIS FILE
  Run after build_sentinel2_index_timeseries.py has produced the image-level
  CSV:
      python src/remote_sensing/aggregate_sentinel2_timeseries.py

  No Earth Engine connection is needed for this step — it only reads and
  reshapes the CSV that script already saved.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.utils.logger import get_logger

log = get_logger(__name__)

INPUT_CSV_PATH = Path("data/processed/muthukur_sentinel2_index_timeseries.csv")
OUTPUT_CSV_PATH = Path("data/processed/muthukur_sentinel2_daily_indices.csv")

REQUIRED_INPUT_COLUMNS = [
    "date",
    "image_id",
    "cloud_percentage",
    "ndvi_mean",
    "ndwi_mean",
    "ndmi_mean",
    "ndre_mean",
    "latitude",
    "longitude",
    "buffer_m",
]


def _ndvi_level(value) -> str:
    if value is None or value != value:  # NaN check without importing numpy/pandas here
        return "Unknown"
    if value < 0.20:
        return "Low vegetation greenness"
    if value <= 0.45:
        return "Moderate vegetation greenness"
    return "High vegetation greenness"


def _moisture_level(value) -> str:
    if value is None or value != value:
        return "Unknown"
    if value < -0.20:
        return "Dry vegetation / moisture stress"
    if value <= 0.10:
        return "Moderate moisture"
    return "Good moisture"


def _canopy_stress_level(value) -> str:
    if value is None or value != value:
        return "Unknown"
    if value < 0.10:
        return "Possible low chlorophyll / canopy stress"
    if value <= 0.25:
        return "Moderate canopy condition"
    return "Stronger canopy / chlorophyll signal"


def aggregate_timeseries() -> bool:
    """
    Read the image-level Sentinel-2 index CSV, collapse duplicate dates into
    one row per day, add interpretation columns, and write the daily CSV.

    Returns True on success, False if the input file is missing, malformed,
    or the output folder can't be created — always with a clear, friendly
    explanation printed first.
    """

    import pandas as pd

    if not INPUT_CSV_PATH.exists():
        print()
        print(f"Input file not found: {INPUT_CSV_PATH}")
        print("Run build_sentinel2_index_timeseries.py first to create it.")
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
        print("Re-run build_sentinel2_index_timeseries.py to regenerate the file.")
        return False

    input_rows = len(df)
    unique_dates = df["date"].nunique()
    duplicate_date_count = input_rows - unique_dates

    log.info("Read %d image-level rows covering %d unique dates.", input_rows, unique_dates)
    log.info("Dates with more than one scene (combined into one row): %d", duplicate_date_count)

    daily = (
        df.groupby("date", as_index=False)
        .agg(
            cloud_percentage=("cloud_percentage", "mean"),
            ndvi_mean=("ndvi_mean", "mean"),
            ndwi_mean=("ndwi_mean", "mean"),
            ndmi_mean=("ndmi_mean", "mean"),
            ndre_mean=("ndre_mean", "mean"),
            scene_count=("image_id", "count"),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            buffer_m=("buffer_m", "first"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    daily["ndvi_level"] = daily["ndvi_mean"].apply(_ndvi_level)
    daily["moisture_level"] = daily["ndmi_mean"].apply(_moisture_level)
    daily["canopy_stress_level"] = daily["ndre_mean"].apply(_canopy_stress_level)

    try:
        OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        log.error("Could not create output folder %s: %s", OUTPUT_CSV_PATH.parent, exc)
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
    print(f"Saved daily CSV to: {OUTPUT_CSV_PATH}")
    print()
    print("This is still a standalone file — not yet shown in the dashboard")
    print("and not yet merged with weather/soil data.")
    return True


def main():
    log.info("Aggregating Sentinel-2 vegetation index time series into daily rows...")
    success = aggregate_timeseries()

    if success:
        log.info("Sentinel-2 daily aggregation completed successfully.")
    else:
        log.info("Sentinel-2 daily aggregation did not complete. See messages above.")


if __name__ == "__main__":
    main()
