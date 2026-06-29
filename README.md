# 🥭 Sensor-Free Mango Digital Twin

A Python-based sensor-free digital twin prototype for mango orchard risk intelligence using public weather, forecast, and soil datasets.

This project focuses on the Muthukur / Peddapanjani mango-growing area in Chittoor district, Andhra Pradesh, India. It estimates irrigation risk, heat stress risk, and disease-friendly weather risk without using physical IoT sensors.

---

## 1. Project Goal

The goal of this project is to build a low-cost digital twin framework for mango orchards using publicly available data sources.

Instead of installing field sensors, this system uses:

- NASA POWER for historical daily weather
- Open-Meteo for recent and forecast weather
- SoilGrids for soil texture and soil health indicators
- Python-based risk models
- Streamlit dashboard for visualization and what-if simulation

---

## 2. Current Features

The current MVP includes:

- Historical weather data collection using NASA POWER
- Recent and forecast weather collection using Open-Meteo
- Soil intelligence using SoilGrids
- Mango irrigation-risk scoring
- Heat-stress risk scoring
- Disease-friendly weather-risk scoring
- Soil-adjusted irrigation risk
- Historical risk dashboard
- Forecast risk dashboard
- Risk summary by Low, Medium, and High days
- Monthly risk summary
- What-if simulation for rainfall, temperature, and humidity changes
- Scenario explanation and advisory output
- Sentinel-2 vegetation intelligence (NDVI, NDWI, NDMI, NDRE) via Google Earth Engine, aggregated to one row per day
- A Vegetation Health dashboard page showing satellite-derived greenness/moisture/canopy-stress trends
- A combined weather + soil + vegetation feature table joining historical risk data with the nearest-previous (never future) Sentinel-2 observation and static soil properties
- A Combined Intelligence dashboard page that interprets weather risk, soil conditions, and vegetation health together, with freshness-aware warnings
- A standalone FAO-56 Penman-Monteith soil-water balance prototype (ET0, ETc, root-zone depletion, Ks water-stress coefficient, TAW, RAW)
- A Water Balance dashboard page showing the FAO-56 output, marked as a simplified rainfed prototype
- A mango phenology calendar (regional, generic growth-stage dates) and a phenology-aware FAO-56 standalone script that assigns crop coefficient (Kc) by growth stage instead of a constant value
- A Phenology Water Balance dashboard page showing the phenology-aware FAO-56 output, including a prototype comparison against the constant-Kc Water Balance page

---

## 3. Study Area

All study-area settings, date ranges, file paths, and risk thresholds are centralized in `configs/config.yaml` — nothing is hardcoded in the source files. To point this project at a different orchard, edit that file only.

Current test location (from `configs/config.yaml`):

```yaml
study_area:
  name: "Muthukur / Peddapanjani mango-growing area"
  district: "Chittoor"
  state: "Andhra Pradesh"
  country: "India"
  latitude: 13.294219
  longitude: 78.624294
```

---

## 4. Data Sources

### NASA POWER

Used for historical daily agro-weather data.

Variables used:

- Average temperature
- Maximum temperature
- Minimum temperature
- Relative humidity
- Rainfall
- Solar radiation
- Wind speed

### Open-Meteo

Used for recent and forecast weather data.

Variables used:

- Forecast maximum temperature
- Forecast minimum temperature
- Forecast average temperature
- Rainfall
- Precipitation
- Relative humidity
- Solar radiation
- Wind speed
- FAO ET0 evapotranspiration

### SoilGrids

Used for static soil intelligence.

Variables used:

- Sand percentage
- Silt percentage
- Clay percentage
- Soil pH
- Soil organic carbon
- Bulk density
- Cation exchange capacity

---

## 5. Project Architecture

```text
Public Data Sources
        |
        |-- NASA POWER historical weather
        |-- Open-Meteo forecast weather
        |-- SoilGrids soil properties
        |
        v
Python Data Ingestion
        |
        v
Feature Engineering
        |
        |-- Rolling rainfall
        |-- Temperature stress features
        |-- Humidity/rainfall disease features
        |-- Soil water-retention factor
        |
        v
Risk Engine
        |
        |-- Irrigation risk
        |-- Heat stress risk
        |-- Disease-friendly weather risk
        |
        v
Streamlit Dashboard
        |
        |-- Historical trends
        |-- Forecast intelligence
        |-- Soil intelligence
        |-- What-if simulation
        |-- Advisory recommendations
```

---

## 6. Folder Structure

```text
mango-digital-twin/
│
├── app/
│   └── streamlit_app.py
│
├── data/
│   ├── raw/
│   │   ├── muthukur_weather_nasa_power.csv
│   │   ├── muthukur_weather_open_meteo.csv
│   │   └── muthukur_soilgrids.csv
│   │
│   └── processed/
│       ├── muthukur_weather_risk_scores.csv
│       └── muthukur_open_meteo_forecast_risk.csv
│
├── src/
│   ├── weather/
│   │   ├── fetch_weather.py
│   │   └── fetch_open_meteo.py
│   │
│   ├── risk/
│   │   ├── historical_risk_engine.py
│   │   └── open_meteo_risk_engine.py
│   │
│   ├── soil/
│   │   └── fetch_soilgrids.py
│   │
│   ├── pipeline/
│   │   └── run_pipeline.py
│   │
│   └── utils/
│       └── config.py
│
├── notebooks/
├── configs/
│   └── config.yaml
├── requirements.txt
├── README.md
└── main.py
```

Notes on the structure:

- `src/utils/config.py` loads `configs/config.yaml` once and exposes it through `get_config()`. Every script (fetch, risk engine, dashboard) calls this instead of hardcoding coordinates, dates, file paths, or thresholds.
- `src/risk/historical_risk_engine.py` is the real historical risk engine. The old `src/risk/risk_engine.py` has been removed it had been accidentally overwritten with a duplicate of the dashboard code and was not actually computing risk scores.
- `src/pipeline/run_pipeline.py` (invoked via `main.py`) runs the full ingestion-to-risk pipeline in the correct order, or just the risk-scoring steps with `--skip-fetch`.

---

## 7. Setup Instructions

### Step 1: Create virtual environment

```bash
python -m venv .venv
```

### Step 2: Activate virtual environment

For Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

For Command Prompt:

```bash
.venv\Scripts\activate.bat
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

---

## 8. How to Run the Project

### Option A: Run the unified pipeline (recommended)

```bash
python main.py --skip-fetch
```

As of the pipeline-orchestration milestone, this is the main near-real-time
pipeline command — a single command that brings every downstream output up
to date from whatever raw/cached data is already on disk, with no network
calls. It runs in two layers every time:

1. **Core risk recomputation** — historical risk and forecast risk are
   recomputed from the cached NASA POWER / Open-Meteo / SoilGrids CSVs.
2. **Freshness-aware downstream steps** — Sentinel-2 daily aggregation, the
   combined feature table, the mango phenology calendar, the constant-Kc
   FAO-56 water balance, the phenology-aware FAO-56 water balance, and the
   FAO-56 model comparison are each regenerated or refreshed automatically,
   in that dependency order, using the existing standalone scripts' own
   build functions — no scientific logic is duplicated in the pipeline
   runner.

Each downstream step uses **freshness-aware RUN / SKIP_FRESH logic**: if a
step's output file already exists and is newer than every one of its
required input files, the step prints `SKIP` and a reason instead of
re-running for nothing; if the output is missing or any input is newer than
it, the step prints `RUN` and regenerates it. A step whose required input
doesn't exist yet at all is skipped with a clear warning (`SKIP_MISSING_INPUT`)
rather than failing the whole pipeline run.

If you want a full run including fresh network fetches (NASA POWER,
SoilGrids, Open-Meteo) before the same downstream regeneration, drop the
flag:

```bash
python main.py
```

This runs every fetch/risk step in the correct order — NASA POWER fetch →
SoilGrids fetch → historical risk engine → Open-Meteo fetch → forecast risk
engine — and then the same freshness-aware downstream steps as above.

`main.py` itself is just a thin entry point — both commands above delegate
to `src/pipeline/run_pipeline.py`, which defines the actual step list.

Every run writes `data/processed/pipeline_run_metadata.json`, recording the
run's start/end timestamps, latest available date per key file, row counts,
file modification times, and a per-step `RUN` / `SKIP_FRESH` /
`SKIP_MISSING_INPUT` / `FAILED` result for every freshness-aware step — so
you can see exactly what happened on the last run without re-reading every
CSV yourself.

Then launch the dashboard:

```bash
streamlit run app/streamlit_app.py
```

### Option B: Run each step manually

### 1. Fetch NASA POWER historical weather

```bash
python src/weather/fetch_weather.py
```

Output:

```text
data/raw/muthukur_weather_nasa_power.csv
```

### 2. Fetch SoilGrids soil data

```bash
python src/soil/fetch_soilgrids.py
```

Output:

```text
data/raw/muthukur_soilgrids.csv
```

### 3. Generate historical risk scores

```bash
python src/risk/historical_risk_engine.py
```

Output:

```text
data/processed/muthukur_weather_risk_scores.csv
```

### 4. Fetch Open-Meteo forecast weather

```bash
python src/weather/fetch_open_meteo.py
```

Output:

```text
data/raw/muthukur_weather_open_meteo.csv
```

### 5. Generate Open-Meteo forecast risk scores

```bash
python src/risk/open_meteo_risk_engine.py
```

Output:

```text
data/processed/muthukur_open_meteo_forecast_risk.csv
```

### 6. Run Streamlit dashboard

```bash
streamlit run app/streamlit_app.py
```

All coordinates, date ranges, file paths, and risk thresholds used by these scripts come from `configs/config.yaml`.

---

## 9. Risk Model Logic

### Irrigation Risk

The irrigation-risk score is based on:

- 7-day rainfall
- Maximum temperature
- Solar radiation
- Soil water-retention adjustment factor

The current irrigation model:

```text
soil-adjusted irrigation risk = weather irrigation risk × soil irrigation factor
```

A soil factor below 1.0 reduces irrigation risk.

A soil factor above 1.0 increases irrigation risk.

For the current study location, the soil irrigation factor is approximately:

```text
0.89
```

This means the soil slightly reduces estimated irrigation risk because of better water-retention behavior.

Both the historical and forecast risk tables include `soil_adjusted_irrigation_risk_score` / `soil_adjusted_irrigation_risk_level` columns alongside the weather-only irrigation score, and the dashboard's advisory section uses the soil-adjusted level when soil data is available. The soil factor formula is a transparent placeholder heuristic (clay/sand/organic-carbon based), documented in `src/risk/historical_risk_engine.py`, pending replacement by the physics-informed model planned in Future Work.

### Heat Stress Risk

The heat-stress score is based on:

- Maximum temperature
- Average temperature

Higher temperatures increase mango heat-stress risk.

### Disease-Friendly Weather Risk

The disease-risk score is based on:

- Relative humidity
- Average temperature
- Recent rainfall

High humidity, suitable temperature, and recent rainfall increase disease-friendly weather conditions.

---

## 10. Phenology-Aware FAO-56 Water-Balance Model (Standalone)

In addition to the constant-Kc FAO-56 prototype above, the project has a
second, separate standalone script that makes the crop coefficient (Kc)
growth-stage-aware instead of constant:

- **Mango phenology calendar** — `src/phenology/mango_phenology_calendar.py`
  assigns one growth stage per calendar date using a simplified, regional
  (Andhra Pradesh / South India) seasonal calendar. It is not calibrated to
  a specific cultivar or to field observations at this study site. Output:
  `data/processed/muthukur_mango_phenology_calendar.csv`.
- **Phenology-aware FAO-56 script** —
  `src/water_balance/fao56_phenology_water_balance.py` joins the combined
  feature table with the phenology calendar by date, then looks up a Kc
  value per growth stage instead of using the constant Kc = 0.75. It reuses
  the same ET0 / TAW / RAW / depletion logic as the original FAO-56 script.
  Output: `data/processed/muthukur_fao56_phenology_water_balance.csv`.

Stage-aware Kc values used (first-pass assumptions, not field-calibrated):

| Growth stage | Kc |
|---|---|
| Flower induction / pre-flowering | 0.65 |
| Flowering | 0.75 |
| Fruit set | 0.85 |
| Fruit development | 0.90 |
| Maturity / harvest | 0.80 |
| Rest / vegetative phase | 0.60 |

The original constant-Kc FAO-56 script and its output CSV are untouched —
this is a separate, parallel script and output file, and it still remains
available on its own (run it directly, or via `python main.py --skip-fetch`,
see section 8 above). This script's output is now visible on the
dashboard's **Phenology Water Balance** page (see section 11 below). **Both
FAO-56 models, the combined feature table, the mango phenology calendar,
and the FAO-56 model comparison are now wired into the unified pipeline:**
`python main.py --skip-fetch` (and the full `python main.py` run)
regenerates all of them automatically, in dependency order, via
freshness-aware steps in `src/pipeline/run_pipeline.py` that call each
script's own existing build function directly — no FAO-56 or Kc math is
duplicated in the pipeline runner. The standalone command
(`python src/water_balance/fao56_phenology_water_balance.py`) still works
exactly as before, for targeted debugging. It remains a prototype — Kc
values are assumed, not cultivar-specific, not field-calibrated, and
irrigation events are not yet included. See `ROADMAP.md` and
`MILESTONE_SUMMARY.md` for limitations and next steps.

---

## 11. Dashboard Sections

The Streamlit dashboard uses sidebar navigation with one page per topic, plus a
data source status panel (last-updated badges for each raw/processed file)
in the sidebar:

- **Overview & Map** — latest digital twin status, study-area map, latest weather, latest recommendation
- **Historical Risk** — date filter, rainfall/temperature/risk-score trends, risk summary, monthly risk summary, highest-risk months
- **Forecast Risk** — forecast date range, forecast irrigation/heat/disease risk (weather-only and soil-adjusted), forecast trends, forecast risk table, forecast advisory
- **Soil Intelligence** — soil properties, soil-adjusted irrigation risk, soil interpretation notes, SoilGrids summary table
- **Vegetation Health** — Sentinel-2 NDVI/NDWI/NDMI/NDRE trends, latest reading, greenness/moisture/canopy-stress interpretation, raw daily and image-level tables
- **Combined Intelligence** — combined weather + soil + vegetation view: latest status metrics, date/freshness filters, risk and vegetation trend charts, a dual-axis irrigation-risk-vs-NDVI chart, freshness counts, water-stress/disease/combined-stress/staleness interpretation rules, and the raw combined table
- **Water Balance** — FAO-56 soil-water balance output: latest ET0, ETc, root-zone depletion, Ks water-stress coefficient, TAW, RAW; ET0+ETc, rainfall+ETc, depletion (with RAW/TAW reference lines), and Ks trend charts; a water-stress-level count chart; interpretation notes; and the raw FAO-56 table. Carries an explicit disclaimer that this is a simplified rainfed prototype.
- **Mango Phenology** — current growth stage, stage descriptions and sensitivities, stage counts and timeline, monthly stage distribution.
- **Phenology Water Balance** — the phenology-aware FAO-56 output (`data/processed/muthukur_fao56_phenology_water_balance.csv`): latest date, mango stage, Kc, ET0, ETc, root-zone depletion, Ks, and water-stress level; Kc, ET0/ETc, depletion, and Ks trend charts; water-stress-level counts and stage-wise water-stress/ETc breakdowns; a labeled prototype comparison of ETc and water-stress counts against the constant-Kc Water Balance page where that output exists; interpretation notes on how Kc and water sensitivity change by stage; and the raw table. Carries an explicit disclaimer that this is a simplified, assumption-based, non-field-calibrated prototype with no irrigation events modeled yet.
- **What-if Simulator** — rainfall/temperature/humidity sliders, simulated risk, scenario explanation
- **Raw Data** — expandable raw/processed tables (historical, forecast, SoilGrids, Sentinel-2 daily vegetation)

See `ROADMAP.md` for the full multi-phase development plan (local PC → cloud → remote sensing → scientific modeling → phenology → advanced modeling → IndiaAI compute exploration).

---

## 12. What-if Simulator

The what-if simulator allows the user to test changes in:

- Rainfall percentage
- Temperature change
- Humidity change

Example scenarios:

```text
Rainfall -80%, temperature +3°C, humidity -10%
```

This simulates drought-like stress.

```text
Rainfall +50%, temperature 0°C, humidity +10%
```

This simulates wet and humid disease-friendly conditions.

---

## 13. Current Project Status

Completed:

- VS Code project setup
- NASA POWER data pipeline
- Open-Meteo data pipeline
- SoilGrids data pipeline
- Historical risk engine
- Forecast risk engine
- Soil-adjusted irrigation risk (now actually applied to risk scores, not just displayed)
- Streamlit dashboard with sidebar navigation, study-area map, and data-source status badges
- What-if simulator
- Scenario explanation
- Advisory output
- Centralized configuration (`configs/config.yaml` + `src/utils/config.py`) no hardcoded coordinates, dates, paths, or thresholds
- Single pipeline runner (`main.py` / `src/pipeline/run_pipeline.py`) with a `--skip-fetch` mode for offline risk recomputation
- NASA POWER `-999` missing-value cleaning in the historical risk engine
- Google Earth Engine setup and authentication check (`src/remote_sensing/gee_setup.py`)
- Sentinel-2 scene availability check (metadata only, no downloads)
- Single-scene NDVI/NDWI/NDMI/NDRE proof-of-concept
- Multi-date Sentinel-2 index time series (one row per scene)
- Daily Sentinel-2 aggregation with greenness/moisture/canopy-stress labels
- Vegetation Health dashboard page (first remote-sensing data visible in the dashboard)
- Combined weather + soil + vegetation feature table (`src/features/build_feature_table.py`), using nearest-previous (never future) Sentinel-2 matching and a data-freshness flag
- Combined Intelligence dashboard page the first true digital-twin view interpreting weather risk, soil conditions, and vegetation health together
- Standalone FAO-56 Penman-Monteith soil-water balance script (`src/water_balance/fao56_water_balance.py`), computing ET0, ETc, root-zone depletion, the Ks water-stress coefficient, TAW, and RAW
- Water Balance dashboard page the first physics-informed water-stress view in the project, with a clear disclaimer that it is a simplified rainfed prototype (constant Kc, no irrigation events, no runoff/deep percolation tracking, no field validation yet)
- Mango phenology calendar (`src/phenology/mango_phenology_calendar.py`) a regional, generic growth-stage calendar assigning one mango stage per date
- Phenology-aware FAO-56 standalone script (`src/water_balance/fao56_phenology_water_balance.py`) joins the combined feature table with the phenology calendar and assigns Kc by growth stage instead of a constant value, reusing the same ET0/TAW/RAW/depletion logic as the original FAO-56 script
- Phenology Water Balance dashboard page visualizes the phenology-aware FAO-56 output, with a labeled prototype comparison against the constant-Kc Water Balance page
- A standalone FAO-56 model comparison script (`src/validation/compare_fao56_models.py`) comparing the constant-Kc and phenology-aware FAO-56 outputs day by day
- **Unified, freshness-aware pipeline orchestration** (`src/pipeline/run_pipeline.py`): `python main.py --skip-fetch` is now the single near-real-time command that regenerates or refreshes historical risk, forecast risk, Sentinel-2 daily aggregation, the combined feature table, the mango phenology calendar, both FAO-56 water-balance models, and the FAO-56 model comparison — each step independently checked for missing inputs and skipped (`SKIP_FRESH`) if its output is already newer than every required input, with the per-step result recorded in `pipeline_run_metadata.json`. No scientific/model logic was duplicated — every step calls the relevant script's own existing function.

Note: the standalone scripts for every step above still exist and can be run individually for targeted debugging, but the recommended day-to-day workflow is the single `python main.py --skip-fetch` command. No ML or cloud/GPU work has started.

Next planned (in priority order, see `ROADMAP.md` and `MILESTONE_SUMMARY.md` for full detail): phenology-aware crop coefficients/risk logic beyond Kc, calibration of Kc values against local/cultivar data, and advanced modeling (Monte Carlo, Bayesian calibration, ML-based forecasting) with cloud deployment, a real scheduler, and IndiaAI Compute as later-stage options only if a genuine deployment/GPU/scale need arises.

---

## 14. Future Work

Planned future upgrades:

- Calibrate the phenology-aware Kc stage values against local/cultivar-specific data (current values are first-pass assumptions)
- Add irrigation-event, runoff, and deep-percolation tracking to the water balance (currently rainfed-only depletion)
- Add phenology-aware mango risk modeling (beyond Kc heat/disease/forecast risk by growth stage)
- Add a real scheduler for unattended/recurring runs (the pipeline itself is now unified and freshness-aware, but nothing schedules it yet — every run is still manually triggered)
- Add Ensemble Kalman Filter state estimation
- Add Monte Carlo uncertainty simulation
- Add GCP deployment
- Add PostGIS support for farm boundary and parcel-level analysis
- Add validation against yield, APMC arrivals, or disease records
- Explore IndiaAI Compute only if a genuine GPU/scale need arises

See `MILESTONE_SUMMARY.md` for a beginner-friendly snapshot of what is and isn't built yet.

---

## 15. Research Direction

This project supports the idea of a sensor-free digital twin for mango orchard risk intelligence.

Research framing:


A sensor-free digital twin framework for mango orchards that integrates public weather, forecast, and soil intelligence to estimate irrigation stress, heat stress, and disease-friendly weather risk without field-deployed IoT sensors.


Future research version:


A sensor-free, phenology-aware, Bayesian digital twin for mango orchard risk forecasting using Earth observation, agro-weather fusion, soil intelligence, and physics-informed data assimilation.


---

## 16. Disclaimer

This project is a research and prototype system. The risk scores are not final agronomic recommendations. Field validation, expert calibration, and local farmer observations are required before operational use.
