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

## 2. Run the full pipeline (fetches fresh data)

```bash
python main.py
```

This fetches fresh weather (NASA POWER, Open-Meteo) and soil (SoilGrids)
data, then runs both risk engines. Use this when you want up-to-date
numbers. It needs an internet connection.

## 3. Run the pipeline without re-fetching (uses cached CSVs)

```bash
python main.py --skip-fetch
```

This re-runs only the risk-scoring steps against the weather/soil CSVs
already saved in `data/raw/`. Use this for quick local testing, or when
you have no internet connection. It's also the fastest way to confirm
your code changes didn't break the scoring logic.

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
and the **Water Balance** page, which shows the FAO-56 soil-water balance
output if `data/processed/muthukur_fao56_water_balance.csv` exists (see
step 7.11) — each page shows a friendly warning with the exact command to
run if its own file doesn't exist yet. Note that `main.py` does **not**
currently run the FAO-56 script (or the combined-feature-table script) —
both must be run manually before their dashboard pages will show data.

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
- Step 3 prints a pipeline summary and ends with `Pipeline finished
  successfully.`
- Step 5 ends with all tests showing `PASSED` and a line like `24 passed
  in 1.22s`.
- Step 6 produces no output (silence means no syntax errors).
- `logs/pipeline.log` contains a fresh `STARTING` / `SUCCEEDED` line for
  each pipeline step you just ran.

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
on the dashboard's **Combined Intelligence** page (see below), but the
script itself is still standalone: not wired into `main.py` yet — this is
prep work for FAO-56 modeling and (much later) ML.

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
separate runoff/deep-percolation accounting — the script itself is still
standalone, **not wired into `main.py` yet**.

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

### 7.13 What's configured so far

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
  future one) plus a freshness flag. The script itself is standalone — not
  wired into `main.py` yet — but its output CSV is shown on the dashboard's
  **Combined Intelligence** page (step 7.10), the first page that interprets
  weather risk, soil conditions, and vegetation health together. This is
  still prep work for FAO-56 modeling and (much later) ML.
- `src/water_balance/fao56_water_balance.py` (step 7.11) — computes a daily
  FAO-56 Penman-Monteith soil-water balance (ET0, ETc, TAW, RAW, root-zone
  depletion, Ks water-stress coefficient) from the combined feature table,
  writing `data/processed/muthukur_fao56_water_balance.csv`. Shown on the
  dashboard's **Water Balance** page (step 7.12) — the first
  physics-informed water-stress view in the project. Standalone — **not
  wired into `main.py` yet**. Known limitations of this prototype: a
  constant crop coefficient (Kc = 0.75, not phenology-aware), rainfed-only
  depletion (no modeled irrigation events), no runoff/deep-percolation
  accounting, and no field validation.
