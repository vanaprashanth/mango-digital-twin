"""
Multi-date Sentinel-1 SAR backscatter time series — STANDALONE, CSV only.

WHAT THIS FILE DOES (and does NOT do):
  - Computes mean VV and VH radar backscatter (dB) and the VV/VH ratio over
    the study-area buffer for every usable Sentinel-1 GRD IW scene in the
    configured date range, and writes one CSV row per scene.
  - It does NOT download or save any raster/image file — only the three mean
    scalar values per scene, plus its date/id/orbit pass.
  - It does NOT integrate with main.py or the Streamlit dashboard in this
    step, and does NOT aggregate by date. Each row is one Sentinel-1 scene.
    Aggregation is done by aggregate_sentinel1_timeseries.py.

WHY SENTINEL-1 SAR (as a cloudy-season fallback for Sentinel-2):
  Sentinel-2 is an optical sensor — cloud cover blocks its view completely.
  In the south Indian monsoon season (June–September), cloud cover can render
  Sentinel-2 unusable for weeks at a time. Sentinel-1 is a Synthetic Aperture
  Radar (SAR) sensor that penetrates cloud cover and images the ground
  regardless of weather. The two bands collected here are:

    VV  — vertical-transmit / vertical-receive backscatter.
          Sensitive to surface roughness, canopy structure, and soil moisture.
    VH  — vertical-transmit / horizontal-receive backscatter.
          Sensitive to vegetation volume (canopy density, leaf/branch geometry).

  IMPORTANT — these are PROXY signals only. VV/VH backscatter is NOT NDVI,
  NOT a direct soil-moisture reading, and NOT a field-calibrated crop index.
  They are radar proxies that correlate loosely with canopy structure and soil
  moisture under specific conditions. Do not treat them as direct equivalents
  to optical vegetation indices.

SAR COLLECTION DETAILS:
  Collection: COPERNICUS/S1_GRD (Ground Range Detected, log10-scaled dB)
  Mode: IW (Interferometric Wide Swath) — the standard land-surface mode
  Polarizations: VV + VH
  Orbit preference: DESCENDING (the usual daytime pass over south India).
    Both ASCENDING and DESCENDING are kept if only one is available.
  Temporal resolution: ~6–12 days per orbit direction at this latitude.

HOW TO USE THIS FILE
  Run after GEE is set up (earthengine authenticate, or via service account):
      python src/remote_sensing/build_sentinel1_sar_timeseries.py

  Reads area-of-interest settings (latitude/longitude/buffer_radius_m) and
  date range from configs/config.yaml under `remote_sensing`, same as the
  Sentinel-2 scripts.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.remote_sensing.gee_setup import check_earth_engine_setup
from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger(__name__)

SENTINEL1_COLLECTION = "COPERNICUS/S1_GRD"
PREFERRED_ORBIT_PASS = "DESCENDING"

OUTPUT_CSV_PATH = Path("data/processed/muthukur_sentinel1_sar_timeseries.csv")

REQUIRED_ROW_FIELDS = ["date", "image_id", "orbit_pass"]


def build_sar_timeseries(assume_ee_initialized: bool = False) -> bool:
    """
    Query every usable Sentinel-1 GRD IW VV+VH scene for the configured
    area/date range, compute mean VV, VH, and VV/VH ratio per scene, and
    write one CSV row per scene (no date aggregation). Returns True on
    success, False if Earth Engine isn't ready or no scenes are found.

    assume_ee_initialized
        When True, skip the check_earth_engine_setup() call and go straight
        to the Earth Engine API calls. Use this when the caller (e.g.
        run_pipeline.py) has already called try_init_earth_engine() and
        verified that Earth Engine is ready — re-running
        check_earth_engine_setup() would call ee.Initialize() a second time
        with the default credential chain, which fails in CI/service-account
        environments where the first initialization used
        ServiceAccountCredentials. Defaults to False so standalone script
        invocations still go through the interactive setup check.
    """

    if not assume_ee_initialized:
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

    aoi = ee.Geometry.Point([lon, lat])
    if buffer_m:
        aoi = aoi.buffer(buffer_m)

    def reduce_to_feature(image):
        stats = image.select(["VV", "VH"]).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi, scale=10, maxPixels=1e9
        )
        vv = stats.get("VV")
        vh = stats.get("VH")
        # VV/VH ratio in linear scale, computed server-side.
        # SAR values are stored as log10(linear) dB; converting back to
        # linear before dividing, then back to dB for the ratio column.
        # For simplicity we store the dB ratio directly (VV_dB - VH_dB).
        vv_vh_ratio = ee.Number(vv).subtract(ee.Number(vh))

        metadata = ee.Dictionary(
            {
                "date": image.date().format("YYYY-MM-dd"),
                "image_id": image.get("system:index"),
                "orbit_pass": image.get("orbitProperties_pass"),
                "vv_mean": vv,
                "vh_mean": vh,
                "vv_vh_ratio_mean": vv_vh_ratio,
            }
        )
        return ee.Feature(None, metadata)

    try:
        base_collection = (
            ee.ImageCollection(SENTINEL1_COLLECTION)
            .filterBounds(aoi)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
            .sort("system:time_start")
        )

        # Prefer DESCENDING orbit (daytime pass over south India), but fall
        # back to all passes if DESCENDING has no coverage.
        descending_collection = base_collection.filter(
            ee.Filter.eq("orbitProperties_pass", PREFERRED_ORBIT_PASS)
        )
        desc_count = descending_collection.size().getInfo()

        if desc_count > 0:
            collection = descending_collection
            log.info(
                "Using %d DESCENDING-orbit Sentinel-1 scenes.", desc_count
            )
        else:
            scene_count_all = base_collection.size().getInfo()
            log.info(
                "No DESCENDING-orbit scenes found; falling back to all %d "
                "available scenes (ASCENDING + DESCENDING).",
                scene_count_all,
            )
            collection = base_collection

        scene_count = collection.size().getInfo()
        log.info(
            "Found %d usable Sentinel-1 scenes for the configured area/date range.",
            scene_count,
        )

        if scene_count == 0:
            print()
            print("No Sentinel-1 IW VV+VH scenes found for the configured area/date range.")
            print("Check the date range and area-of-interest settings in configs/config.yaml.")
            return False

        log.info(
            "Computing VV/VH backscatter means for all %d scenes "
            "(one batched request)...",
            scene_count,
        )
        feature_collection = collection.map(reduce_to_feature)
        result = feature_collection.getInfo()

    except Exception as exc:
        log.error("Failed to build Sentinel-1 SAR time series: %s", exc)
        print()
        print("Something went wrong talking to Earth Engine while building the")
        print("Sentinel-1 SAR time series.")
        print(f"Details: {exc}")
        print()
        print("This is usually a transient network/server issue. Try again, or")
        print("narrow the date range in configs/config.yaml and retry.")
        return False

    features = result.get("features", [])
    rows = []
    skipped = 0

    for feature in features:
        props = feature.get("properties", {})

        if any(props.get(field) is None for field in REQUIRED_ROW_FIELDS):
            log.warning(
                "Skipping a scene with missing date/id/orbit metadata: %s", props
            )
            skipped += 1
            continue

        rows.append(
            {
                "date": props.get("date"),
                "image_id": props.get("image_id"),
                "orbit_pass": props.get("orbit_pass"),
                "vv_mean": props.get("vv_mean"),
                "vh_mean": props.get("vh_mean"),
                "vv_vh_ratio_mean": props.get("vv_vh_ratio_mean"),
                "latitude": lat,
                "longitude": lon,
                "buffer_m": buffer_m,
            }
        )

    if not rows:
        print()
        print("Earth Engine returned scenes, but none had usable backscatter values.")
        print("Try widening the date range or checking area-of-interest settings.")
        return False

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

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    df.to_csv(OUTPUT_CSV_PATH, index=False)

    log.info(
        "Processed %d scenes, skipped %d, wrote %d rows.",
        len(features), skipped, len(rows),
    )
    log.info("Saved Sentinel-1 SAR time series CSV to: %s", OUTPUT_CSV_PATH)

    print()
    print(f"Scenes found:     {scene_count}")
    print(f"Scenes processed: {len(rows)}")
    print(f"Scenes skipped:   {skipped}")
    print(f"Saved SAR time series CSV to: {OUTPUT_CSV_PATH}")
    print()
    print("Note: VV/VH values are radar backscatter in dB — proxy signals only.")
    print("They are NOT equivalent to optical vegetation indices (NDVI etc.).")
    print("No raster/image data was downloaded — only these summary numbers.")
    return True


def main():
    log.info("Building Sentinel-1 SAR backscatter time series...")
    success = build_sar_timeseries()

    if success:
        log.info("Sentinel-1 SAR time series build completed successfully.")
    else:
        log.info(
            "Sentinel-1 SAR time series build did not complete. See messages above."
        )


if __name__ == "__main__":
    main()
