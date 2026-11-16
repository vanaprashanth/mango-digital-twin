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
