# 🥭 Milestone Summary — Sensor-Free Mango Digital Twin

This is a plain-language snapshot of what has been built so far, written so
anyone (not just a developer) can understand where the project stands before
the next phase of work begins.

---

## Project Name

Sensor-Free Mango Digital Twin

## Study Location

Muthukur / Peddapanjani mango-growing area, Chittoor district, Andhra
Pradesh, India (latitude 13.294219, longitude 78.624294). All location,
date-range, and threshold settings live in `configs/config.yaml`, so the
same codebase could point at a different orchard by editing that one file.

## Current Data Sources

- **NASA POWER** — historical daily weather (temperature, humidity, rainfall,
  solar radiation, wind speed).
- **Open-Meteo** — recent and forecast weather, including FAO ET0
  evapotranspiration.
- **SoilGrids** — static soil properties (sand/silt/clay %, pH, organic
  carbon, bulk density, cation exchange capacity).
- **Sentinel-2 (via Google Earth Engine)** — satellite imagery used to
  compute vegetation/water indices (NDVI, NDWI, NDMI, NDRE). Only small
  scalar/metadata values are downloaded — no raster images are stored
  locally.

## Current Dashboard Pages

The Streamlit dashboard (`streamlit run app/streamlit_app.py`) has eight
pages, navigated from the sidebar:

1. **Overview & Map** — latest digital twin status, study-area map, latest
   weather, latest recommendation.
2. **Historical Risk** — date filter, rainfall/temperature/risk-score
   trends, risk-day summary, monthly risk summary.
3. **Forecast Risk** — forecast date range, forecast risk metrics, forecast
   trends and table, forecast advisory.
4. **Soil Intelligence** — soil properties, soil-adjusted irrigation risk,
   plain-language soil interpretation.
5. **Vegetation Health** — Sentinel-2 NDVI/NDWI/NDMI/NDRE trends, latest
   reading, greenness/moisture/canopy-stress interpretation.
6. **Combined Intelligence** — the first page that shows weather risk, soil
   conditions, and vegetation health together, with filters and
   interpretation rules (see below).
7. **What-if Simulator** — sliders to test rainfall/temperature/humidity
   changes and see the simulated risk impact.
8. **Raw Data** — expandable raw/processed tables for every data source.

## Current Generated Data Files

- `data/raw/muthukur_weather_nasa_power.csv`
- `data/raw/muthukur_weather_open_meteo.csv`
- `data/raw/muthukur_soilgrids.csv`
- `data/processed/muthukur_weather_risk_scores.csv` (historical risk)
- `data/processed/muthukur_open_meteo_forecast_risk.csv` (forecast risk)
- `data/processed/muthukur_sentinel2_single_scene_indices.csv` (one-scene proof of concept)
- `data/processed/muthukur_sentinel2_index_timeseries.csv` (one row per Sentinel-2 scene)
- `data/processed/muthukur_sentinel2_daily_indices.csv` (one row per day, vegetation only)
- `data/processed/muthukur_combined_feature_table.csv` (weather + soil + vegetation, one row per weather date)

## Current Risk Models

Three rule-based risk scores, each 0–1 and bucketed into Low/Medium/High:

- **Irrigation risk** — driven by 7-day rainfall, maximum temperature, solar
  radiation, and a soil water-retention adjustment factor (~0.89 for this
  location, meaning the soil slightly reduces irrigation risk).
- **Heat stress risk** — driven by maximum and average temperature.
- **Disease-friendly weather risk** — driven by humidity, average
  temperature, and recent rainfall.

These are transparent threshold-based rules, not a trained machine-learning
model. The same is true for the "forecast" risk — it applies the same rules
to Open-Meteo's forecast weather values, not a learned prediction model.

## Current Remote-Sensing Capability

- Google Earth Engine is set up and authenticated for this project.
- Sentinel-2 scene availability can be checked for the study area (metadata
  only).
- NDVI, NDWI, NDMI, and NDRE are computed for every usable scene in the
  configured date range, then aggregated into one row per day with
  beginner-friendly greenness/moisture/canopy-stress labels.
- No raster/pixel imagery is ever downloaded or stored — only small scalar
  index values and metadata.

## Current Combined Digital-Twin Capability

`src/features/build_feature_table.py` joins the historical weather/risk
data with the daily vegetation data and the static soil data into one
table. For every weather date, it attaches the **nearest previous**
Sentinel-2 observation (never a future one, so the data never "sees the
future") plus how stale that observation is (`Fresh` / `Moderate` / `Stale`
/ `Missing`). The **Combined Intelligence** dashboard page reads this table
and interprets it with four rules: possible water stress, disease-friendly
conditions, combined stress (low vegetation greenness + high risk), and a
stale-data warning. This is the first view in the project where weather,
soil, and satellite vegetation data are reasoned about together.

---

## What Has Not Been Done Yet

- No FAO-56 water balance model yet.
- No phenology-aware mango growth-stage model yet.
- No machine-learning model yet.
- No cloud deployment yet.
- No IndiaAI/GPU usage yet.
- No raster export/download workflow yet (only scalar index values are
  computed; no satellite images are saved).
- No field/yield validation yet (risk scores have not been checked against
  real orchard outcomes).
- The combined feature table is not yet wired into `main.py` — it is still
  a standalone script, read directly by the dashboard only.

## Recommended Next Steps

1. **Documentation checkpoint** — this milestone summary, plus the updated
   `README.md`, `ROADMAP.md`, and `DEVELOPMENT.md`, freeze a clear record of
   what exists before bigger scientific modeling begins.
2. **Optional Git commit** — commit this stable state as a checkpoint that
   can be returned to if later changes need to be rolled back.
3. **Add the combined table to the main pipeline only after reviewing its
   stability** — once confident in `build_feature_table.py`'s behavior over
   more data, consider wiring it into `main.py` so it runs automatically.
4. **Start FAO-56 water balance as the next scientific model** — replace the
   simple irrigation-risk rules with a physics-informed soil-water balance
   model.
5. **Add phenology-aware mango logic** — let risk interpretation change by
   growth stage (dormancy, flowering, fruit set, fruit development,
   maturity).
6. **Later, prepare cloud deployment** — once the local system and FAO-56/
   phenology work are stable, move storage, scheduling, and the dashboard to
   the cloud (GCP, as planned in `ROADMAP.md`).
7. **Later, explore IndiaAI only if GPU-heavy work is needed** — for example,
   if a future ML or deep-learning model genuinely requires GPU compute at
   scale.

---

This project is a research and prototype system. The risk scores and
vegetation interpretations are not final agronomic recommendations. Field
validation, expert calibration, and local farmer observations are still
required before any operational use.
