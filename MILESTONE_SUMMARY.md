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

The Streamlit dashboard (`streamlit run app/streamlit_app.py`) has thirteen
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
8. **Mango Phenology** — current growth stage, stage descriptions and
   sensitivities, stage counts and timeline, monthly stage distribution.
9. **Phenology Water Balance** — the phenology-aware FAO-56 output, with
   Kc/ET0/ETc/depletion/Ks trends, stage-wise breakdowns, and a labeled
   prototype comparison against the constant-Kc Water Balance page (see
   below).
10. **FAO-56 Model Comparison** — day-by-day comparison of the constant-Kc
    and phenology-aware FAO-56 outputs: ETc differences, water-stress-level
    changes, and stage-wise breakdowns; reads
    `data/processed/muthukur_fao56_model_comparison.csv`.
11. **Irrigation Advisory** — the Forecast-Aware Irrigation Advisory:
    latest advisory action and priority callout (High / Medium / Low),
    FAO-56 water-stress context, forecast rainfall context, decision-rule
    table, technical details, limitations, and the raw single-row advisory
    snapshot; reads
    `data/processed/muthukur_forecast_aware_irrigation_advisory.csv`.
12. **What-if Simulator** — sliders to test rainfall/temperature/humidity
    changes and see the simulated risk impact.
13. **Raw Data** — expandable raw/processed tables for every data source.

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
  - Integrated into `main.py` as of the pipeline-integration milestone
    below — it no longer needs to be run manually as long as its two
    inputs already exist. It can still also be run standalone on its own.

---

## Phenology-Aware Water Balance Dashboard Milestone (new)

The phenology-aware FAO-56 output above is now visible in the Streamlit
dashboard, on a new **Phenology Water Balance** sidebar page, mirroring the
existing constant-Kc **Water Balance** page.

- **What it shows:** latest mango stage, Kc, ET0, ETc, root-zone
  depletion, Ks, and water-stress level; trend charts for Kc, ET0/ETc,
  depletion, and Ks; water-stress-level counts; stage-wise water-stress and
  ETc breakdowns; and an expandable raw data table.
- **Input CSV:** `data/processed/muthukur_fao56_phenology_water_balance.csv`
  (produced by `src/water_balance/fao56_phenology_water_balance.py`).
- **Output / dashboard page:** the **Phenology Water Balance** page in
  `app/streamlit_app.py`, sitting between the **Mango Phenology** and
  **What-if Simulator** pages in the sidebar. Where the original constant-Kc
  output (`data/processed/muthukur_fao56_water_balance.csv`) also exists,
  the page includes a labeled prototype comparison of ETc and water-stress
  counts between the two Kc approaches.
- **Limitations:**
  - Kc values are assumed, not cultivar-specific, and not field-calibrated.
  - Irrigation events are not yet included (rainfed-only depletion).
  - The underlying script is now run automatically by `python main.py
    --skip-fetch` / `python main.py` (see the pipeline-integration
    milestone below) whenever its two inputs already exist — it can also
    still be run manually/standalone the same as before.
  - The constant-Kc-vs-phenology-aware comparison is a prototype
    illustration only, not a validated model comparison.

The original constant-Kc Water Balance page and its underlying script/CSV
are unchanged by this addition.

---

## Pipeline Integration for Phenology-Aware FAO-56 Water Balance Milestone (new)

The phenology-aware FAO-56 water balance script described above is now
wired into the main pipeline, so it no longer has to be run as a separate
manual step every time.

- **What changed:** `src/pipeline/run_pipeline.py` gained one new,
  optional pipeline step. It is included in both the full pipeline
  (`python main.py`) and the cached-data pipeline (`python main.py
  --skip-fetch`).
- **Required input files:**
  - `data/processed/muthukur_combined_feature_table.csv`
  - `data/processed/muthukur_mango_phenology_calendar.csv`
- **Output file:** `data/processed/muthukur_fao56_phenology_water_balance.csv`
- **How it works:** the new pipeline step calls the existing
  `build_fao56_phenology_water_balance()` function from
  `src/water_balance/fao56_phenology_water_balance.py` directly — the
  FAO-56 and Kc-by-growth-stage math was **not duplicated** anywhere in
  the pipeline runner. If either required input file is missing, the step
  prints a clear message naming the missing file(s) and skips itself,
  without stopping the rest of the pipeline run.
- **What did not change:** `main.py` itself was **not directly modified**
  — it remains a thin entry point that delegates to
  `src/pipeline/run_pipeline.py`, exactly as before. The original
  constant-Kc FAO-56 script and its output CSV, the dashboard, and the
  underlying FAO-56/Kc math are all unchanged by this milestone. The
  standalone command (`python src/water_balance/fao56_phenology_water_balance.py`)
  still works exactly as before, independent of the pipeline.
- **Verification performed:** `python -m compileall app src tests main.py`
  (clean), `python -m pytest tests/ -v` (24/24 passed), `python main.py
  --skip-fetch` (confirmed the new step runs and regenerates the output
  CSV), and `streamlit run app/streamlit_app.py` (dashboard still launches
  cleanly).
- **Limitations carried forward unchanged:** Kc values are still
  first-pass assumptions, not cultivar-specific or field-calibrated;
  irrigation events are still not modeled; the combined feature table and
  the mango phenology calendar script itself are still standalone and not
  built automatically by the pipeline (only consumed by it, if already
  present).

---

## Unified Freshness-Aware Pipeline Orchestration Milestone (new)

The pipeline-integration milestone above wired in one script
(phenology-aware FAO-56) as a single optional step. This milestone replaces
that with a general, unified orchestration layer covering every downstream
output, so `python main.py --skip-fetch` now behaves as a real
near-real-time, one-command pipeline.

- **What changed:** `src/pipeline/run_pipeline.py` was rebuilt around a
  two-layer design. Layer 1 (unchanged) runs the original core fetch/risk
  steps in strict order, stopping on first failure as before. Layer 2 adds
  six freshness-aware steps, always run after Layer 1 regardless of Layer
  1's outcome: Sentinel-2 daily aggregation, the combined weather + soil +
  vegetation feature table, the mango phenology calendar, the constant-Kc
  FAO-56 water balance, the phenology-aware FAO-56 water balance, and the
  FAO-56 model comparison. Each Layer 2 step calls the corresponding
  standalone script's own existing build function directly — no FAO-56,
  Kc, or vegetation-index math was duplicated in the pipeline runner.
  `src/utils/pipeline_metadata.py` gained an additive `step_results` field
  recording, for every freshness-aware step, its name, status, and a short
  detail message.
- **Why it matters:** before this milestone, keeping every downstream
  output current meant remembering to run several scripts by hand in the
  right order, or risking stale dashboard data. Now a single command,
  `python main.py --skip-fetch`, brings every downstream output up to date
  from cached/raw data with no network calls — the project's "one-command
  regeneration" milestone. Each step is checked individually for missing
  required inputs (skipped with a warning, not a failure, so one missing
  upstream file doesn't break the whole run) and for freshness (skipped as
  `SKIP_FRESH` if its output is already newer than every required input,
  so unnecessary recomputation is avoided when nothing has changed).
- **Key outputs:**
  - `python main.py --skip-fetch` as the recommended day-to-day command,
    and `python main.py` (full fetch + everything above) as the full
    end-to-end option.
  - A per-step `RUN` / `SKIP_FRESH` / `SKIP_MISSING_INPUT` / `FAILED`
    status for each of the six freshness-aware steps, printed to the
    console and recorded in `data/processed/pipeline_run_metadata.json`
    under a new `step_results` array, alongside the metadata file's
    existing run timestamps, latest dates, row counts, and file
    modification times.
  - Every standalone script for every step still exists and still works
    exactly as before for targeted, single-step debugging — the pipeline
    command is additive, not a replacement for those scripts.
- **Limitations:**
  - Still local-only — no scheduler exists yet, so the pipeline must still
    be triggered manually every time; nothing runs it automatically on a
    timer.
  - No database — all inputs and outputs remain CSV/JSON files on the
    local disk.
  - No cloud deployment yet — storage, scheduling, and the dashboard all
    still run on the local PC, as planned for a later phase in
    `ROADMAP.md`.
  - No AI/ML yet — every step is still a transparent, rule-based or
    physics-informed calculation; nothing in this milestone introduces a
    trained model.
  - Freshness checks are based on file modification time, not on whether
    the underlying data actually changed — because the historical/forecast
    risk engines rewrite their output files on every run, most downstream
    steps will still show `RUN` (not `SKIP_FRESH`) on every consecutive
    pipeline invocation today; this is expected with the current design,
    not a bug.

---

## Forecast-Aware Irrigation Advisory Milestone (new)

`src/advisory/forecast_aware_irrigation.py` is a standalone module that
converts the project's water-stress monitoring into farmer-facing irrigation
decision support for the first time.

- **Inputs:**
  - `data/processed/muthukur_fao56_phenology_water_balance.csv` (phenology-aware
    FAO-56 water balance: latest mango stage, Ks coefficient, root-zone
    depletion, water stress level, Kc, ET0, ETc)
  - `data/processed/muthukur_open_meteo_forecast_risk.csv` (Open-Meteo forecast
    data, used for daily rainfall totals)
- **Output:** `data/processed/muthukur_forecast_aware_irrigation_advisory.csv` —
  a single-row snapshot with the advisory timestamp, current FAO-56 date, mango
  stage, water-stress status (Ks, level, ETc, root-zone depletion), forecast
  resolution and rainfall, and the advisory decision: `advisory_action`,
  `advisory_priority` (High / Medium / Low), `advisory_reason`, and
  `advisory_limitations`.
- **Method:** a rule-based decision engine combining three signals:
  1. Phenology-aware FAO-56 water stress level (Low / Medium / High) and Ks from
     the latest available row.
  2. Open-Meteo forecast daily rainfall for the next 24 hours (6 h and 12 h
     totals cannot be derived from daily-resolution data).
  3. Mango crop stage — Fruit set and Fruit development are treated as critical
     stages where even uncertain rain warrants partial irrigation.
- **Advisory actions (farmer-facing):**
  - *No irrigation needed now* — water stress is Low, regardless of forecast.
  - *Wait and monitor* — Medium stress with forecast rain ≥ 2 mm.
  - *Monitor closely; consider irrigation soon* — Medium stress, low forecast rain.
  - *Delay irrigation and recheck after rainfall* — High stress but ≥ 5 mm rain
    forecast, or High stress + non-critical stage with 2–5 mm uncertain rain.
  - *Apply partial irrigation and recheck* — High stress + critical crop stage
    (Fruit set or Fruit development) with 2–5 mm uncertain rain.
  - *Irrigate now or apply partial irrigation* — High stress with < 2 mm forecast
    rain, or forecast data unavailable.
- **Dashboard page:** new **Irrigation Advisory** sidebar page showing the latest
  advisory action and priority (colour-coded by `st.error` / `st.warning` /
  `st.success`), top-8 status metrics, a three-column FAO-56 / forecast /
  crop-stage context panel, the full decision-rule table, technical details, and
  an expandable limitations section; reads
  `data/processed/muthukur_forecast_aware_irrigation_advisory.csv`.
- **Pipeline integration:** the seventh freshness-aware step in
  `src/pipeline/run_pipeline.py`. `python main.py --skip-fetch` now regenerates
  the advisory output whenever the phenology-aware FAO-56 water balance or the
  forecast risk CSV is newer than the last advisory output.
- **Why it matters:** converts water-stress monitoring into actionable farmer
  guidance; prevents unnecessary irrigation when rain is expected in the next
  24 hours; gives context-aware recommendations that change by crop stage.
- **Limitations:**
  - Rule-based logic only — not AI or machine learning.
  - Forecast at daily resolution: 6 h and 12 h rainfall totals are not computable;
    thresholds use the next-24-hour total.
  - No soil-moisture sensor validation.
  - No irrigation-event history (water balance is rainfed-only depletion).
  - No yield or outcome validation.
  - Rainfall forecasts can change; re-run `python main.py --skip-fetch` before
    acting on the advisory.
  - This advisory should support, not replace, farmer judgment and local knowledge.

---

## Interpolated-Kc Water Balance and FAO-56 Sensitivity Analysis Milestone (new)

Two standalone research/analysis scripts added to improve the scientific quality
of the FAO-56 water-balance model and to quantify the uncertainty in its key
assumed parameters.

### Part A — Interpolated-Kc Water Balance

`src/water_balance/fao56_interpolated_kc_water_balance.py`

- **Problem addressed:** the existing phenology-aware FAO-56 script assigns one
  Kc value per mango growth stage (a step function), so Kc jumps abruptly at
  every stage boundary. In reality, a tree's water demand changes gradually as
  it moves through stages.
- **Approach:** "stage-midpoint linear" interpolation — the midpoint day of each
  contiguous stage block is the Kc anchor (full stage value); between consecutive
  anchors, Kc is linearly interpolated using `np.interp`. This replaces abrupt
  jumps with smooth transitions while keeping the same stage Kc targets.
- **Inputs:**
  - `data/processed/muthukur_combined_feature_table.csv`
  - `data/processed/muthukur_mango_phenology_calendar.csv`
- **Output:** `data/processed/muthukur_fao56_interpolated_kc_water_balance.csv`
  — 536 rows, same date range as the phenology-aware model.
- **Output columns:** `date`, `mango_stage`, `stage_kc` (step function, for
  comparison), `interpolated_kc` (smooth value used for ETc/depletion),
  `et0_mm_day`, `etc_mm_day`, `root_zone_depletion_mm`, `taw_mm`, `raw_mm`,
  `ks`, `water_stress_level`, `interpolation_method` ("stage_anchor" or
  "linear_midpoint").
- **Key statistics (baseline parameters: root=1.2 m, p=0.50):**
  - Interpolated Kc range: 0.60 – 0.90 (same bounds as stage Kc)
  - Mean |interpolated Kc − stage Kc| = 0.0275; max = 0.1611
  - Mean ETc = 3.80 mm/day; mean ET0 = 4.87 mm/day
  - Water stress: 304 High, 27 Medium, 205 Low days
- **Physics:** ET0, TAW, RAW, and depletion equations are identical to all
  other FAO-56 scripts (imported from `fao56_water_balance.py`, not
  duplicated). Only the Kc driving ETc changes.

### Part B — FAO-56 Sensitivity Analysis

`src/validation/fao56_sensitivity_analysis.py`

- **Problem addressed:** the FAO-56 water balance depends on three key
  parameters that are assumed, not measured at this orchard: root depth,
  depletion fraction *p*, and Kc (via a multiplier). It was not known how
  sensitive the outputs are to each assumption.
- **Approach:** full factorial 4 × 3 × 3 = 36 scenario grid:
  - Root depth: 0.8 / 1.0 / 1.2 (baseline) / 1.5 m
  - Depletion fraction *p*: 0.40 / 0.50 (baseline) / 0.60
  - Kc multiplier: 0.90 / 1.00 (baseline) / 1.10
- **Inputs:** same as above (combined feature table + phenology calendar).
- **Outputs:**
  - `data/processed/muthukur_fao56_sensitivity_analysis.csv` — 36-row table
    with per-scenario metrics (mean ETc, mean depletion, max depletion, TAW,
    RAW, High/Medium/Low stress days, % High-stress, and deltas from baseline)
  - `data/processed/muthukur_fao56_sensitivity_summary.md` — markdown report
    with per-parameter tables, worst/best-case scenarios, and interpretation
    notes
- **Key findings (536-day analysis period, 2025-01-01 – 2026-06-21):**
  - Baseline (root=1.2 m, p=0.50, Kc×1.00): 297 High-stress days (55.4%),
    mean ETc 3.78 mm/day, mean depletion 98.0 mm
  - Across all 36 scenarios: High-stress days range 264 – 327 (49 – 61%)
  - Mean ETc range: 3.40 – 4.16 mm/day; mean depletion range: 63 – 126 mm
  - Root depth has the largest effect on TAW/RAW and therefore stress count;
    deeper roots (1.5 m) reduce High-stress days by up to 33 vs 0.8 m
  - Kc multiplier has the largest per-unit effect on mean ETc
  - All three parameters interact: worst case (root=0.8 m, p=0.40, Kc×1.10)
    → 327 High days; best case (root=1.5 m, p=0.60, Kc×0.90) → 264 High days
  - ET0 is identical across all 36 scenarios (does not depend on Kc, root
    depth, or *p*), isolating water-stress effects from ET0 uncertainty

### Limitations

- Both scripts are **standalone only** — not yet wired into `main.py`,
  `run_pipeline.py`, or the dashboard. Running `python main.py --skip-fetch`
  does NOT regenerate these outputs.
- The interpolated Kc is more physically plausible than a step function but
  is still assumption-based and not field-calibrated. Real Kc dynamics depend
  on canopy size, cultivar, local microclimate, and irrigation practices.
- The sensitivity analysis quantifies the uncertainty band from three
  parameters; soil texture inputs from SoilGrids (a separate source of TAW/RAW
  uncertainty) are not varied here.
- No soil-moisture sensor validation.
- No yield or outcome validation.
- Stage Kc anchor values are still first-pass assumptions from general FAO-56 /
  mango guidance, not measured at this orchard.

### Why it matters

The sensitivity analysis is the first step in this project that explicitly
documents the uncertainty around the FAO-56 water-stress signal rather than
presenting a single baseline number. Knowing that High-stress days can range
from 264 to 327 (±10% relative to baseline) depending on plausible parameter
values gives important context for interpreting all FAO-56 outputs in this
project, and sets a baseline against which future field calibration can be
measured.

## What Has Not Been Done Yet

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
- No real scheduler yet — `python main.py --skip-fetch` is a single command
  that can regenerate every downstream output, but nothing triggers that
  command automatically; every run is still manually invoked.
- No database yet — all data still lives in local CSV/JSON files.

## Recommended Next Steps

1. **Optional Git commit** — commit this stable state as a checkpoint for
   the forecast-aware irrigation advisory milestone, so it can be returned
   to if later changes need to be rolled back.
2. **Add a real scheduler** for unattended/recurring pipeline runs, now
   that the pipeline itself is unified and freshness-aware and only needs
   to be triggered.
3. **Calibrate the phenology-aware Kc values** against local or
   cultivar-specific data as it becomes available.
4. **Add irrigation-event, runoff, and deep-percolation tracking** to the
   water balance, moving it past a rainfed-only prototype.
5. **Later, prepare cloud deployment** — once the local system and
   phenology work are stable, move storage, scheduling, and the dashboard
   to the cloud (GCP, as planned in `ROADMAP.md`).
6. **Later, explore IndiaAI only if GPU-heavy work is needed** — for example,
   if a future ML or deep-learning model genuinely requires GPU compute at
   scale.

---

This project is a research and prototype system. The risk scores and
vegetation interpretations are not final agronomic recommendations. Field
validation, expert calibration, and local farmer observations are still
required before any operational use.
