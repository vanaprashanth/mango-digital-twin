"""
Multi-date Sentinel-2 vegetation index time series — STANDALONE, CSV only.

WHAT THIS FILE DOES (and does NOT do):
  - It computes mean NDVI/NDWI/NDMI/NDRE over the study-area buffer for
    EVERY usable Sentinel-2 scene in the configured date range (the same
    scenes check_sentinel2_availability.py already confirmed exist), and
    writes one CSV row per scene.
  - It does NOT download or save any raster/image file — only the four
    mean scalar values per scene, plus its date/id/cloud cover.
  - It does NOT integrate with main.py or the Streamlit dashboard, and does
    NOT aggregate by date/month. Each row is one Sentinel-2 image. Sentinel-2
    can return more than one image for the same calendar date when adjacent
    tiles/orbits both cover the study area — those are kept as separate rows
    on purpose (see module docs in DEVELOPMENT.md). Aggregation is a planned
    later step, not done here.

THE FOUR INDICES (see test_single_scene_indices.py for the full explanation):
  NDVI = (B8 - B4) / (B8 + B4)   — vegetation greenness
  NDWI = (B3 - B8) / (B3 + B8)   — surface water / canopy water signal
  NDMI = (B8 - B11) / (B8 + B11) — vegetation moisture
  NDRE = (B8 - B5) / (B8 + B5)   — chlorophyll / canopy stress signal

HOW THIS WORKS, EFFICIENTLY
  Instead of calling Earth Engine once per scene per index (slow, ~100+
  scenes x 4 indices = 400+ round trips), this script:
    1. Maps an "add index bands" function over the whole collection
       server-side (Earth Engine computes all four indices for every scene
       in one batched operation).
    2. Maps a "reduce to mean + attach metadata" function over the result,
       still server-side.
    3. Makes exactly ONE getInfo() call to pull all the resulting rows back
       to this script at once.

HOW TO USE THIS FILE
  Run after check_sentinel2_availability.py confirms scenes exist:
      python src/remote_sensing/build_sentinel2_index_timeseries.py

  Reads the same area-of-interest settings (latitude/longitude/buffer_radius_m),
  date range, and cloud threshold from configs/config.yaml under
  `remote_sensing` that the other remote_sensing scripts already use.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.remote_sensing.gee_setup import check_earth_engine_setup
from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger(__name__)

SENTINEL2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"

OUTPUT_CSV_PATH = Path("data/processed/muthukur_sentinel2_index_timeseries.csv")

# Bands each index needs, used to build the index bands server-side.
INDEX_BAND_PAIRS = {
    "ndvi": ("B8", "B4"),
    "ndwi": ("B3", "B8"),
    "ndmi": ("B8", "B11"),
    "ndre": ("B8", "B5"),
}

REQUIRED_ROW_FIELDS = ["date", "image_id", "cloud_percentage"]


def build_index_timeseries() -> bool:
    """
    Query every usable Sentinel-2 scene for the configured area/date range,
    compute mean NDVI/NDWI/NDMI/NDRE per scene, and write one CSV row per
    scene (no date/month aggregation). Returns True on success, False if
    Earth Engine isn't ready or no scenes are found.
    """

    if not check_earth_engine_setup():
        print()
        print("Earth Engine isn't ready yet — fix the issue above, then run")
        print("this script again.")
        return False

    import ee
    import pandas as pd

    config = get_config()
    rs = config.remote_sensing

    lat = rs.get("latitude")
    lon = rs.get("longitude")
    buffer_m = rs.get("buffer_radius_m", 0) or 0
    start_date = config.remote_sensing_start_date()
    end_date = config.remote_sensing_end_date()
    cloud_threshold = rs.get("cloud_threshold_percent", 100)

    aoi = ee.Geometry.Point([lon, lat])
    if buffer_m:
        aoi = aoi.buffer(buffer_m)

    def add_index_bands(image):
        bands = [
            image.normalizedDifference(list(pair)).rename(name)
            for name, pair in INDEX_BAND_PAIRS.items()
        ]
        return image.addBands(bands)

    def reduce_to_feature(image):
        stats = image.select(list(INDEX_BAND_PAIRS.keys())).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi, scale=10, maxPixels=1e9
        )
        metadata = ee.Dictionary(
            {
                "date": image.date().format("YYYY-MM-dd"),
                "image_id": image.get("system:index"),
                "cloud_percentage": image.get("CLOUDY_PIXEL_PERCENTAGE"),
            }
        )
        return ee.Feature(None, stats.combine(metadata))

    try:
        collection = (
            ee.ImageCollection(SENTINEL2_COLLECTION)
            .filterBounds(aoi)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))
            .sort("system:time_start")
        )

        scene_count = collection.size().getInfo()
        log.info("Found %d usable Sentinel-2 scenes for the configured area/date range.", scene_count)

        if scene_count == 0:
            print()
            print("No Sentinel-2 scenes matched the configured area/date range/cloud")
            print("threshold. Run check_sentinel2_availability.py first to confirm")
            print("coverage, or widen the date range / raise cloud_threshold_percent.")
            return False

        log.info("Computing NDVI/NDWI/NDMI/NDRE means for all %d scenes (one batched request)...", scene_count)
        feature_collection = collection.map(add_index_bands).map(reduce_to_feature)
        result = feature_collection.getInfo()

    except Exception as exc:
        log.error("Failed to build Sentinel-2 index time series: %s", exc)
        print()
        print("Something went wrong talking to Earth Engine while building the")
        print("time series.")
        print(f"Details: {exc}")
        print()
        print("This is usually a transient network/server issue, or the date range")
        print("is large enough that the request timed out — try again, or narrow")
        print("the date range in configs/config.yaml and retry.")
        return False

    features = result.get("features", [])
    rows = []
    skipped = 0

    for feature in features:
        props = feature.get("properties", {})

        if any(props.get(field) is None for field in REQUIRED_ROW_FIELDS):
            log.warning("Skipping a scene with missing date/id/cloud metadata: %s", props)
            skipped += 1
            continue

        rows.append(
            {
                "date": props.get("date"),
                "image_id": props.get("image_id"),
                "cloud_percentage": props.get("cloud_percentage"),
                "ndvi_mean": props.get("ndvi"),
                "ndwi_mean": props.get("ndwi"),
                "ndmi_mean": props.get("ndmi"),
                "ndre_mean": props.get("ndre"),
                "latitude": lat,
                "longitude": lon,
                "buffer_m": buffer_m,
            }
        )

    if not rows:
        print()
        print("Earth Engine returned scenes, but none had usable index values.")
        print("Try widening the date range or checking your area-of-interest settings.")
        return False

    try:
        OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        log.error("Could not create output folder %s: %s", OUTPUT_CSV_PATH.parent, exc)
        print()
        print(f"Could not create the output folder: {OUTPUT_CSV_PATH.parent}")
        print(f"Details: {exc}")
        return False

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    df.to_csv(OUTPUT_CSV_PATH, index=False)

    log.info("Processed %d scenes, skipped %d, wrote %d rows.", len(features), skipped, len(rows))
    log.info("Saved time series CSV to: %s", OUTPUT_CSV_PATH)

    print()
    print(f"Scenes found:     {scene_count}")
    print(f"Scenes processed: {len(rows)}")
    print(f"Scenes skipped:   {skipped}")
    print(f"Saved time series CSV to: {OUTPUT_CSV_PATH}")
    print()
    print("Note: Sentinel-2 may return more than one image for the same calendar")
    print("date (overlapping tiles/orbits) — these are kept as separate rows.")
    print("No raster/image data was downloaded — only these summary numbers.")
    return True


def main():
    log.info("Building Sentinel-2 vegetation index time series...")
    success = build_index_timeseries()

    if success:
        log.info("Sentinel-2 index time series build completed successfully.")
    else:
        log.info("Sentinel-2 index time series build did not complete. See messages above.")


if __name__ == "__main__":
    main()
