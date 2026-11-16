# Optional GCS snapshot loader (development only)

Status: foundation only. The dashboard does **not** use it. Local files via
`config.path()` remain the default everywhere, including Streamlit Community Cloud.

Code: `src/cloud/snapshot_loader.py` (reuses `src/cloud/publish.py` schemas).
Tests: `tests/test_cloud_snapshot_loader.py`.

## Selecting a source

| `MANGOTWIN_DATA_SOURCE` | Behaviour |
|---|---|
| unset / `local` | Unchanged local files. Nothing is created or contacted. |
| `gcs_snapshot` | Refresh from `pipeline-runs/latest.json`; else last verified snapshot; else local files. |
| anything else | Error (never guessed). |

Other variables: `MANGOTWIN_GCS_BUCKET`, `MANGOTWIN_SNAPSHOT_DIR`
(default `~/.cache/mangotwin/snapshots`).

Future dashboard wiring (not done here, needs review): replace
`config = get_config()` with `source = select_data_source(get_config()); config = source.config`,
show `source.provenance` / `source.warnings`, and cache the call with a short TTL.

## Verification chain

1. `latest.json` -> consumes `schema_version, run_id, manifest_object, manifest_sha256`.
2. `manifest.json` bytes must hash to `manifest_sha256`; then `publish.validate_manifest`.
3. Consumed manifest fields: `schema_version, run_id, run_prefix, executed_at, pipeline_status,
   input_observation_dates, inputs{object,generation,sha256,latest_date}, irrigation_events,
   satellite_data{status,latest_observation_date}, scientific_validation{status,field_validated},
   outputs[]{key,path,object,bytes,sha256}`.
4. Each output: manifest `path` must equal the path derived from `config.path(key)`; object must be
   under the run prefix; downloaded size and SHA-256 must match.

## Activation

Download to `staging/<run-id>-<token>/`, write `SNAPSHOT.json`, re-verify the whole directory,
`os.replace` it to `runs/<run-id>/`, then atomically replace `ACTIVE.json`. Readers follow only
`ACTIVE.json`. Any failure deletes staging and leaves the previous snapshot active.

## What integrity does and does not mean

SHA-256 matching shows the files are what the pipeline published. It is not field validation or
evidence of scientific accuracy; irrigation labels remain surrogate.

## Limitations

- Not in a snapshot: SoilGrids, irrigation events (GitHub-backed), ML model binaries, ML metrics and
  other unpublished ML artifacts. They stay on their existing sources; their versions are compared
  with the run's recorded inputs and reported in `external_dependencies`, never merged.
- The published irrigation-events copy in GCS may be stale versus GitHub.
- Two processes sharing one cache directory can race on `ACTIVE.json` (last writer wins; both
  writers only ever point at fully verified runs). Use one cache dir per process for strictness.
- Needs `google-cloud-storage` and ADC; `requirements.txt` is intentionally unchanged.

## Network behaviour (timeouts, retries, sessions)

- Every request has an explicit `(connect, read)` timeout (default 10 s / 30 s) and the library's own
  retry is disabled (`retry=None`), so the loader's bounded policy is the only one in force.
- Transient failures only (timeouts, connection resets, HTTP 408/429/5xx, `RetryError`) are retried:
  4 attempts per request, 1 s / 2 s / 4 s backoff, 600 s overall deadline.
  Auth errors, HTTP 4xx, generation mismatches, checksum/size mismatches, invalid manifests and
  missing objects fail immediately.
- Each request uses a fresh `storage.Client` (new HTTP session) built from the same ADC and closed
  afterwards with the public `Client.close()`. Rationale: reusing one client produced stalls of 75-120 s
  in diagnostics while fresh clients took under a second. The root cause is not proven; this is
  a mitigation using supported APIs only.
- Downloads go to `<file>.part`, are pinned with `if_generation_match` to the generation seen in the
  object's metadata (and to a manifest `generation` if one is ever published), and are renamed into place
  only after size and SHA-256 match.
- Tuning: `MANGOTWIN_SNAPSHOT_DOWNLOAD_ATTEMPTS` (1-10), `..._CONNECT_TIMEOUT_SECONDS`,
  `..._READ_TIMEOUT_SECONDS`, `..._DEADLINE_SECONDS`, `MANGOTWIN_SNAPSHOT_FRESH_CLIENT` (true/false).

## Dashboard integration (optional; local files remain the default)

`app/streamlit_app.py` resolves its data source once per script run, before any dataset path is built:
`data_source = resolve_dashboard_source(); config = data_source.config`. Nothing else in the page code changed.

| Setting | Effect |
|---|---|
| `MANGOTWIN_DATA_SOURCE` unset / `local` | Unchanged local files. No GCS import, no network, no cache directory. **Streamlit Community Cloud stays here.** |
| `MANGOTWIN_DATA_SOURCE=gcs_snapshot` | One verified run for all published outputs; refresh at most every `MANGOTWIN_SNAPSHOT_REFRESH_SECONDS` (default 300, range 60-86400; 60 s after a failed refresh). |

- **Sources:** published outputs (21 files) come from the active snapshot; SoilGrids, irrigation events (GitHub-backed),
  ML model/metrics/feature importance/training dataset and everything unpublished keep their existing local paths.
- **Fallback order:** fresh verified snapshot -> previously verified snapshot (with a warning) -> local files (with a warning).
  Invalid settings or missing credentials produce a visible warning, never a crash.
- **Caching:** every `st.cache_data` loader is keyed by file path, and snapshot paths contain the run id
  (`runs/<run-id>/data/...`), so a new run cannot be served DataFrames cached for an older run; old entries
  stay valid for sessions still on the old run. The refresh decision is process-wide (shared by sessions).
- **Display:** sidebar panel with run id, execution time, integrity statement, validation status, satellite status and
  observation dates, input versions. Main-area warnings for fallback, stale snapshot, and local irrigation events / SoilGrids
  that differ from the versions the run used. Integrity is described as checksum verification, never as field validation.
- **Not done:** no change to `requirements.txt`, Streamlit deployment settings, Cloud Run, IAM, workflows or irrigation persistence.
