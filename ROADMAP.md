# 🥭 Sensor-Free Mango Digital Twin — Technical Roadmap

This roadmap defines the development order for the project, from the current
stable MVP through to advanced modeling and compute scaling. Phases are
sequential by design: each phase assumes the previous one is stable before
starting. The explicit rule for this project is **do not skip ahead** —
no GPU work, no deep learning, no IndiaAI compute, and no advanced modeling
until the local prototype and cloud basics are clean and explainable.

---

## Current Status (MVP, local PC)

Working and verified on the local Windows/VS Code setup:

1. NASA POWER historical weather pipeline
2. Open-Meteo recent and forecast weather API pipeline
3. SoilGrids soil intelligence pipeline
4. Historical risk engine
5. Forecast risk engine
6. Soil-adjusted irrigation risk
7. Streamlit dashboard
8. Forecast risk section (Open-Meteo API forecast + risk rules)
9. NASA POWER `-999` missing-value cleaning
10. README and project structure cleanup
11. `main.py` pipeline runner with `--skip-fetch`

**Important clarification, preserved throughout this roadmap:** the "future
prediction" shown today is *not* a trained ML model. It is:

```text
Open-Meteo forecast API → forecast weather values → mango risk rules → future irrigation / heat / disease risk
```

Actual model-based forecasting (time series, probabilistic, ML) is deferred
to Phase 6, only after validation data exists.

---

## Phase 1 — Local PC Development (current phase)

Hardware: Dell laptop, Intel i7, 16 GB RAM, Intel Iris Xe, 1 TB SSD.
No GPU-heavy work in this phase — this machine is for engineering, dashboards,
pipelines, and small-scale experiments only.

Scope:

1. Clean and organize the codebase
2. Improve the Streamlit dashboard
3. Add sidebar navigation
4. Add a study-area map
5. Add better forecast charts and tables
6. Keep configuration-driven paths, dates, and coordinates (already done via `configs/config.yaml`)
7. Add logging and error handling
8. Add small sample datasets (for tests / offline dev)
9. Add unit tests
10. Add local CSV/parquet feature tables
11. Add basic statistical models, only if lightweight (no deep learning)
12. Prepare the GitHub repo properly (`.gitignore`, license, contribution notes)

**Immediate next work, in order:**

1. Dashboard redesign — done
2. Sidebar navigation — done
3. Study-area map — done
4. Improve forecast dashboard visibility (date range, soil-adjusted metric, forecast table — done)
5. Data source / status badges — done
6. Move raw data into expandable sections — done
7. Sentinel-2 / Google Earth Engine — done ahead of schedule, see Phase 3 below (still local-only, not cloud-deployed)
8. FAO-56 water balance — done ahead of schedule, see Phase 4 below (standalone, simplified rainfed prototype)
9. Phenology-aware crop coefficients and growth-stage logic — done, including dashboard visualization, see Phase 5 below
10. Prepare cloud migration once the local dashboard and pipelines are clean

---

## Phase 2 — Normal Cloud Migration (GCP)

Start simple. GCP is the chosen first cloud because it fits well with Earth
Engine, Cloud Storage, Cloud Run, BigQuery, and scheduled jobs.

Goals:

1. Store raw and processed data in Cloud Storage
2. Schedule daily fetches for NASA POWER, Open-Meteo, and later Sentinel-2 (Cloud Scheduler + Cloud Functions/Run)
3. Run the risk pipeline automatically
4. Deploy the Streamlit dashboard (Cloud Run)
5. Add database support (PostgreSQL / PostGIS) if/when spatial queries justify it
6. Add Google Earth Engine integration for Sentinel-2 vegetation data
7. Create a reproducible cloud pipeline (infra-as-code where practical)
8. Keep costs low at the start — free tier / minimal always-on resources

---

## Phase 3 — Remote Sensing and Vegetation Intelligence — COMPLETED (local PC, standalone)

Done so far, ahead of the original cloud-first sequencing — all of this ran
locally against Google Earth Engine, with no cloud deployment and no raster
downloads:

1. [DONE] Google Earth Engine setup and authentication check (`gee_setup.py`)
2. [DONE] Sentinel-2 metadata availability check (`check_sentinel2_availability.py`)
3. [DONE] Single-scene NDVI/NDWI/NDMI/NDRE index test (`test_single_scene_indices.py`)
4. [DONE] Multi-date Sentinel-2 index time series, one row per scene (`build_sentinel2_index_timeseries.py`)
5. [DONE] Daily Sentinel-2 aggregation with greenness/moisture/canopy-stress labels (`aggregate_sentinel2_timeseries.py`)
6. [DONE] Vegetation Health dashboard page (NDVI/NDWI/NDMI/NDRE trends, interpretation, raw tables)
7. [DONE] Combined weather + soil + vegetation feature table (`build_feature_table.py`), using nearest-previous (never future) Sentinel-2 matching plus a freshness flag
8. [DONE] Combined Intelligence dashboard page — weather risk, soil intelligence, and vegetation health interpreted together

Not yet done from the original Phase 3 scope:

- Cloud masking (current scenes are filtered by a cloud-cover threshold, not pixel-level masking)
- Monthly/weekly aggregation (only daily aggregation exists so far)
- Multi-farm/multi-location vegetation time series (single study area only)

Goal achieved: the dashboard now shows weather risk, soil intelligence, and
vegetation health together on the Combined Intelligence page. Still standalone
in one respect: the combined feature table itself is not yet wired into
`main.py` — only the dashboard reads it directly.

---

## Phase 4 — Scientific Water-Stress Modeling — COMPLETED (local PC, standalone prototype)

Done so far, ahead of the original cloud-first sequencing — fully local,
no cloud deployment, no raster downloads:

1. [DONE] FAO-56 Penman-Monteith style soil-water balance (`src/water_balance/fao56_water_balance.py`)
2. [DONE] ET0 calculated via the FAO-56 Penman-Monteith equation from weather variables
3. [DONE] Rainfall input from the combined feature table
4. [DONE] Soil water-holding capacity (TAW/RAW) from Saxton-Rawls field-capacity/wilting-point estimates using SoilGrids texture
5. [DONE] Constant crop coefficient assumption for mango (Kc = 0.75 — not yet phenology-aware)
6. [DONE] Root-zone depletion balance and Ks water-stress coefficient (functions as the daily water-stress score)
7. [DONE] Water Balance dashboard page showing ET0, ETc, depletion, Ks, TAW, RAW, trends, and interpretation

Not yet done from the original Phase 4 scope, carried forward explicitly as
known limitations of this prototype:

- Crop coefficient is a constant (0.75), not phenology-aware by growth stage
- Depletion balance is rainfed-only — no actual irrigation events are modeled
- No runoff or deep-percolation tracking (all rainfall above field capacity is currently treated as lost from the root zone, with no separate runoff/percolation accounting)
- No field/yield validation against real orchard outcomes yet
- Not wired into `main.py` — still a standalone script, read directly by the dashboard only

Goal achieved (in simplified prototype form): the FAO-56 model and Water
Balance page give the first physics-informed water-stress signal in the
project, replacing nothing yet — the original simple irrigation rules still
run unchanged, and the FAO-56 output is a separate, parallel view pending
the limitations above being addressed.

---

## Phase 5 — Phenology-Aware Mango Digital Twin (in progress, standalone steps completed)

Replace the FAO-56 prototype's constant crop coefficient (Kc = 0.75) with
growth-stage-specific Kc values, and add mango growth-stage logic generally:

1. Dormancy / rest period
2. Flowering
3. Fruit set
4. Fruit development
5. Maturity / harvest period

Risk should change by stage:

1. Heat risk during flowering may be more serious
2. Rainfall/humidity during flowering or fruiting may increase disease risk
3. Water stress during fruit development may affect yield
4. Forecast alerts depend on the current mango stage

Completed so far, fully local, standalone (no cloud, no GPU, no raster
downloads):

1. [DONE] Mango phenology calendar (`src/phenology/mango_phenology_calendar.py`)
   — a simplified, regional (Andhra Pradesh / South India) growth-stage
   calendar, not cultivar-specific and not field-validated. Output:
   `data/processed/muthukur_mango_phenology_calendar.csv`. Also has its own
   Mango Phenology dashboard page.
2. [DONE] Phenology-aware Kc standalone FAO-56 script
   (`src/water_balance/fao56_phenology_water_balance.py`) — joins the
   combined feature table with the phenology calendar by date and assigns
   Kc per growth stage (see table below) instead of the constant Kc = 0.75,
   reusing the same ET0/TAW/RAW/depletion logic as the original FAO-56
   script. Output: `data/processed/muthukur_fao56_phenology_water_balance.csv`.
   The original constant-Kc FAO-56 script and CSV are untouched.
3. [DONE] Phenology-aware FAO-56 dashboard page (**Phenology Water
   Balance**) — visualizes the stage-aware Kc, ET0, ETc, root-zone
   depletion, Ks, and water-stress level over time, with stage-wise
   breakdowns and a labeled prototype comparison against the constant-Kc
   Water Balance page where that output exists.

Kc values used (first-pass assumptions, not field-calibrated):

| Growth stage | Kc |
|---|---|
| Flower induction / pre-flowering | 0.65 |
| Flowering | 0.75 |
| Fruit set | 0.85 |
| Fruit development | 0.90 |
| Maturity / harvest | 0.80 |
| Rest / vegetative phase | 0.60 |

Not yet done from Phase 5 scope (kept as future work, not started):

- Wiring either phenology script into `main.py`
- Local/cultivar-specific Kc calibration (current values are generic
  FAO-56/mango guidance, not measured at this orchard)
- Irrigation-event modeling (still rainfed-only depletion)
- Field/yield validation
- Phenology-aware heat/disease/forecast risk logic beyond Kc (items 1-4
  in the "Risk should change by stage" list above)

---

## Phase 6 — Advanced Modeling

Only after the basic system is stable.

Possible modules:

1. Monte Carlo uncertainty simulation
2. Confidence scores for risk output
3. Ensemble Kalman Filter data assimilation
4. Bayesian calibration
5. ML-based yield or risk forecasting, if validation data becomes available
6. Graph-based spatial modeling, if multiple orchards/regions are added
7. Reinforcement-learning advisory policy — future research idea only

---

## Phase 7 — IndiaAI Compute / AIKosh Exploration (later-stage option)

Not the immediate next step. Use only when:

1. The project grows beyond local/cloud CPU workloads
2. GPU is genuinely needed (ML, deep learning, foundation-model fine-tuning, or large-scale geospatial processing)
3. Ready to apply as a startup/research project
4. There is a clear compute requirement and project proposal

Before using IndiaAI, verify:

1. Current eligibility rules
2. Current GPU pricing and subsidy rules
3. Whether individual researchers/students can apply
4. Whether this project fits agriculture AI / climate risk / digital twin use cases
5. What documentation or proposal is needed
6. Whether AIKosh has useful agriculture, weather, soil, crop, yield, or district-level datasets

Possible proposal framing:

> "A sensor-free, phenology-aware mango digital twin for orchard risk
> forecasting using public weather, soil, and satellite data to support
> irrigation stress, heat stress, and disease-risk intelligence for Indian
> farmers."

---

## Sequencing Rule

PC (engineering, dash