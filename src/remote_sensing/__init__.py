"""
Remote sensing module (Sentinel-2 / Google Earth Engine).

This package will eventually compute vegetation and water indices from
Sentinel-2 satellite imagery for the study area:

- NDVI (Normalized Difference Vegetation Index) — overall plant health/vigor.
- NDWI (Normalized Difference Water Index) — surface water / canopy water content.
- NDMI (Normalized Difference Moisture Index) — vegetation moisture stress.
- NDRE (Normalized Difference Red Edge) — early-stage stress detection, more
  sensitive than NDVI for crops with dense canopy like mango trees.

As of this commit, this is SETUP ONLY: no satellite data is fetched yet and
no indices are computed yet. See gee_setup.py to test your Earth Engine
authentication, and DEVELOPMENT.md for the full setup guide.
"""
