"""
Sentinel-2 vegetation/water index calculations — PLACEHOLDER.

This file does NOT fetch any satellite imagery yet, and does NOT compute
any real index values yet. It exists only to document, in code, what each
index means and where the real implementation will live once the project
moves past the setup phase.

WHY THESE INDICES MATTER FOR A MANGO ORCHARD (beginner-friendly notes):

  NDVI — Normalized Difference Vegetation Index
      Formula: (NIR - RED) / (NIR + RED)
      What it tells you: how green/leafy/healthy the canopy looks overall.
      Higher NDVI generally means denser, healthier vegetation. Useful as
      a general crop-health indicator, but it can saturate (stop changing
      much) once a canopy is already dense, which is common for mature
      mango trees.

  NDWI — Normalized Difference Water Index
      Formula: (GREEN - NIR) / (GREEN + NIR)
      What it tells you: presence of surface water or very high canopy
      water content. Often used to detect standing water, water bodies,
      or flooding near the orchard, not subtle plant stress.

  NDMI — Normalized Difference Moisture Index
      Formula: (NIR - SWIR1) / (NIR + SWIR1)
      What it tells you: vegetation moisture/water stress. Lower NDMI can
      indicate the canopy is under water stress (useful alongside our
      existing rainfall-based irrigation risk score).

  NDRE — Normalized Difference Red Edge
      Formula: (NIR - RedEdge) / (NIR + RedEdge)
      What it tells you: similar purpose to NDVI but more sensitive to
      chlorophyll/nitrogen changes in dense canopies, so it can pick up
      early-stage stress that NDVI misses once a canopy is already mature
      and "saturated" looking to NDVI.

WHAT HAPPENS NEXT (future phase, not yet built):
  - Define the area of interest as a point + buffer (see configs/config.yaml
    `remote_sensing.latitude` / `longitude` / `buffer_radius_m`).
  - Query the Sentinel-2 Surface Reflectance collection in Earth Engine,
    filtered by date range and cloud cover threshold
    (`remote_sensing.cloud_threshold_percent`).
  - Compute each index per available scene and reduce it to a single value
    (e.g. mean) over the area of interest.
  - Merge those index values into the existing risk tables so that future
    risk scoring can use real vegetation/moisture signals instead of only
    weather and soil data.

None of that is implemented here yet. This file is intentionally just
documentation + stub functions so the project structure is ready when that
work begins.
"""


def calculate_ndvi(nir_band, red_band):
    """
    Placeholder for NDVI = (NIR - RED) / (NIR + RED).

    Not implemented yet — this phase only sets up the project structure
    for Sentinel-2 / Earth Engine integration. See module docstring above.
    """
    raise NotImplementedError(
        "calculate_ndvi() is a placeholder for the upcoming remote-sensing "
        "phase. No Sentinel-2 data is fetched yet."
    )


def calculate_ndwi(green_band, nir_band):
    """
    Placeholder for NDWI = (GREEN - NIR) / (GREEN + NIR).

    Not implemented yet — see module docstring above.
    """
    raise NotImplementedError(
        "calculate_ndwi() is a placeholder for the upcoming remote-sensing "
        "phase. No Sentinel-2 data is fetched yet."
    )


def calculate_ndmi(nir_band, swir1_band):
    """
    Placeholder for NDMI = (NIR - SWIR1) / (NIR + SWIR1).

    Not implemented yet — see module docstring above.
    """
    raise NotImplementedError(
        "calculate_ndmi() is a placeholder for the upcoming remote-sensing "
        "phase. No Sentinel-2 data is fetched yet."
    )


def calculate_ndre(nir_band, red_edge_band):
    """
    Placeholder for NDRE = (NIR - RedEdge) / (NIR + RedEdge).

    Not implemented yet — see module docstring above.
    """
    raise NotImplementedError(
        "calculate_ndre() is a placeholder for the upcoming remote-sensing "
        "phase. No Sentinel-2 data is fetched yet."
    )
