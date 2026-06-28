"""
Sentinel-2 metadata availability check — METADATA ONLY, no imagery download.

WHAT THIS FILE DOES (and does NOT do):
  - It asks Earth Engine "how many Sentinel-2 scenes exist for my area of
    interest and date range, and what are their dates/cloud cover?"
  - It does NOT download any pixel data (no .getDownloadURL, no export, no
    thumbnail, no array of band values). Only small metadata fields
    (scene count, timestamps, CLOUDY_PIXEL_PERCENTAGE) are requested.
  - It does NOT compute NDVI/NDWI/NDMI/NDRE. See sentinel2_indices.py for
    that future phase.

This is intentional: this step only confirms "is there usable Sentinel-2
imagery for my orchard and dates?" before any real fetching/index work
begins.

HOW TO USE THIS FILE
  Run after `python src/remote_sensing/gee_setup.py` reports success:
      python src/remote_sensing/check_sentinel2_availability.py

  Reads the area of interest (latitude/longitude/buffer_radius_m), date
  range, and cloud-cover threshold from configs/config.yaml under
  `remote_sensing` — the same settings gee_setup.py already prints.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.remote_sensing.gee_setup import check_earth_engine_setup
from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger(__name__)

# Sentinel-2 Surface Reflectance (harmonized), the standard analysis-ready
# collection for vegetation/water indices.
SENTINEL2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"


def check_sentinel2_availability() -> bool:
    """
    Query Earth Engine for the number of Sentinel-2 scenes available for the
    configured area of interest and date range, below the configured cloud
    cover threshold. Prints scene count and a per-scene date/cloud-cover
    table. Returns True if at least one scene is available, False otherwise
    (including if Earth Engine itself isn't ready yet).

    Only metadata is requested from Earth Engine here (collection size,
    timestamps, CLOUDY_PIXEL_PERCENTAGE) — no pixel/band data is fetched.
    """

    if not check_earth_engine_setup():
        print()
        print("Earth Engine isn't ready yet — fix the issue above, then run")
        print("this script again.")
        return False

    import ee

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

    collection = (
        ee.ImageCollection(SENTINEL2_COLLECTION)
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))
    )

    print()
    print(f"Checking Sentinel-2 ({SENTINEL2_COLLECTION}) availability for:")
    print(f"  Location:        ({lat}, {lon}), buffer {buffer_m} m")
    print(f"  Date range:      {start_date} to {end_date}")
    print(f"  Cloud threshold: < {cloud_threshold}% (CLOUDY_PIXEL_PERCENTAGE)")

    scene_count = collection.size().getInfo()

    print()
    print(f"Scenes found: {scene_count}")

    if scene_count == 0:
        print()
        print("No scenes matched. Try widening the date range or raising")
        print("cloud_threshold_percent in configs/config.yaml.")
        return False

    timestamps_ms = collection.aggregate_array("system:time_start").getInfo()
    cloud_pcts = collection.aggregate_array("CLOUDY_PIXEL_PERCENTAGE").getInfo()

    rows = sorted(zip(timestamps_ms, cloud_pcts), key=lambda r: r[0])

    print()
    print(f"{'Date':<12} {'Cloud %':>8}")
    print(f"{'-'*12} {'-'*8}")
    for ts_ms, cloud_pct in rows:
        scene_date = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        print(f"{scene_date:<12} {cloud_pct:>8.1f}")

    print()
    print("This confirms imagery is available — no pixel data was downloaded.")
    print("Next phase (not started yet): fetch one scene and compute indices.")
    return True


def main():
    log.info("Checking Sentinel-2 metadata availability...")
    found = check_sentinel2_availability()

    if found:
        log.info("Sentinel-2 availability check passed (scenes found).")
    else:
        log.info("Sentinel-2 availability check did not find usable scenes yet.")


if __name__ == "__main__":
    main()
