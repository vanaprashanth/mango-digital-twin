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
- `src/risk/historical_risk_engine.py` is the real historical risk engine. The old `src/risk/risk_engine.py` has been removed — it had been accidentally overwritten with a duplicate of the dashboard code and was not actually computing risk scores.
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

### Option A: Run the full pipeline (recommended)

```bash
python main.py
```

This runs every step in the correct order: NASA POWER fetch → SoilGrids fetch → historical risk engine → Open-Meteo fetch → forecast risk engine.

If you only want to recompute risk scores from already-downloaded raw data (no network calls), use:

```bash
python main.py --skip-fetch
```

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

## 10. Dashboard Sections

The Streamlit dashboard uses sidebar navigation with one page per topic, plus a
data source status panel (last-updated badges for each raw/processed file)
in the sidebar:

- **Overview & Map** — latest digital twin status, study-area map, latest weather, latest recommendation
- **Historical Risk** — date filter, rainfall/temperature/risk-score trends, risk summary, monthly risk summary, highest-risk months
- **Forecast Risk** — forecast date range, forecast irrigation/heat/disease risk (weather-only and soil-adjusted), forecast trends, forecast risk table, forecast advisory
- **Soil Intelligence** — soil properties, soil-adjusted irrigation risk, soil interpretation notes, SoilGrids summary table
- **Vegetation Health** — Sentinel-2 NDVI/NDWI/NDMI/NDRE trends, latest reading, greenness/moisture/canopy-stress interpretation, raw daily and image-level tables
- **Combined Intelligence** — combined weather + soil + vegetation view: latest status metrics, date/freshness filters, risk and vegetation trend charts, a dual-axis irrigation-risk-vs-NDVI chart, freshness counts, water-stress/disease/combined-stress/staleness interpretation rules, and the raw combined table
- **What-if Simulator** — rainfall/temperature/humidity sliders, simulated risk, scenario explanation
- **Raw Data** — expandable raw/processed tables (historical, forecast, SoilGrids, Sentinel-2 daily vegetation)

See `ROADMAP.md` for the full multi-phase development plan (local PC → cloud → remote sensing → scientific modeling → phenology → advanced modeling → IndiaAI compute exploration).

---

## 11. What-if Simulator

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

## 12. Current Project Status

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
- Centralized configuration (`configs/config.yaml` + `src/utils/config.py`) — no hardcoded coordinates, dates, paths, or thresholds
- Single pipeline runner (`main.py` / `src/pipeline/run_pipeline.py`) with a `--skip-fetch` mode for offline risk recomputation
- NASA POWER `-999` missing-value cleaning in the historical risk engine
- Google Earth Engine setup and authentication check (`src/remote_sensing/gee_setup.py`)
- Sentinel-2 scene availability check (metadata only, no downloads)
- Single-scene NDVI/NDWI/NDMI/NDRE proof-of-concept
- Multi-date Sentinel-2 index time series (one row per scene)
- Daily Sentinel-2 aggregation with greenness/moisture/canopy-stress labels
- Vegetation Health dashboard page (first remote-sensing data visible in the dashboard)
- Combined weather + soil + vegetation feature table (`src/features/build_feature_table.py`), using nearest-previous (never future) Sentinel-2 matching and a data-freshness flag
- Combined Intelligence dashboard page — the first true digital-twin view interpreting weather risk, soil conditions, and vegetation health together

Note: the combined feature table and Combined Intelligence page are standalone so far — they are not yet wired into `main.py`, and no FAO-56, phenology, ML, or cloud/GPU work has started.

Next planned (in priority order, see `ROADMAP.md` and `MILESTONE_SUMMARY.md` for full detail): review stability of the combined feature table before wiring it into `main.py`, then a FAO-56 soil-water balance model, phenology-aware risk logic, and advanced modeling (Monte Carlo, Bayesian calibration, ML-based forecasting) — with cloud deployment and IndiaAI Compute as later-stage options only if a genuine deployment/GPU/scale need arises.

---

## 13. Future Work

Planned future upgrades:

- Wire the combined weather/soil/vegetation feature table into `main.py` (only after its stability is reviewed)
- Add FAO-56 soil-water balance model
- Add phenology-aware mango risk modeling
- Add Ensemble Kalman Filter state estimation
- Add Monte Carlo uncertainty simulation
- Add GCP deployment
- Add PostGIS support for farm boundary and parcel-level analysis
- Add validation against yield, APMC arrivals, or disease records
- Explore IndiaAI Compute only if a genuine GPU/scale need arises

See `MILESTONE_SUMMARY.md` for a beginner-friendly snapshot of what is and isn't built yet.

---

## 14. Research Direction

This project supports the idea of a sensor-free digital twin for mango orchard risk intelligence.

Research framing:


A sensor-free digital twin framework for mango orchards that integrates public weather, forecast, and soil intelligence to estimate irrigation stress, heat stress, and disease-friendly weather risk without field-deployed IoT sensors.


Future research version:


A sensor-free, phenology-aware, Bayesian digital twin for mango orchard risk forecasting using Earth observation, agro-weather fusion, soil intelligence, and physics-informed data assimilation.


---

## 15. Disclaimer

This project is a research and prototype system. The risk scores are not final agronomic recommendations. Field validation, expert calibration, and local farmer observations are required before operational use.
