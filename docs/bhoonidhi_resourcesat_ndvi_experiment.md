# ISRO Resourcesat-2A Vegetation Analysis

## Project
MangoTwin - Sensor-Free Mango Digital Twin

## Study Location
- Region: Muthukur, Peddapanjani Mandal, Chittoor District, Andhra Pradesh, India
- Latitude: 13.294219
- Longitude: 78.624294

## Data Source
- Platform: ISRO Bhoonidhi
- Satellite: Resourcesat-2A
- Sensor: LISS-3
- Product collection: ResourceSat-2A_LISS3_L2
- Acquisition dates: 2026-10-07 and 2026-10-31
- Spatial resolution: 24 meters

## Methodology
The analysis uses rasterio to read small windows around the
study point from two locally downloaded satellite scenes.

Bands used:
- BAND3: Red
- BAND4: Near Infrared (NIR)

Exploratory raw-band NDVI:

NDVI = (NIR - Red) / (NIR + Red)

Sampling windows:
- 1x1 pixels
- 3x3 pixels
- 5x5 pixels
- 9x9 pixels

Each scene is sampled around the same geographic coordinates.
However, individual raster pixels are not necessarily aligned
between acquisition dates.

## Results

| Window | 2026-10-07 | 2026-10-31 |
|--------|------------|------------|
| 1x1 | 0.1978 | 0.4293 |
| 3x3 | 0.1925 | 0.5466 |
| 5x5 | 0.1922 | 0.5977 |
| 9x9 | 0.1944 | 0.5810 |

All sampled pixels were valid according to raster masks and
the calculations performed.

## Interpretation
The October 31 acquisition produced higher raw-band NDVI
values across all sampling windows.

This difference must not be interpreted as confirmed vegetation
growth or improved crop health.

Possible confounding factors include atmospheric conditions,
clouds, shadows, radiometric scaling, illumination and
differences in pixel alignment.

The selected geographic point is not a field-verified mango
orchard. Actual land cover and crop identity remain unknown.

## Limitations
- No confirmed surface-reflectance calibration
- No cloud or cloud-shadow mask
- No field boundary
- No ground-truth crop labels
- No field validation
- Raw-band NDVI is exploratory, not production-ready
- No confirmed mango or groundnut classification

## Next Research Steps
1. Investigate ResourceSat-2A_LISS3_BOA availability.
2. Verify BOA reflectance units and scaling.
3. Apply cloud and shadow quality screening.
4. Compare radiometrically consistent observations.
5. Investigate field-boundary-based vegetation statistics.
6. Evaluate seasonal crop identification with ground truth.

## Repository Policy
Original satellite imagery, ZIP archives and experimental
outputs are stored locally under data/satellite_experiments/.
This directory is excluded from Git.

The analysis script is maintained at:
src/isro/bhoonidhi/compare_ndvi.py

This experiment does not modify the production MangoTwin
models, Streamlit dashboard or GCS pipeline.
