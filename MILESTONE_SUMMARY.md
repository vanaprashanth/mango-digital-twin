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

The Streamlit dashboard (`streamlit run app/streamlit_app.py`) has nine
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
7. **Water Balance** — the FAO-56 soil-water balance output (ET0, ETc,
   root-zone depletion, Ks water-stress coefficient, TAW, RAW), with
   trend charts and interpretation notes. Carries an explicit disclaimer
   that this is a simplified rainfed prototype (see below).
8. **What-if Simulator** — sliders to test rainfall/temperature/humidity
   changes and see the simulated risk impact.
9. **Raw Data** — expandable raw/processed tables for every data source.

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
- `data/processed/muthukur_fao56_water_balance.csv` (FAO-56 soil-water balance: ET0, ETc, depletion, Ks, TAW, RAW, one row per date)
- `data/processed/muthukur_mango_phenology_calendar.csv` (one mango growth stage per date)
- `data/processed/muthukur_fao56_phenology_water_balance.csv` (phenology-aware FAO-56 soil-water balance: stage, Kc, ET0, ETc, depletion, Ks, TAW, RAW, water-stress score/level, one row per date)

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

## FAO-56 Soil-Water Balance Milestone (new)

`src/water_balance/fao56_water_balance.py` is a standalone script that adds
the project's first physics-informed water-stress signal, separate from the
existing rule-based irrigation risk score.

- **Input:** `data/processed/muthukur_combined_feature_table.csv` (the
  weather + soil + vegetation feature table).
- **Output:** `data/processed/muthukur_fao56_water_balance.csv` — one row
  per date with ET0 (reference evapotranspiration), ETc (estimated crop
  water use), root-zone depletion, the Ks water-stress coefficient, TAW
  (total available water), RAW (readily available water), and a
  Low/Medium/High water-stress level.
- **Method:** ET0 via the FAO-56 Penman-Monteith equation; TAW/RAW from
  Saxton-Rawls field-capacity and wilting-point estimates derived from
  SoilGrids texture; a daily root-zone depletion balance driven by rainfall
  and ETc.
- **Dashboard:** the new **Water Balance** page shows the latest reading,
  trend charts (ET0+ETc, rainfall+ETc, depletion with RAW/TAW reference
  lines, Ks), a water-stress-level count chart, interpretation notes for
  every term, and the raw table.
- **Key assumptions:** the crop coefficient (Kc) is held constant at 0.75
  for the whole season — it is not yet phenology-aware; the depletion
  balance is rainfed-only, with no modeled irrigation events; rainfall
  above field capacity is treated as lost from the root zone, with no
  separate runoff or deep-percolation accounting.
- **What remains incomplete:** phenology-aware Kc by growth stage,
  irrigation-event modeling, runoff/deep-percolation tracking, and any
  field/yield validation. The script is also not yet wired into `main.py`
  — it is standalone, read directly by the dashboard only.

This milestone is explicitly a **simplified rainfed prototype**, and the
Water Balance dashboard page carries that disclaimer directly.

---

## Phenology-Aware FAO-56 Crop Coefficient Milestone (new)

`src/water_balance/fao56_phenology_water_balance.py` is a second, separate
standalone script that replaces the constant Kc = 0.75 above with a
growth-stage-specific Kc, using a new mango phenology calendar
(`src/phenology/mango_phenology_calendar.py`) as its growth-stage source.
The original constant-Kc FAO-56 script and CSV are untouched.

- **Inputs:**
  - `data/processed/muthukur_combined_feature_table.csv` (weather + soil +
    vegetation feature table)
  - `data/processed/muthukur_mango_phenology_calendar.csv` (a simplified,
    regional Andhra Pradesh / South India growth-stage calendar — one mango
    stage per date, not cultivar-specific)
- **Output:** `data/processed/muthukur_fao56_phenology_water_balance.csv` —
  one row per date with `mango_stage`, `kc`, `et0_mm_day`, `etc_mm_day`,
  `rainfall_mm`, `root_zone_depletion_mm`, `taw_mm`, `raw_mm`, `ks`,
  `water_stress_score`, `water_stress_level`, plus vegetation/soil context
  columns where available.
- **Method:** joins the two input tables by date, looks up Kc by
  `mango_stage`, then reuses the same ET0 (FAO-56 Penman-Monteith) and
  TAW/RAW/depletion logic as the original constant-Kc script — so the two
  scripts can never disagree on the underlying water-balance math, only on
  Kc.
- **Kc stage assumptions (first version):**

  | Growth stage | Kc |
  |---|---|
  | Flower induction / pre-flowering | 0.65 |
  | Flowering | 0.75 |
  | Fruit set | 0.85 |
  | Fruit development | 0.90 |
  | Maturity / harvest | 0.80 |
  | Rest / vegetative phase | 0.60 |

- **Limitations:**
  - Kc values are assumed, based on general mango/FAO-56 guidance — not
    locally calibrated for this orchard.
  - No cultivar-specific calibration yet.
  - No irrigation events yet (still rainfed-only depletion, same as the
    constant-Kc script).
  - No field validation yet.
  - Not yet integrated into the dashboard or `main.py` — this script is
    standalone only and currently has no dashboard page of its own.

---

## What Has Not Been Done Yet

- No dashboard page for the phenology-aware FAO-56 output yet (the
  constant-Kc version has a Water Balance page; the phenology-aware version
  does not yet).
- No local/cultivar-specific calibration of the phenology-aware Kc values —
  they are first-pass assumptions from general guidance.
- No irrigation-event modeling in either water balance (rainfed-only
  depletion).
- No runoff or deep-percolation tracking in the water balance.
- No phenology-aware heat/disease/forecast risk logic yet (only Kc is
  stage-aware so far).
- No machine-learning model yet.
- No cloud deployment yet.
- No IndiaAI/GPU usage yet.
- No raster export/download workflow yet (only scalar index values are
  computed; no satellite images are saved).
- No field/yield validation yet (risk scores and both FAO-56 outputs have
  not been checked against real orchard outcomes).
- The combined feature table and both FAO-56 water balance scripts are not
  yet wired into `main.py` — all are still standalone scripts.

## Recommended Next Steps

1. **Documentation checkpoint** — this milestone summary, plus the updated
   `README.md`, `ROADMAP.md`, and `DEVELOPMENT.md`, freeze a clear record of
   the phenology-aware FAO-56 standalone milestone before dashboard
   visualization work begins.
2. **Optional Git commit** — commit this stable state as a checkpoint that
   can be returned to if later changes need to be rolled back.
3. **Add a dashboard page for the phenology-aware FAO-56 output** —
   mirroring the existing Water Balance page, once ready.
4. **Add the combined table and both FAO-56 scripts to the main pipeline
   only after reviewing their stability** — once confident in their
   behavior over more data, consider wiring them into `main.py` so they run
   automatically.
5. **Calibrate the phenology-aware Kc values** against local or
   cultivar-specific data as it becomes available.
6. **Add irrigation-event, runoff, and deep-percolation tracking** to the
   water balance, moving it past a rainfed-only prototype.
7. **Later, prepare cloud deployment** — once the local system and
   phenology work are stable, move storage, scheduling, and the dashboard
   to the cloud (GCP, as planned in `ROADMAP.md`).
8. **Later, explore IndiaAI only if GPU-heavy work is needed** — for example,
   if a future ML or deep-learning model genuinely requires GPU compute at
   scale.

---

This project is a research and prototype system. The risk scores and
vegetation interpretations are not final agronomic recommendations. Field
validation, expert calibration, and local farmer observations are still
required before any operational use.
