# Developer Command Checklist

Quick reference for running, testing, and verifying the Sensor-Free Mango
Digital Twin project on your local machine. Everything here runs on your
laptop — no cloud, no GPU, no external accounts required beyond the free
weather/soil APIs the pipeline already calls.

## 1. Install requirements

```bash
pip install -r requirements.txt
```

Run this once, and again any time `requirements.txt` changes (it now
includes `pytest` for running tests).

## 2. Run the full pipeline (recommended for daily use)

```bash
python main.py
```

This is the **full pipeline refresh**: fetches fresh raw data from NASA POWER,
Open-Meteo, and SoilGrids, runs both risk engines, then runs all nine
freshness-aware downstream steps. Use this command for the daily scheduled run
and any time you want up-to-date raw data.

For offline/rebuild mode (no network calls — recomputes from raw data already on disk):

```bash
python main.py --skip-fetch
```

Use `--skip-fetch` for local testing and development when you do not want to
re-fetch. Both commands run in two layers:

1. **Core risk recomputation** — historical risk and forecast risk are
   recomputed from the weather/soil CSVs already saved in `data/raw/`.
2. **Freshness-aware downstream steps**, run in dependency order: Sentinel-2
   daily aggregation, the combined feature table, the mango phenology
   calendar, the constant-Kc FAO-56 water balance, the phenology-aware
   FAO-56 water balance, the FAO-56 model comparison, and the
   forecast-aware irrigation advisory. Each step calls the corresponding
   standalone script's own existing build function directly — no
   scientific/model logic is duplicated in the pipeline runner.

Each downstream step prints one of four statuses, also recorded per-step in
`data/processed/pipeline_run_metadata.json`:

- **`RUN`** — the step's output was missing, or older than at least one of
  its required inputs, so it was regenerated.
- **`SKIP_FRESH`** — the step's output already exists and is newer than
  every required input, so it was left alone.
- **`SKIP_MISSING_INPUT`** — a required input file doesn't exist yet, so
  the step was skipped with a warning instead of failing the whole run.
- **`FAILED`** — the step's build function raised an exception or reported
  failure; the rest of the pipeline still continues, and the failure is
  recorded in the metadata JSON.

Using `--skip-fetch` is the fastest way to confirm your code changes didn't
break the scoring or modeling logic, and it works with no internet connection.

## 3. Automate daily refresh (Windows Task Scheduler)

A PowerShell script is provided for hands-free daily runs:

```powershell
.\scripts\run_daily_pipeline.ps1
```

This activates the virtual environment, runs `python main.py`, saves a
timestamped log under `logs\daily_pipeline\`, and exits with code 1 on failure.
Configure it as a Windows Task Scheduler task that runs daily at 6 AM — see
`docs\DAILY_REFRESH_WINDOWS.md` for the full setup guide.

Both `python main.py` and `python main.py --skip-fetch` are thin entry
points into `src/pipeline/run_pipeline.py`, which is where the actual step
list lives (`main.py` itself was not changed by the orchestration
milestone). **Every standalone script for every step above still exists
and can be run individually** (see step 7 below) for targeted debugging of
one specific step — but the recommended workflow for normal use is
`python main.py` (full refresh with fetch) for the daily automated run, or
`python main.py --skip-fetch` for fast offline rebuilds, not running each
script by hand. For example, the phenology-aware FAO-56 script can still be run on
its own:

```bash
python src/water_balance/fao56_phenology_water_balance.py
```

The original constant-Kc FAO-56 output
(`data/processed/muthukur_fao56_water_balance.csv`, see step 7.11) and the
phenology-aware output are both now regenerated automatically by the
unified pipeline command in step 2 above, as long as their own required
inputs already exist.

## 4. Run the Streamlit dashboard

```bash
streamlit run app/streamlit_app.py
```

Opens the dashboard in your browser. If a data file is missing, the
relevant section shows a friendly warning instead of crashing — you don't
need to run the full pipeline first to explore the dashboard. This includes
the **Vegetation Health** page, which shows Sentinel-2 NDVI/NDWI/NDMI/NDRE
trends if `data/processed/muthukur_sentinel2_daily_indices.csv` exists (see
step 7.8), the **Combined Intelligence** page, which shows the combined
weather + soil + vegetation view if
`data/processed/muthukur_combined_feature_table.csv` exists (see step 7.9),
the **Water Balance** page, which shows the FAO-56 soil-water balance
output if `data/processed/muthukur_fao56_water_balance.csv` exists (see
step 7.11), the **Phenology Water Balance** page, which shows the
phenology-aware FAO-56 output if
`data/processed/muthukur_fao56_phenology_water_balance.csv` exists (see
step 7.14), and the **Irrigation Advisory** page, which shows the
forecast-aware irrigation advisory if
`data/processed/muthukur_forecast_aware_irrigation_advisory.csv` exists
(see step 7.16) — each page shows a friendly warning with the exact command
to run if its own file doesn't exist yet. As of the unified pipeline
orchestration milestone, `python main.py --skip-fetch` (see step 2 above)
now regenerates **all** of these output CSVs automatically — the combined
feature table, the constant-Kc FAO-56 script, the mango phenology
calendar, the phenology-aware FAO-56 script, and the forecast-aware
irrigation advisory no longer need to be run manually before their
dashboard pages show data, as long as their own required inputs
(ultimately, the raw weather/soil/Sentinel-2 data) already exist on disk.

## 5. Run the tests

```bash
python -m pytest tests/ -v
```

The test suite covers config loading, column validation, risk-level
classification, soil-factor calculation, and `-999` missing-value
cleaning. Tests use only the real local config or small in-memory sample
data — no network calls, no cloud, no GPU.

## 6. Check syntax across the whole project

```bash
python -m py_compile $(find . -name "*.py" -not -path "./.venv/*" -not -path "./venv/*")
```

Confirms every Python file in the project parses without syntax errors.
Useful to run before committing changes or after editing several files.

## What "it's working" looks like

After steps 1–6 above, you should see:
- Step 2 prints a console summary ending with `Core pipeline (fetch/risk)
  finished successfully.`, followed by a `RUN` / `SKIP_FRESH` /
  `SKIP_MISSING_INPUT` / `FAILED` line for each of the nine freshness-aware
  downstream steps, and finally `Pipeline run metadata written to:
  data/processed/pipeline_run_metadata.json`.
- Step 5 ends with all tests showing `PASSED` and a line like `24 passed
  in 1.22s`.
- Step 6 produces no output (silence means no syntax errors).
- `logs/pipeline.log` contains a fresh `STARTING` / `SUCCEEDED` line for
  each pipeline step you just ran.
- `data/processed/pipeline_run_metadata.json` contains a `step_results`
  array listing every freshness-aware step's name, status, and detail from
  the most recent run.
- If a daily scheduled run completed, a timestamped log file will exist
  under `logs/daily_pipeline/` (e.g. `daily_pipeline_2025-06-15_06-00-01.log`).

## 7. Google Earth Engine setup (Sentinel-2 prep phase)

This project is starting to prepare for Sentinel-2 satellite imagery via
Google Earth Engine (GEE). As of now this is **setup only** — no satellite
data is fetched, no NDVI/NDWI/NDMI/NDRE indices are calculated yet, and
nothing about the existing weather/soil pipeline changes. This section
just gets your machine ready for that future work.

### 7.1 Install the Earth Engine Python API

Already included in `requirements.txt` (step 1 above installs it), but if
you need to install it on its own:

```bash
pip install earthengine-api
```

### 7.2 Get access to Earth Engine (one-time, free for research/non-commercial use)

Google Earth Engine requires a Google account to be registered for access.
If you haven't done this yet, sign up at https://earthengine.google.com/signup/
(this is a one-time step done in your browser, not from this project).

### 7.3 Authenticate on your machine (one-time per machine)

```bash
earthengine authenticate
```

This opens a browser window asking you to log in with the Google account
you registered with Earth Engine, then stores a local credential file on
your machine. You do not need to repeat this every time you run the
project — only once per machine (or after credentials expire/are revoked).

### 7.4 Test that authentication worked

```bash
python src/remote_sensing/gee_setup.py
```

This script ONLY tries to initialize Earth Engine and reports one of three
outcomes:
- `earthengine-api` is not installed → tells you to `pip install earthengine-api`.
- Installed but not authenticated → tells you to run `earthengine authenticate`.
- Installed and authenticated → prints "Success" and shows the
  `remote_sensing` settings currently in `configs/config.yaml`.

It does not download any satellite imagery — it is safe to run at any time,
as often as you like, to check your setup status.

### 7.5 Check Sentinel-2 image availability (metadata only, no downloads)

Once `gee_setup.py` reports success, you can check whether usable Sentinel-2
scenes actually exist for your orchard's location and date range:

```bash
python src/remote_sensing/check_sentinel2_availability.py
```

This queries the Sentinel-2 Surface Reflectance collection
(`COPERNICUS/S2_SR_HARMONIZED`) for your configured latitude/longitude
(+ buffer), date range, and cloud-cover threshold, and prints:
- How many scenes matched.
- Each scene's date and cloud-cover percentage.

It only requests small metadata fields (scene count, timestamps, cloud
cover) — no pixel/band data is downloaded, and no indices are computed.
This is purely a "does imagery exist for what I want to study?" check before
any real fetching work begins.

### 7.6 Test real index values for one scene (standalone, small CSV only)

Once availability is confirmed, you can prove out the actual index math on
one real scene:

```bash
python src/remote_sensing/test_single_scene_indices.py
```

This selects the single lowest-cloud Sentinel-2 scene for your configured
area/date range, computes the mean NDVI, NDWI, NDMI, and NDRE over the
buffer, and writes one row to:

```
data/processed/muthukur_sentinel2_single_scene_indices.csv
```

with columns `date`, `image_id`, `cloud_percentage`, `ndvi_mean`,
`ndwi_mean`, `ndmi_mean`, `ndre_mean`, `latitude`, `longitude`, `buffer_m`.

This is a standalone proof-of-concept only — it is **not** wired into
`main.py` or the Streamlit dashboard. No raster/image data is downloaded,
only the four mean scalar values per scene.

### 7.7 Build a multi-date vegetation index time series (standalone, small CSV only)

Once the single-scene test works, you can build the same index values across
every usable scene in the configured date range:

```bash
python src/remote_sensing/build_sentinel2_index_timeseries.py
```

This computes NDVI/NDWI/NDMI/NDRE means for every scene returned by the
same query check_sentinel2_availability.py uses, in one batched Earth Engine
request (not one network round trip per scene), and writes one row per
scene to:

```
data/processed/muthukur_sentinel2_index_timeseries.csv
```

with the same columns as the single-scene CSV. Sentinel-2 can return more
than one image for the same calendar date (overlapping tiles/orbits) — those
are kept as separate rows; this script does not aggregate by date or month.
It logs how many scenes were found, processed, and skipped, and is still
standalone: not wired into `main.py` or the dashboard, no raster downloads.

### 7.8 Aggregate the time series into one row per day

Sentinel-2 can return more than one scene for the same calendar date
(overlapping tiles). This step collapses those into one daily row, with no
Earth Engine connection required — it only reshapes the CSV from step 7.7:

```bash
python src/remote_sensing/aggregate_sentinel2_timeseries.py
```

Input: `data/processed/muthukur_sentinel2_index_timeseries.csv`
Output: `data/processed/muthukur_sentinel2_daily_indices.csv`

For each date: `ndvi_mean`/`ndwi_mean`/`ndmi_mean`/`ndre_mean` and
`cloud_percentage` are averaged across that day's scenes (cloud_percentage
uses mean rather than minimum so it stays consistent with the
already-averaged index values, instead of describing just one scene), and
`scene_count` records how many scenes contributed. Three added columns —
`ndvi_level`, `moisture_level`, `canopy_stress_level` — give a
beginner-friendly label (e.g. "Moderate vegetation greenness") alongside the
real numeric values, using fixed thresholds documented in the script's
docstring. Still standalone: not wired into `main.py` or the dashboard yet.

### 7.9 Build a combined weather + soil + vegetation feature table

Once the daily vegetation CSV exists, you can join it with the historical
weather/risk data and the static SoilGrids soil data into one combined
table — still standalone, no Earth Engine connection needed:

```bash
python src/features/build_feature_table.py
```

Inputs:
- `data/processed/muthukur_weather_risk_scores.csv`
- `data/processed/muthukur_sentinel2_daily_indices.csv`
- `data/raw/muthukur_soilgrids.csv`

Output: `data/processed/muthukur_combined_feature_table.csv`

For each historical weather date, this attaches the most recent Sentinel-2
vegetation observation that happened **on or before** that date (never a
later one — a satellite image from after the date would let the table
"see the future"), plus how many days old that observation is
(`days_since_sentinel2_observation`) and a `vegetation_data_freshness`
label (`Fresh` / `Moderate` / `Stale` / `Missing`). It also attaches the
constant SoilGrids soil properties (sand/silt/clay %, pH, organic carbon,
bulk density, CEC, soil irrigation factor) to every row. It logs input/
output row counts and vegetation match coverage. The resulting CSV is shown
on the dashboard's **Combined Intelligence** page (see below). As of the
unified pipeline orchestration milestone, this script is also regenerated
automatically by `python main.py --skip-fetch` (step 2 above) whenever its
own required inputs already exist — it can still be run standalone for
targeted debugging using the command above.

### 7.10 Combined Intelligence dashboard page

Once the combined feature table exists, the dashboard's **Combined
Intelligence** sidebar page shows it directly — no extra command needed
beyond step 4 above (`streamlit run app/streamlit_app.py`). The page
includes latest-status metrics (date, irrigation/heat/disease risk, NDVI,
NDMI, vegetation freshness, soil irrigation factor), a date-range and
vegetation-freshness filter, risk and vegetation trend charts, a dual-axis
irrigation-risk-vs-NDVI chart, a freshness-count chart, four interpretation
rules (possible water stress, disease-friendly conditions, combined stress,
stale-data warning), and an expandable raw table. It is read-only and does
not change `main.py` or any other dashboard page.

### 7.11 Build the FAO-56 soil-water balance (standalone, small CSV only)

Once the combined feature table exists, you can compute a daily FAO-56
Penman-Monteith soil-water balance — still standalone, no Earth Engine
connection needed:

```bash
python src/water_balance/fao56_water_balance.py
```

Input: `data/processed/muthukur_combined_feature_table.csv`

Output: `data/processed/muthukur_fao56_water_balance.csv`

For each date, this computes reference evapotranspiration (ET0) via the
FAO-56 Penman-Monteith equation, estimated crop water use (ETc = ET0 × Kc,
with Kc currently held constant at 0.75), total/readily available water
(TAW/RAW) from Saxton-Rawls field-capacity and wilting-point estimates
based on SoilGrids texture, a root-zone depletion balance driven by
rainfall and ETc, the Ks water-stress coefficient, and a Low/Medium/High
water-stress level. It logs TAW/RAW and a water-stress-day breakdown. The
resulting CSV is shown on the dashboard's **Water Balance** page (see
below). **This is a simplified rainfed prototype**: Kc is constant (not
phenology-aware), there are no modeled irrigation events, and there is no
separate runoff/deep-percolation accounting. As of the unified pipeline
orchestration milestone, this script is also regenerated automatically by
`python main.py --skip-fetch` (step 2 above) whenever its required input
already exists — it can still be run standalone for targeted debugging
using the command above.

### 7.12 Water Balance dashboard page

Once the FAO-56 CSV exists, the dashboard's **Water Balance** sidebar page
shows it directly — no extra command needed beyond step 4 above
(`streamlit run app/streamlit_app.py`). The page includes a disclaimer that
this is a simplified rainfed prototype, latest-status metrics (date, ET0,
ETc, root-zone depletion, Ks, water-stress level, TAW, RAW), ET0+ETc and
rainfall+ETc charts, a depletion chart with RAW/TAW reference lines, a Ks
trend chart, a water-stress-level count chart, interpretation notes for
each term, and an expandable raw table. It is read-only and does not
change `main.py` or any other dashboard page.

### 7.13 Build the phenology-aware FAO-56 soil-water balance (standalone, small CSV only)

Once both the combined feature table and the mango phenology calendar
(`data/processed/muthukur_mango_phenology_calendar.csv`) exist, you can
compute a second, separate FAO-56 soil-water balance that uses a
growth-stage-aware crop coefficient instead of the constant Kc = 0.75 —
still standalone, no Earth Engine connection needed:

```bash
python src/water_balance/fao56_phenology_water_balance.py
```

Inputs:
- `data/processed/muthukur_combined_feature_table.csv`
- `data/processed/muthukur_mango_phenology_calendar.csv`

Output: `data/processed/muthukur_fao56_phenology_water_balance.csv`

This joins the two input tables by date, looks up a Kc value for each row's
`mango_stage` (Flower induction/pre-flowering 0.65, Flowering 0.75, Fruit
set 0.85, Fruit development 0.90, Maturity/harvest 0.80, Rest/vegetative
0.60), and reuses the same ET0/TAW/RAW/depletion logic as
`fao56_water_balance.py` (step 7.11) to compute `etc_mm_day`,
`root_zone_depletion_mm`, `ks`, `water_stress_score`, and
`water_stress_level`. It logs stage day counts, Kc-by-stage, and a
water-stress breakdown. **The original constant-Kc FAO-56 script and its
output CSV (step 7.11) are not modified.** As of the unified pipeline
orchestration described in step 2 above, this script is **no longer
standalone with respect to the pipeline**: `python main.py --skip-fetch` (and full
`python main.py`) now runs it automatically, via a step in
`src/pipeline/run_pipeline.py` that calls this script's existing
`build_fao56_phenology_water_balance()` function directly (no math
duplicated, `main.py` itself unchanged). The standalone command shown
above still works exactly the same, independent of the pipeline. The Kc
values above are first-pass assumptions based on general mango/FAO-56
guidance — not field-calibrated or cultivar-specific for this orchard.

### 7.14 Phenology Water Balance dashboard page

Once the phenology-aware FAO-56 CSV exists, the dashboard's **Phenology
Water Balance** sidebar page shows it directly — no extra command needed
beyond step 4 above:

```bash
streamlit run app/streamlit_app.py
```

The page is visible in the sidebar between **Mango Phenology** and
**What-if Simulator**. It includes latest-status metrics (date, mango
stage, Kc, ET0, ETc, root-zone depletion, Ks, water-stress level); Kc,
ET0/ETc, depletion, and Ks trend charts; water-stress-level counts and
stage-wise water-stress/ETc breakdowns; a labeled prototype comparison of
ETc and water-stress counts against the constant-Kc Water Balance output
when `data/processed/muthukur_fao56_water_balance.csv` also exists;
interpretation notes on how Kc and water sensitivity change by stage; and
an expandable raw table. It carries an explicit disclaimer that this is a
simplified, assumption-based, non-field-calibrated prototype with no
irrigation events modeled yet. It is read-only and does not change
`main.py` or any other dashboard page. As of the unified pipeline
orchestration milestone, `python main.py --skip-fetch` (step 2 above) now
regenerates this script's output CSV automatically whenever its required
inputs already exist, so manually running step 7.13 first is no longer
required.

### 7.16 Generate the forecast-aware irrigation advisory (standalone)

Once the phenology-aware FAO-56 water balance and the Open-Meteo forecast
risk CSV both exist, you can generate the irrigation advisory directly — no
Earth Engine connection needed:

```bash
python src/advisory/forecast_aware_irrigation.py
```

Inputs:
- `data/processed/muthukur_fao56_phenology_water_balance.csv`
- `data/processed/muthukur_open_meteo_forecast_risk.csv`

Output: `data/processed/muthukur_forecast_aware_irrigation_advisory.csv`

The script reads the **latest row** from the phenology-aware water balance
(Ks coefficient, root-zone depletion, water stress level, mango stage, Kc,
ET0, ETc) and looks up the first forecast day's daily rainfall from the
Open-Meteo forecast CSV. It applies a rule-based decision engine — combining
water stress level (Low / Medium / High), Ks, forecast daily rainfall, and
mango stage sensitivity (Fruit set and Fruit development are treated as
critical stages) — and writes a single-row output CSV with the advisory
action, priority, reason, and limitations.

The advisory is printed to the console as a formatted summary when run
directly. It is also regenerated automatically by
`python main.py --skip-fetch` (step 2 above) as the ninth freshness-aware
downstream step, whenever either input is newer than the last advisory.

**Note on forecast resolution:** only daily forecast data is available from
Open-Meteo in this project. 6-hour and 12-hour rainfall totals cannot be
computed; decision thresholds are applied to the next-24-hour total. Rain
probability is also not in the current Open-Meteo daily output.

### 7.17 Irrigation Advisory dashboard page

Once the advisory CSV exists, the dashboard's **Irrigation Advisory** sidebar
page shows it directly — no extra command needed beyond step 4 above:

```bash
streamlit run app/streamlit_app.py
```

The page is visible in the sidebar between **FAO-56 Model Comparison** and
**What-if Simulator**. It includes:
- A priority callout (green / amber / red, matching Low / Medium / High)
  showing the advisory action and reason.
- Top-8 status metrics: generated timestamp, FAO-56 date, mango stage,
  water stress level, Ks, ETc, root-zone depletion, and forecast rain.
- A three-column context panel (FAO-56 water balance / forecast inputs /
  crop stage).
- The full eight-row decision-rule reference table.
- Technical details (FAO-56 parameters and forecast inputs) in an expander.
- An expandable limitations section parsing each limitation from the CSV.
- The raw single-row advisory snapshot in an expander.

It carries an explicit disclaimer that this is rule-based decision support,
not AI or machine learning, and that it should support but not replace farmer
judgment and local knowledge. It is read-only and does not change `main.py`
or any other dashboard page.

### 7.18 Generate the interpolated-Kc FAO-56 water balance (standalone research script)

A separate, standalone research script smooths the Kc transitions between mango
phenology stages.  Instead of the abrupt step-function Kc used in
`fao56_phenology_water_balance.py`, it uses "stage-midpoint linear" interpolation:
the midpoint day of each stage block is the Kc anchor, and Kc is linearly
interpolated between consecutive anchors:

```bash
python src/water_balance/fao56_interpolated_kc_water_balance.py
```

Inputs:
- `data/processed/muthukur_combined_feature_table.csv`
- `data/processed/muthukur_mango_phenology_calendar.csv`

Output: `data/processed/muthukur_fao56_interpolated_kc_water_balance.csv`

The output CSV includes both `stage_kc` (the step-function value, same as the
phenology-aware script) and `interpolated_kc` (the smoothed value), so the two
approaches can be compared directly. The `interpolation_method` column labels each
day as "stage_anchor" or "linear_midpoint" so the smoothing is always traceable.

The ET0, TAW, RAW, and depletion equations are identical to all other FAO-56
scripts in this project (imported directly from `fao56_water_balance.py`, not
duplicated). Only the Kc driving ETc changes.

**Pipeline integration:** this script is now the **sixth freshness-aware step** in
`src/pipeline/run_pipeline.py` — `python main.py --skip-fetch` regenerates its output
automatically whenever the combined feature table or phenology calendar is newer.
The existing constant-Kc and stage-Kc water balance CSVs are untouched. The
interpolation is still assumption-based and not field-calibrated. Not yet on the dashboard.

### 7.19 Run the FAO-56 sensitivity analysis (standalone research script)

A standalone sensitivity analysis tests how much the FAO-56 water-stress outputs
change when the three key assumed parameters are varied across a full factorial grid
(4 × 3 × 3 = 36 scenarios):

```bash
python src/validation/fao56_sensitivity_analysis.py
```

Inputs:
- `data/processed/muthukur_combined_feature_table.csv`
- `data/processed/muthukur_mango_phenology_calendar.csv`

Parameters varied:

| Parameter | Values | Baseline |
|---|---|---|
| Root depth | 0.8 / 1.0 / 1.2 / 1.5 m | 1.2 m (config) |
| Depletion fraction *p* | 0.40 / 0.50 / 0.60 | 0.50 (config) |
| Kc multiplier | 0.90 / 1.00 / 1.10 | 1.00 |

Outputs:
- `data/processed/muthukur_fao56_sensitivity_analysis.csv` — 36-row scenario table
  with mean ETc, mean depletion, High/Medium/Low stress day counts, and deltas from
  baseline for every combination
- `data/processed/muthukur_fao56_sensitivity_summary.md` — markdown report with
  per-parameter tables, worst/best-case scenarios, and interpretation notes

**Pipeline integration:** this script is now the **eighth freshness-aware step** in
`src/pipeline/run_pipeline.py` — `python main.py --skip-fetch` regenerates both output
files automatically whenever the combined feature table or phenology calendar is newer.
It does not overwrite any existing water-balance CSV. First explicit
uncertainty-quantification step in this project. Not yet on the dashboard.

### 7.15 What's configured so far

`configs/config.yaml` now has a `remote_sensing` section with the study
area's latitude/longitude, an optional buffer radius (meters) for defining
a small area of interest instead of a single point, a start/end date range,
and a Sentinel-2 cloud-cover threshold. These values are not used by the
main pipeline yet — they're there so this and future remote-sensing work has
a single place to read settings from, consistent with how the rest of this
project avoids hardcoded values.

`src/remote_sensing/sentinel2_indices.py` documents what NDVI, NDWI, NDMI,
and NDRE mean and why they matter for a mango orchard, with stub functions
that raise `NotImplementedError` for now. `test_single_scene_indices.py`
(step 7.6) proves the real calculations work on one scene,
`build_sentinel2_index_timeseries.py` (step 7.7) extends that across every
usable scene in the date range, and `aggregate_sentinel2_timeseries.py`
(step 7.8) collapses that into one clean daily row with simple
greenness/moisture/canopy-stress labels; full pipeline integration is still
a later phase.

## Where things live

- `src/utils/logger.py` — shared logging setup. Every pipeline script logs
  to both the terminal and `logs/pipeline.log`.
- `src/utils/validation.py` — shared column-validation checks for weather,
  soil, and risk data. Raises a clear `MissingColumnsError` if a file is
  missing expected columns.
- `tests/` — lightweight local tests (see step 5).
- `logs/pipeline.log` — running log of every pipeline run. Safe to delete;
  it will be recreated automatically.
- `src/utils/soil_factor.py` — single shared soil-adjusted irrigation
  factor calculation, used by both risk engines and the dashboard so the
  same soil values always produce the same factor everywhere.
- `src/remote_sensing/` — Sentinel-2 / Google Earth Engine prep (see step 7
  above). `gee_setup.py` checks your authentication status; `check_sentinel2_availability.py`
  confirms usable scenes exist for your area/date range (metadata only);
  `test_single_scene_indices.py` computes real NDVI/NDWI/NDMI/NDRE means for
  one scene as a standalone CSV test; `build_sentinel2_index_timeseries.py`
  extends that to every usable scene in the date range, one row per scene;
  `aggregate_sentinel2_timeseries.py` collapses duplicate-date scenes into
  one daily row with greenness/moisture/canopy-stress labels;
  `sentinel2_indices.py` documents what each index means, with stub
  functions for the eventual full integration. The resulting daily CSV is
  shown on the dashboard's **Vegetation Health** page (see below) — this is
  the first remote-sensing data visible in the dashboard, but it is not yet
  merged into the irrigation/heat/disease risk scores.
- `src/features/build_feature_table.py` (step 7.9) — joins the historical
  weather/risk CSV, the daily Sentinel-2 vegetation CSV, and the static
  SoilGrids soil CSV into one combined table
  (`data/processed/muthukur_combined_feature_table.csv`), using the
  nearest *previous* Sentinel-2 observation for each weather date (never a
  future one) plus a freshness flag. As of the unified pipeline
  orchestration milestone, `python main.py --skip-fetch` also regenerates
  this output automatically whenever its required inputs already exist —
  its output CSV is shown on the dashboard's **Combined Intelligence** page
  (step 7.10), the first page that interprets weather risk, soil
  conditions, and vegetation health together. This is still prep work for
  FAO-56 modeling and (much later) ML.
- `src/water_balance/fao56_water_balance.py` (step 7.11) — computes a daily
  FAO-56 Penman-Monteith soil-water balance (ET0, ETc, TAW, RAW, root-zone
  depletion, Ks water-stress coefficient) from the combined feature table,
  writing `data/processed/muthukur_fao56_water_balance.csv`. Shown on the
  dashboard's **Water Balance** page (step 7.12) — the first
  physics-informed water-stress view in the project. As of the unified
  pipeline orchestration milestone, this output is also regenerated
  automatically by `python main.py --skip-fetch` whenever its required
  input already exists. Known limitations of this prototype: a
  constant crop coefficient (Kc = 0.75, not phenology-aware), rainfed-only
  depletion (no modeled irrigation events), no runoff/deep-percolation
  accounting, and no field validation.
- `src/water_balance/fao56_phenology_water_balance.py` (step 7.13) — a
  separate, parallel FAO-56 script that joins the combined feature table
  with the mango phenology calendar and assigns Kc by growth stage instead
  of the constant 0.75, reusing the same ET0/TAW/RAW/depletion logic as
  `fao56_water_balance.py`. Writes
  `data/processed/muthukur_fao56_phenology_water_balance.csv`. Does not
  modify the original constant-Kc script or CSV. Shown on the dashboard's
  **Phenology Water Balance** page (step 7.14). As of the unified pipeline
  orchestration milestone, this is one of nine freshness-aware steps in
  `src/pipeline/run_pipeline.py` that call each script's own existing build
  function directly, with no math duplicated — `python main.py
  --skip-fetch` and full `python main.py` both regenerate its output CSV
  automatically whenever the combined feature table and phenology calendar
  already exist; the standalone command above still works on its own too.
  `main.py` itself was not modified. Kc values are first-pass assumptions,
  not field-calibrated or cultivar-specific.
- `src/validation/compare_fao56_models.py` — compares the constant-Kc and
  phenology-aware FAO-56 outputs day by day (ETc differences, stress-level
  changes, stage-wise breakdowns), writing
  `data/processed/muthukur_fao56_model_comparison.csv` and a markdown
  summary. This is the sixth freshness-aware step in `run_pipeline.py`,
  regenerated automatically by `python main.py --skip-fetch` whenever both
  FAO-56 outputs already exist. Its output is shown on the dashboard's
  **FAO-56 Model Comparison** sidebar page.
- `src/advisory/forecast_aware_irrigation.py` (step 7.16) — the
  standalone Forecast-Aware Irrigation Advisory module. Reads the latest
  row from the phenology-aware FAO-56 water balance and the current
  Open-Meteo forecast risk CSV, applies a rule-based decision engine that
  combines FAO-56 water-stress level (Low / Medium / High), Ks coefficient,
  mango crop stage, and forecast daily rainfall to produce a single-row
  advisory snapshot. This is the ninth and final freshness-aware step in
  `run_pipeline.py`, regenerated automatically by
  `python main.py --skip-fetch` whenever either input is newer than the
  last advisory output. Output:
  `data/processed/muthukur_forecast_aware_irrigation_advisory.csv`. Known
  limitations: rule-based (not AI/ML), daily forecast resolution only
  (6 h / 12 h totals unavailable), no soil-moisture sensor validation, no
  irrigation-event history, no yield validation. Advisory should support
  but not replace farmer judgment.
- `src/water_balance/fao56_interpolated_kc_water_balance.py` (step 7.18) — a
  standalone research script that produces a smoothly interpolated Kc series
  from the stage-Kc step function, using "stage-midpoint linear" interpolation
  (`np.interp` between the midpoint of each contiguous stage block). Imports
  ET0, TAW/RAW, and depletion functions directly from `fao56_water_balance.py`
  — no physics duplicated. Output CSV includes both `stage_kc` and
  `interpolated_kc` columns for direct comparison, plus `interpolation_method`
  labelling each day. Output:
  `data/processed/muthukur_fao56_interpolated_kc_water_balance.csv`.
  Now the sixth freshness-aware step in `run_pipeline.py` — regenerated
  automatically by `python main.py --skip-fetch`. The existing constant-Kc
  and stage-Kc CSVs are untouched. Still assumption-based, not field-calibrated.
  Not yet on the dashboard.
- `src/validation/fao56_sensitivity_analysis.py` (step 7.19) — a standalone
  sensitivity analysis that runs the FAO-56 phenology-aware water balance across
  a full factorial grid of 4 × 3 × 3 = 36 parameter combinations (root depth ×
  depletion fraction × Kc multiplier) and records per-scenario metrics and
  deltas from the baseline in a 36-row CSV and a markdown summary. First
  explicit uncertainty-quantification step in this project. Now the eighth
  freshness-aware step in `run_pipeline.py` — regenerated automatically by
  `python main.py --skip-fetch`. Not yet on the dashboard.
