"""
Google Earth Engine (GEE) setup and authentication check.

WHAT THIS FILE DOES (and does NOT do):
  - It ONLY tries to initialize the Earth Engine Python API and tells you
    whether that worked, whether you need to authenticate, or whether the
    `earthengine-api` package isn't installed at all.
  - It does NOT download any Sentinel-2 imagery.
  - It does NOT compute NDVI/NDWI/NDMI/NDRE.
  - It does NOT make any other network calls beyond the one Earth Engine
    initialization check.

This is intentional: this project phase is "prepare for Earth Engine", not
"start using Earth Engine for analysis." That comes later (see ROADMAP.md
and DEVELOPMENT.md).

HOW TO USE THIS FILE
  1. Install the Earth Engine Python API (see DEVELOPMENT.md for full
     instructions):
         pip install earthengine-api
  2. Authenticate once (opens a browser window, one-time per machine):
         earthengine authenticate
  3. Run this script to confirm everything is wired up:
         python src/remote_sensing/gee_setup.py

You should run this script any time you're not sure whether Earth Engine
is ready to use — it is completely safe to re-run.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger(__name__)


def check_earth_engine_setup() -> bool:
    """
    Try to import and initialize the Earth Engine Python API.

    Returns True if Earth Engine is installed, authenticated, and ready to
    use. Returns False otherwise, after printing a clear, beginner-friendly
    explanation of what's missing and what command will fix it.

    This function deliberately does not fetch any imagery — ee.Initialize()
    only opens a session with Earth Engine's servers, it does not request
    or download data.
    """

    try:
        import ee
    except ImportError:
        log.error("Earth Engine Python API is not installed.")
        print()
        print("The 'earthengine-api' package is not installed in this environment.")
        print("Install it with:")
        print()
        print("    pip install earthengine-api")
        print()
        print("Then run this script again.")
        return False

    # As of mid-2024+, Earth Engine requires every initialization to be
    # tied to a Google Cloud project (the one you picked/created during
    # `earthengine authenticate`). We read it from configs/config.yaml
    # instead of hardcoding it so it stays out of source-controlled code.
    config = get_config()
    project_id = config.remote_sensing.get("gee_project_id")

    if not project_id:
        print()
        print("No 'gee_project_id' set in configs/config.yaml under remote_sensing.")
        print("Add the Google Cloud project ID you saw during `earthengine authenticate`")
        print("(also visible at https://console.cloud.google.com/ in the project dropdown), e.g.:")
        print()
        print('    remote_sensing:')
        print('      gee_project_id: "your-project-id"')
        return False

    try:
        ee.Initialize(project=project_id)
    except Exception as exc:
        # The most common case here is "not authenticated yet" — Earth
        # Engine raises an error when no valid credentials are found, or
        # when the configured project ID doesn't match an authenticated
        # account / doesn't have the Earth Engine API enabled.
        log.warning("Earth Engine could not initialize: %s", exc)
        print()
        print("Earth Engine is installed, but could not initialize.")
        print("This usually means one of two things:")
        print("  1. You have not authenticated yet on this machine, or")
        print(f"  2. The project '{project_id}' isn't set up for Earth Engine access.")
        print()
        print("Authenticate with (run once, opens a browser window):")
        print()
        print("    earthengine authenticate")
        print()
        print("Then run this script again to confirm.")
        return False

    log.info("Earth Engine initialized successfully.")
    print()
    print("Success: Earth Engine is installed, authenticated, and initialized.")
    print("You're ready for the next phase (Sentinel-2 imagery + index calculations).")
    return True


def print_area_of_interest_config() -> None:
    """
    Print the study-area / Sentinel-2 settings currently in configs/config.yaml,
    so it's easy to confirm they look right before any real fetching begins.
    """

    config = get_config()
    rs = config.remote_sensing

    if not rs:
        print()
        print("No 'remote_sensing' section found in configs/config.yaml yet.")
        return

    print()
    print("Current remote_sensing config (from configs/config.yaml):")
    print(f"  Latitude:            {rs.get('latitude')}")
    print(f"  Longitude:           {rs.get('longitude')}")
    print(f"  Buffer radius (m):   {rs.get('buffer_radius_m')}")
    print(f"  Start date:          {config.remote_sensing_start_date()}")
    print(f"  End date:            {config.remote_sensing_end_date()}")
    print(f"  Cloud threshold (%): {rs.get('cloud_threshold_percent')}")


def main():
    log.info("Checking Earth Engine setup...")
    is_ready = check_earth_engine_setup()
    print_area_of_interest_config()

    if is_ready:
        log.info("Earth Engine setup check passed.")
    else:
        log.info("Earth Engine setup check did not pass yet. See instructions above.")


if __name__ == "__main__":
    main()
