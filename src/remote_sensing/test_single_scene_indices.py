"""
Single-scene Sentinel-2 vegetation index test — STANDALONE, small CSV only.

WHAT THIS FILE DOES (and does NOT do):
  - It picks ONE low-cloud Sentinel-2 scene (from the same collection
    check_sentinel2_availability.py already confirmed has coverage) and
    computes the mean of four vegetation/water indices over a small buffer
    around the study location.
  - It writes ONE small CSV row (one scene's worth of summary numbers) to
    data/processed/. It does NOT download or save any raster/image file.
  - It does NOT integrate with main.py or the Streamlit dashboard. It is a
    standalone proof-of-concept: "can we compute real index values for one
    real scene?" — nothing more.

THE FOUR INDICES (Sentinel-2 Surface Reflectance bands):
  NDVI — Normalized Difference Vegetation Index = (NIR - RED) / (NIR + RED)
         Bands: (B8 - B4) / (B8 + B4)
         Meaning: overall vegetation greenness/vigor. Higher = denser,
         healthier-looking canopy.

  NDWI — Normalized Difference Water Index = (GREEN - NIR) / (GREEN + NIR)
         Bands: (B3 - B8) / (B3 + B8)
         Meaning: surface water / very high canopy water content signal.
         Useful for spotting standing water or flooding near the orchard,
         not subtle plant stress.

  NDMI — Normalized Difference Moisture Index = (NIR - SWIR1) / (NIR + SWIR1)
         Bands: (B8 - B11) / (B8 + B11)
         Meaning: vegetation moisture/water stress. Lower NDMI can suggest
         the canopy is under water stress.

  NDRE — Normalized Difference Red Edge = (NIR - RedEdge) / (NIR + RedEdge)
         Bands: (B8 - B5) / (B8 + B5)
         Meaning: similar purpose to NDVI but more sensitive to
         chlorophyll/nitrogen changes in dense canopies — can catch
         early-stage stress that NDVI misses once a canopy is mature and
         "saturated" looking to NDVI.

HOW TO USE THIS FILE
  Run after check_sentinel2_availability.py confirms scenes exist:
      python src/remote_sensing/test_single_scene_indices.py

  Reads the same area-of-interest settings (latitude/longitude/buffer_radius_m)
  and cloud threshold from configs/config.yaml under `remote_sensing`.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.remote_sensing.gee_setup import check_earth_engine_setup
from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger(__name__)

SENTINEL2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"

# Output CSV: small summary only, never raster data.
OUTPUT_CSV_PATH = Path("data/processed/muthukur_sentinel2_single_scene_indices.csv")

# Sentinel-2 bands each index needs, so we can give a clear error if a band
# is missing from a particular scene instead of crashing.
REQUIRED_BANDS = {
    "ndvi": ["B8", "B4"],
    "ndwi": ["B3", "B8"],
    "ndmi": ["B8", "B11"],
    "ndre": ["B8", "B5"],
}


def _normalized_difference_mean(image, band_a: str, band_b: str, aoi, scale: int = 10):
    """
    Compute (band_a - band_b) / (band_a + band_b) for `image`, then reduce
    it to a single mean value over `aoi`. Returns None if the bands aren't
    present on this image (some Sentinel-2 products omit a band, rarely).

    This only ever requests one scalar number from Earth Engine per call —
    no pixel arrays, no raster export.
    """
    import ee

    nd = image.normalizedDifference([band_a, band_b])
    stats = nd.reduceRegion(reducer=ee.Reducer.mean(), geometry=aoi, scale=scale, maxPixels=1e9)
    value = stats.get("nd").getInfo()
    return value


def compute_single_scene_indices() -> bool:
    """
    Select one low-cloud Sentinel-2 scene for the configured area/date range,
    compute mean NDVI/NDWI/NDMI/NDRE over a small buffer, and append one row
    to a small CSV. Returns True on success, False if anything blocks it
    (Earth Engine not ready, no scenes found, etc.) — always with a clear,
    friendly explanation printed first.
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

    try:
        collection = (
            ee.ImageCollection(SENTINEL2_COLLECTION)
            .filterBounds(aoi)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_threshold))
            .sort("CLOUDY_PIXEL_PERCENTAGE")
        )

        scene_count = collection.size().getInfo()
        if scene_count == 0:
            print()
            print("No Sentinel-2 scenes matched the configured area/date range/cloud")
            print("threshold. Run check_sentinel2_availability.py first to confirm")
            print("coverage, or widen the date range / raise cloud_threshold_percent.")
            return False

        log.info("Selecting the lowest-cloud scene out of %d candidates...", scene_count)
        image = collection.first()

        image_id = image.get("system:index").getInfo()
        timestamp_ms = image.get("system:time_start").getInfo()
        cloud_pct = image.get("CLOUDY_PIXEL_PERCENTAGE").getInfo()
        scene_date = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")

        band_names = set(image.bandNames().getInfo())

        log.info("Selected scene: %s (%s), cloud cover %.1f%%", image_id, scene_date, cloud_pct)

        results = {"ndvi_mean": None, "ndwi_mean": None, "ndmi_mean": None, "ndre_mean": None}

        for index_name, (band_a, band_b) in REQUIRED_BANDS.items():
            if band_a not in band_names or band_b not in band_names:
                log.warning(
                    "Skipping %s: required bands %s not both present on this scene.",
                    index_name.upper(),
                    [band_a, band_b],
                )
                continue
            log.info("Computing %s mean over %d m buffer...", index_name.upper(), buffer_m)
            value = _normalized_difference_mean(image, band_a, band_b, aoi)
            results[f"{index_name}_mean"] = value

    except Exception as exc:
        log.error("Failed to compute Sentinel-2 indices: %s", exc)
        print()
        print("Something went wrong talking to Earth Engine while computing indices.")
        print(f"Details: {exc}")
        print()
        print("This is usually a transient network/server issue — try running the")
        print("script again. If it keeps failing, re-run gee_setup.py to confirm")
        print("Earth Engine is still initializing correctly.")
        return False

    row = {
        "date": scene_date,
        "image_id": image_id,
        "cloud_percentage": cloud_pct,
        "ndvi_mean": results["ndvi_mean"],
        "ndwi_mean": results["ndwi_mean"],
        "ndmi_mean": results["ndmi_mean"],
        "ndre_mean": results["ndre_mean"],
        "latitude": lat,
        "longitude": lon,
        "buffer_m": buffer_m,
    }

    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([row])
    df.to_csv(OUTPUT_CSV_PATH, index=False)

    print()
    print("Computed mean vegetation/water indices for one Sentinel-2 scene:")
    print(f"  Date:             {scene_date}")
    print(f"  Image ID:         {image_id}")
    print(f"  Cloud cover:      {cloud_pct:.1f}%")
    print(f"  NDVI (vegetation greenness):       {results['ndvi_mean']}")
    print(f"  NDWI (surface water signal):       {results['ndwi_mean']}")
    print(f"  NDMI (vegetation moisture):        {results['ndmi_mean']}")
    print(f"  NDRE (chlorophyll/stress signal):  {results['ndre_mean']}")
    print()
    print(f"Saved summary CSV to: {OUTPUT_CSV_PATH}")
    print("No raster/image data was downloaded — only these summary numbers.")
    return True


def main():
    log.info("Running single-scene Sentinel-2 index test...")
    success = compute_single_scene_indices()

    if success:
        log.info("Single-scene index test completed successfully.")
    else:
        log.info("Single-scene index test did not complete. See messages above.")


if __name__ == "__main__":
    main()
