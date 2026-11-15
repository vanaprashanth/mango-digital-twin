"""
Cloud Run Job entry point for the Mango Digital Twin data refresh.

    python -m src.cloud.run_pipeline_job                # DRY RUN (the default)
    python -m src.cloud.run_pipeline_job --upload       # real run: uploads verified outputs
    python -m src.cloud.run_pipeline_job --print-inventory   # offline: list object paths
    python -m src.cloud.run_pipeline_job --verify-bucket     # read-only bucket check

Environment (all strictly parsed; an unrecognised value is an error, never a
silent default):

    MANGOTWIN_DRY_RUN                  default true.  Uploads happen ONLY when this
                                       is explicitly false (or --upload is passed).
    MANGOTWIN_REFRESH_SENTINEL2        default true.  false = use cached satellite data.
    MANGOTWIN_GCS_BUCKET / _PREFIX     default mango-digital-twin-vsp-data / data
    MANGOTWIN_ALLOW_LOCAL_OVERWRITE    default false. Refuses to overwrite files that
                                       already exist under data/ (protects a developer
                                       checkout, including the manual irrigation events).

What it does (and nothing else):

  1. Snapshots the generation of every object it could later write.
  2. Downloads ONLY the inputs the pipeline needs from gs://<bucket>/<prefix>/
     into the same repo-relative paths the pipeline already uses.
  3. Runs the existing pipeline unchanged: ``python main.py --skip-soil-fetch
     [--refresh-sentinel2]``.
  4. Sanitises + annotates the run-metadata JSON, verifies every output, and
     (only when not a dry run) uploads an explicit allow-list.

Safety properties (each is covered by tests/test_cloud_pipeline_job.py):

  * Path names come from configs/config.yaml ``paths`` keys, never hardcoded.
  * Application Default Credentials only; no key files or secrets are read.
  * A missing required input fails the job before the pipeline starts.
  * The manual irrigation-events CSV is download-only: never on the upload
    allow-list, any upload of its object name is refused, and the job fails if
    its local bytes changed during the run.
  * The ML training dataset, models, ML metrics and experimental artifacts are
    not on the upload allow-list.
  * Nothing is uploaded unless the pipeline exited 0, its metadata reports
    success, and every output passes verification (existence, non-empty, CSV
    header equal to the object already in the bucket, no unexpected shrinkage).
  * Uploads use the generation observed BEFORE the run as a precondition, so
    anything written by someone else meanwhile is never overwritten.
  * Dry-run uses a read-only bucket wrapper: any write attempt raises.
  * Satellite data is labelled CACHED vs REFRESHED in the log and metadata.
  * The metadata uploaded has local paths removed and is scanned for secrets.
  * Exit status is non-zero on any failure.

Scientific calculations, the ML classifier and the daily GitHub Actions
workflow are untouched.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_config  # noqa: E402

log = logging.getLogger("mangotwin.cloud_job")

DEFAULT_BUCKET = "mango-digital-twin-vsp-data"
DEFAULT_PREFIX = "data"

# --- Inputs ---------------------------------------------------------------
# Required: the job fails (before running anything) if any is absent.
REQUIRED_INPUT_KEYS = (
    "soilgrids_csv",              # cached static soil data (--skip-soil-fetch needs it)
    "irrigation_events_csv",      # manual events; read by the water-balance steps
    "sentinel2_timeseries_csv",   # cached Sentinel-2 series; feature table needs its aggregation
)
# Optional: downloaded if present; the pipeline tolerates their absence.
OPTIONAL_INPUT_KEYS = (
    "sentinel1_sar_timeseries_csv",
    "open_meteo_csv",
    "nasa_power_csv",
)
SATELLITE_KEYS = ("sentinel2_timeseries_csv", "sentinel1_sar_timeseries_csv")

# --- Outputs --------------------------------------------------------------
# The ONLY keys that can ever be uploaded (initial rollout).
# Deliberately absent: ml_training_dataset_csv / _metadata_json, the model,
# ML metrics, backtests, audits and failure-analysis files.
UPLOAD_KEYS = (
    "nasa_power_csv",
    "open_meteo_csv",
    "historical_risk_csv",
    "forecast_risk_csv",
    "sentinel2_timeseries_csv",
    "sentinel2_daily_csv",
    "sentinel1_sar_timeseries_csv",
    "sentinel1_daily_csv",
    "combined_feature_table_csv",
    "mango_phenology_calendar_csv",
    "fao56_water_balance_csv",
    "fao56_phenology_water_balance_csv",
    "fao56_interpolated_kc_water_balance_csv",
    "fao56_model_comparison_csv",
    "fao56_model_comparison_summary_md",
    "fao56_sensitivity_analysis_csv",
    "fao56_sensitivity_summary_md",
    "forecast_aware_irrigation_advisory_csv",
    "et0_comparison_csv",
    "et0_comparison_summary_md",
    "pipeline_run_metadata_json",   # uploaded LAST, after sanitising
)
METADATA_KEY = "pipeline_run_metadata_json"
# Never uploaded, whatever else changes.
PROTECTED_KEYS = ("irrigation_events_csv",)
# Explicitly excluded from the initial rollout (documented + tested).
EXCLUDED_ML_KEYS = (
    "ml_training_dataset_csv",
    "ml_training_dataset_metadata_json",
    "irrigation_priority_model_path",
    "ml_model_metrics_json",
    "ml_feature_importance_csv",
)
# Outputs the job must produce for the run to count as verified.
MUST_EXIST_KEYS = (
    "historical_risk_csv",
    "forecast_risk_csv",
    "combined_feature_table_csv",
    "fao56_interpolated_kc_water_balance_csv",
    "forecast_aware_irrigation_advisory_csv",
    METADATA_KEY,
)
FORBIDDEN_SUFFIXES = (".joblib", ".pkl", ".pickle", ".pt", ".h5", ".onnx")
MAX_ROW_SHRINK = 0.10  # a refreshed time series must not shrink by more than this

# Libraries whose versions are recorded in the execution metadata.
RECORDED_LIBRARIES = (
    "pandas", "numpy", "scikit-learn", "requests", "PyYAML",
    "earthengine-api", "google-cloud-storage",
)

TRUE_VALUES = ("1", "true", "yes", "on")
FALSE_VALUES = ("0", "false", "no", "off")


class JobError(RuntimeError):
    """A clear, user-facing failure. Mapped to a non-zero exit status."""


@dataclass
class JobSettings:
    bucket: str = DEFAULT_BUCKET
    prefix: str = DEFAULT_PREFIX
    refresh_sentinel2: bool = True
    dry_run: bool = True
    allow_schema_change: bool = False
    allow_local_overwrite: bool = False
    project_root: Path = PROJECT_ROOT


@dataclass
class FileMap:
    key: str
    local: Path
    object_name: str


class ReadOnlyBucket:
    """Wraps a bucket so that dry runs cannot write: .blob() always raises."""

    def __init__(self, bucket):
        self._bucket = bucket

    def get_blob(self, name):
        return self._bucket.get_blob(name)

    def blob(self, name):
        raise JobError(f"Dry run is read-only; refusing to open {name!r} for writing.")


def build_file_map(keys, config=None, settings: Optional[JobSettings] = None) -> list[FileMap]:
    """Map config path keys to (local path, GCS object name).

    object name = <prefix>/<path relative to data/>, so data/raw/x.csv maps to
    data/raw/x.csv under the default prefix 'data'.
    """
    config = config or get_config()
    settings = settings or JobSettings()
    root = (settings.project_root / "data").resolve()
    prefix = settings.prefix.strip("/")
    out = []
    for key in keys:
        local = Path(config.path(key))
        try:
            rel = local.resolve().relative_to(root)
        except ValueError as exc:
            raise JobError(f"Config path '{key}' ({local}) is not under {root}; refusing to map it.") from exc
        parts = ([prefix] if prefix else []) + list(rel.parts)
        out.append(FileMap(key, local, "/".join(parts)))
    return out


# --- Small file helpers -----------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_header(data: bytes) -> list[str]:
    lines = data.decode("utf-8-sig", errors="replace").splitlines()
    return next(csv.reader([lines[0]]), []) if lines else []


def local_csv_header(path: Path) -> list[str]:
    with open(path, "rb") as f:
        return csv_header(f.read(65536))


def count_rows(path: Path) -> int:
    with open(path, "rb") as f:
        n = sum(1 for _ in f)
    return max(n - 1, 0)


def latest_date(path: Path, column: str = "date") -> Optional[str]:
    """Max ISO date string in `column` of a CSV, or None."""
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            values = [r[column][:10] for r in csv.DictReader(f) if r.get(column)]
    except (OSError, KeyError, UnicodeDecodeError):
        return None
    return max(values) if values else None


def snapshot_file(path: Path) -> dict[str, Any]:
    entry: dict[str, Any] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    if path.suffix == ".csv":
        entry["header"] = local_csv_header(path)
        entry["rows"] = count_rows(path)
        entry["latest_date"] = latest_date(path)
    return entry


# --- Generation snapshot ------------------------------------------------------

def snapshot_generations(bucket, settings: JobSettings, config=None) -> dict[str, int]:
    """Generation of every object the job could write (0 = does not exist).

    Taken BEFORE downloading, so a write by anyone else at any later point
    makes the corresponding upload fail its precondition.
    """
    out: dict[str, int] = {}
    for fm in build_file_map(UPLOAD_KEYS, config, settings):
        blob = bucket.get_blob(fm.object_name)
        out[fm.object_name] = int(blob.generation) if blob is not None else 0
    return out


# --- Download ---------------------------------------------------------------

def download_inputs(bucket, settings: JobSettings, config=None) -> dict[str, dict[str, Any]]:
    """Download required + optional inputs. Returns per-key snapshot info.

    Fails with one clear message listing every missing required object, and
    refuses to overwrite pre-existing local files, before writing anything.
    """
    required = build_file_map(REQUIRED_INPUT_KEYS, config, settings)
    optional = build_file_map(OPTIONAL_INPUT_KEYS, config, settings)

    blobs: dict[str, Any] = {}
    missing = []
    for fm in required:
        blob = bucket.get_blob(fm.object_name)
        if blob is None:
            missing.append(f"gs://{settings.bucket}/{fm.object_name}  (config key: {fm.key})")
        else:
            blobs[fm.key] = blob
    if missing:
        raise JobError(
            "Required input(s) missing from Cloud Storage; nothing was run:\n  " + "\n  ".join(missing)
        )
    for fm in optional:
        blob = bucket.get_blob(fm.object_name)
        if blob is not None:
            blobs[fm.key] = blob
        else:
            log.warning("Optional input not in bucket (continuing): gs://%s/%s", settings.bucket, fm.object_name)

    existing = [str(fm.local) for fm in required + optional if fm.key in blobs and fm.local.exists()]
    if existing and not settings.allow_local_overwrite:
        raise JobError(
            "Refusing to overwrite existing local file(s); this job is meant to run in a fresh "
            "container. Set MANGOTWIN_ALLOW_LOCAL_OVERWRITE=true only if you really intend it:\n  "
            + "\n  ".join(existing)
        )

    info: dict[str, dict[str, Any]] = {}
    for fm in required + optional:
        blob = blobs.get(fm.key)
        if blob is None:
            continue
        fm.local.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(fm.local))
        if not fm.local.exists() or fm.local.stat().st_size == 0:
            raise JobError(f"Downloaded input is empty: {fm.object_name}")
        entry = snapshot_file(fm.local)
        entry["object"] = fm.object_name
        info[fm.key] = entry
        log.info("Downloaded gs://%s/%s -> %s (%d bytes)", settings.bucket, fm.object_name, fm.local, entry["bytes"])
    return info


# --- Pipeline ---------------------------------------------------------------

def pipeline_command(settings: JobSettings) -> list[str]:
    cmd = [sys.executable, "main.py", "--skip-soil-fetch"]
    if settings.refresh_sentinel2:
        cmd.append("--refresh-sentinel2")
    return cmd


def run_pipeline(settings: JobSettings) -> int:
    cmd = pipeline_command(settings)
    log.info("Running pipeline: %s", " ".join(cmd))
    return subprocess.run(cmd, cwd=str(settings.project_root)).returncode


# --- Satellite labelling ------------------------------------------------------

SATELLITE_NAMES = {"sentinel2_timeseries_csv": "sentinel2", "sentinel1_sar_timeseries_csv": "sentinel1"}


def satellite_report(settings: JobSettings, inputs: dict[str, dict[str, Any]], config=None) -> dict[str, Any]:
    """Label each satellite series CACHED / REFRESHED / UNCHANGED_AFTER_REFRESH_ATTEMPT.

    CACHED means the series is exactly the object downloaded from the bucket;
    it was NOT refreshed from Earth Engine in this run.
    """
    report: dict[str, Any] = {}
    for fm in build_file_map(SATELLITE_KEYS, config, settings):
        name = SATELLITE_NAMES[fm.key]
        before = inputs.get(fm.key)
        if before is None or not fm.local.exists():
            report[name] = {"status": "not_available"}
            continue
        after = snapshot_file(fm.local)
        changed = after["sha256"] != before["sha256"]
        if not settings.refresh_sentinel2:
            if changed:
                raise JobError(
                    f"{fm.local.name} changed although Sentinel refresh was disabled; refusing to continue."
                )
            status = "cached"
        else:
            status = "refreshed" if changed else "unchanged_after_refresh_attempt_using_cached_data"
        report[name] = {
            "status": status,
            "rows": after["rows"],
            "latest_observation_date": after["latest_date"],
            "rows_before": before["rows"],
            "latest_observation_date_before": before["latest_date"],
        }
    return report


def describe_satellite_report(report: dict[str, Any]) -> str:
    parts = []
    for name, r in sorted(report.items()):
        status = r["status"]
        label = "CACHED (not refreshed)" if status == "cached" else status.upper().replace("_", " ")
        parts.append(f"{name}: {label}, latest observation {r.get('latest_observation_date')}")
    return "SATELLITE DATA - " + "; ".join(parts) if parts else "SATELLITE DATA - none"


# --- Run-metadata sanitising --------------------------------------------------

SECRET_PATTERNS = (
    r"BEGIN [A-Z ]*PRIVATE KEY", r"private_key(_id)?\W{0,4}[:=]", r"client_email\W{0,4}[:=]",
    r"ya29\.[0-9A-Za-z_-]{10,}", r"AIza[0-9A-Za-z_-]{20,}", r"gh[pousr]_[0-9A-Za-z]{20,}",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", r"(?i)\b(secret|password|token|api[_-]?key)\b\s*[:=]",
)
LOCAL_PATH_PATTERNS = (
    r"[A-Za-z]:[\\/]", r"(?<![\w.])/(?:app|home|Users|root|tmp|mnt|var|workspace)/",
)


def library_versions() -> dict[str, Optional[str]]:
    out: dict[str, Optional[str]] = {}
    for name in RECORDED_LIBRARIES:
        try:
            out[name] = importlib_metadata.version(name)
        except importlib_metadata.PackageNotFoundError:
            out[name] = None  # recorded as "not installed"
    return out


def environment_info() -> dict[str, Any]:
    v = sys.version_info
    return {"python": f"{v.major}.{v.minor}.{v.micro}", "libraries": library_versions()}


def _scrub_paths(value: Any, project_root: Path) -> Any:
    if isinstance(value, dict):
        return {k: _scrub_paths(v, project_root) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub_paths(v, project_root) for v in value]
    if isinstance(value, str):
        text = value
        for root in {str(project_root), str(project_root.resolve()), project_root.as_posix()}:
            for sep_root in (root, root.replace("\\", "/")):
                text = text.replace(sep_root + os.sep, "").replace(sep_root + "/", "").replace(sep_root, ".")
        return text.replace("\\", "/") if re.match(r"^(data|\.)[\\/]", text) else text
    return value


def scan_for_sensitive(text: str) -> list[str]:
    hits = []
    for pat in SECRET_PATTERNS:
        if re.search(pat, text):
            hits.append(f"secret-like pattern /{pat}/")
    for pat in LOCAL_PATH_PATTERNS:
        if re.search(pat, text):
            hits.append(f"local path pattern /{pat}/")
    return hits


def finalize_metadata(settings: JobSettings, inputs: dict[str, dict[str, Any]], satellite: dict[str, Any], config=None) -> None:
    """Sanitise the pipeline's run-metadata, add cloud execution info, and scan it.

    Raises JobError if anything secret-like or any local path remains.
    """
    fm = build_file_map([METADATA_KEY], config, settings)[0]
    if not fm.local.exists():
        raise JobError("pipeline_run_metadata.json was not produced")
    try:
        meta = json.loads(fm.local.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise JobError(f"pipeline_run_metadata.json is unreadable: {exc}") from exc
    meta = _scrub_paths(meta, settings.project_root)
    meta["cloud_execution"] = {
        "runner": "cloud-run-job",
        "dry_run": settings.dry_run,
        "sentinel_refresh_requested": settings.refresh_sentinel2,
        "satellite_data": satellite,
        "environment": environment_info(),
    }
    text = json.dumps(meta, indent=2, sort_keys=False)
    hits = scan_for_sensitive(text)
    if hits:
        raise JobError("Run metadata failed the sensitive-content scan; nothing was uploaded: " + "; ".join(hits))
    fm.local.write_text(text + "\n", encoding="utf-8")


# --- Verification -----------------------------------------------------------

def verify_outputs(bucket, settings: JobSettings, inputs: dict[str, dict[str, Any]], config=None) -> list[FileMap]:
    """Return the verified upload list or raise JobError describing every problem."""
    problems: list[str] = []
    to_upload: list[FileMap] = []

    meta_fm = build_file_map([METADATA_KEY], config, settings)[0]
    if not meta_fm.local.exists():
        problems.append("pipeline_run_metadata.json was not produced")
    else:
        try:
            status = json.loads(meta_fm.local.read_text(encoding="utf-8")).get("status")
        except (OSError, ValueError) as exc:
            status = f"unreadable ({exc})"
        if status != "success":
            problems.append(f"pipeline metadata status is {status!r}, expected 'success'")

    for fm in build_file_map(PROTECTED_KEYS, config, settings):
        before = inputs.get(fm.key, {}).get("sha256")
        if before is None or not fm.local.exists() or sha256_file(fm.local) != before:
            problems.append(f"protected file changed or vanished during the run: {fm.local.name}")

    for fm in build_file_map(UPLOAD_KEYS, config, settings):
        if fm.key in PROTECTED_KEYS:
            continue
        if not fm.local.exists():
            if fm.key in MUST_EXIST_KEYS:
                problems.append(f"expected output missing: {fm.local.name}")
            continue
        if fm.local.stat().st_size == 0:
            problems.append(f"output is empty: {fm.local.name}")
            continue
        if fm.local.suffix == ".csv":
            header = local_csv_header(fm.local)
            rows = count_rows(fm.local)
            if not header or rows == 0:
                problems.append(f"CSV has no data rows: {fm.local.name}")
                continue
            prev = inputs.get(fm.key)
            if prev and prev.get("rows") and rows < prev["rows"] * (1 - MAX_ROW_SHRINK):
                problems.append(f"{fm.local.name} shrank from {prev['rows']} to {rows} rows")
                continue
            remote_header = prev["header"] if prev else None
            if remote_header is None:
                blob = bucket.get_blob(fm.object_name)
                if blob is not None:
                    remote_header = csv_header(blob.download_as_bytes(start=0, end=65535))
            if remote_header and remote_header != header and not settings.allow_schema_change:
                problems.append(
                    f"schema changed for {fm.local.name}: bucket has {remote_header}, new file has {header}"
                )
                continue
        to_upload.append(fm)

    if problems:
        raise JobError("Output verification failed; nothing was uploaded:\n  " + "\n  ".join(problems))
    return to_upload


# --- Upload -----------------------------------------------------------------

def assert_uploadable(fm: FileMap, settings: JobSettings, config=None) -> None:
    """Last line of defence, independent of the allow-list."""
    protected = {p.object_name for p in build_file_map(PROTECTED_KEYS, config, settings)}
    if fm.object_name in protected or fm.local.name == "muthukur_irrigation_events.csv":
        raise JobError(f"Refusing to upload protected file: {fm.object_name}")
    if fm.local.suffix.lower() in FORBIDDEN_SUFFIXES or "models/" in fm.object_name:
        raise JobError(f"Refusing to upload model artifact: {fm.object_name}")
    if fm.key in EXCLUDED_ML_KEYS or fm.key not in UPLOAD_KEYS:
        raise JobError(f"Refusing to upload non-allow-listed file: {fm.object_name}")


def upload_outputs(bucket, files: list[FileMap], settings: JobSettings, config=None,
                   generations: Optional[dict[str, int]] = None) -> list[str]:
    """Upload with if_generation_match = generation seen BEFORE the run.

    `generations` must come from snapshot_generations(); an object missing
    from it is treated as "must not exist yet" (generation 0), which is the
    safest assumption. The metadata file is uploaded last.
    """
    if settings.dry_run:
        raise JobError("upload_outputs called during a dry run; refusing.")
    for fm in files:
        assert_uploadable(fm, settings, config)
    generations = generations or {}
    ordered = sorted(files, key=lambda f: f.key == METADATA_KEY)
    uploaded = []
    for fm in ordered:
        blob = bucket.blob(fm.object_name)
        try:
            blob.upload_from_filename(str(fm.local), if_generation_match=generations.get(fm.object_name, 0))
        except Exception as exc:  # PreconditionFailed or transport errors
            raise JobError(
                f"Upload failed for {fm.object_name}: {type(exc).__name__}: {exc} "
                f"(already uploaded: {len(uploaded)} file(s))"
            ) from exc
        uploaded.append(fm.object_name)
        log.info("Uploaded %s -> gs://%s/%s", fm.local, settings.bucket, fm.object_name)
    return uploaded


# --- Orchestration ----------------------------------------------------------

def run_job(bucket, settings: JobSettings, config=None, runner=run_pipeline) -> dict[str, Any]:
    config = config or get_config()
    if settings.dry_run:
        bucket = ReadOnlyBucket(bucket)
    log.info("MODE: %s | satellite refresh requested: %s",
             "DRY RUN (nothing will be uploaded)" if settings.dry_run else "LIVE UPLOAD",
             settings.refresh_sentinel2)
    generations = snapshot_generations(bucket, settings, config)
    inputs = download_inputs(bucket, settings, config)
    code = runner(settings)
    if code != 0:
        raise JobError(f"Pipeline exited with status {code}; nothing was uploaded.")
    satellite = satellite_report(settings, inputs, config)
    log.info("%s", describe_satellite_report(satellite))
    finalize_metadata(settings, inputs, satellite, config)
    files = verify_outputs(bucket, settings, inputs, config)
    result: dict[str, Any] = {"dry_run": settings.dry_run, "satellite_data": satellite,
                              "uploaded": [], "would_upload": []}
    if settings.dry_run:
        result["would_upload"] = [f.object_name for f in files]
        log.info("Dry run complete: verified %d output(s); nothing uploaded.", len(files))
        for fm in files:
            log.info("  would upload %s -> gs://%s/%s", fm.local.name, settings.bucket, fm.object_name)
        return result
    result["uploaded"] = upload_outputs(bucket, files, settings, config, generations)
    return result


# --- Inventory / read-only bucket check --------------------------------------

def inventory(settings: JobSettings, config=None) -> dict[str, list[str]]:
    def names(keys):
        return [f.object_name for f in build_file_map(keys, config, settings)]
    return {"required": names(REQUIRED_INPUT_KEYS), "optional": names(OPTIONAL_INPUT_KEYS),
            "upload": names(UPLOAD_KEYS)}


def print_inventory(settings: JobSettings, config=None) -> None:
    inv = inventory(settings, config)
    base = f"gs://{settings.bucket}"
    for title in ("required", "optional", "upload"):
        print(f"\n{title.upper()} ({len(inv[title])}):")
        for n in inv[title]:
            print(f"  {base}/{n}")
    print("\nRead-only verification (no writes):")
    print(f"  gcloud storage ls --long --recursive {base}/{settings.prefix.strip('/')}/")
    print("  python -m src.cloud.run_pipeline_job --verify-bucket")


def verify_bucket(bucket, settings: JobSettings, config=None) -> int:
    """Read-only: report which declared objects exist. Never downloads or writes."""
    bucket = ReadOnlyBucket(bucket)
    inv = inventory(settings, config)
    missing_required = 0
    for title in ("required", "optional", "upload"):
        print(f"\n{title.upper()}:")
        for n in inv[title]:
            blob = bucket.get_blob(n)
            state = f"present ({blob.size} bytes, generation {blob.generation})" if blob else "MISSING"
            print(f"  {state:45s} {n}")
            if blob is None and title == "required":
                missing_required += 1
    return 1 if missing_required else 0


# --- CLI ----------------------------------------------------------------------

def parse_bool_env(name: str, default: bool, environ=None) -> bool:
    raw = (environ if environ is not None else os.environ).get(name)
    if raw is None or raw.strip() == "":
        return default
    value = raw.strip().lower()
    if value in TRUE_VALUES:
        return True
    if value in FALSE_VALUES:
        return False
    raise JobError(
        f"{name}={raw!r} is not a recognised boolean; use one of "
        f"{', '.join(TRUE_VALUES + FALSE_VALUES)}. Refusing to guess."
    )


def parse_args(argv=None, environ=None) -> tuple[JobSettings, argparse.Namespace]:
    env = environ if environ is not None else os.environ
    p = argparse.ArgumentParser(description="Mango Digital Twin pipeline for Cloud Run Jobs.")
    p.add_argument("--bucket", default=env.get("MANGOTWIN_GCS_BUCKET", DEFAULT_BUCKET))
    p.add_argument("--prefix", default=env.get("MANGOTWIN_GCS_PREFIX", DEFAULT_PREFIX))
    p.add_argument("--no-sentinel", action="store_true",
                   help="Use cached satellite data (same as MANGOTWIN_REFRESH_SENTINEL2=false).")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Download, run, verify; upload nothing (default).")
    mode.add_argument("--upload", action="store_true", help="Upload verified outputs (overrides MANGOTWIN_DRY_RUN).")
    p.add_argument("--allow-schema-change", action="store_true",
                   help="Permit CSV headers that differ from the objects already in the bucket.")
    p.add_argument("--print-inventory", action="store_true", help="Print declared object paths and exit (offline).")
    p.add_argument("--verify-bucket", action="store_true", help="Read-only check that declared objects exist, then exit.")
    a = p.parse_args(argv)

    env_dry = parse_bool_env("MANGOTWIN_DRY_RUN", True, env)
    env_refresh = parse_bool_env("MANGOTWIN_REFRESH_SENTINEL2", True, env)
    allow_local = parse_bool_env("MANGOTWIN_ALLOW_LOCAL_OVERWRITE", False, env)
    dry_run = True if a.dry_run else (False if a.upload else env_dry)
    settings = JobSettings(
        bucket=a.bucket, prefix=a.prefix,
        refresh_sentinel2=False if a.no_sentinel else env_refresh,
        dry_run=dry_run, allow_schema_change=a.allow_schema_change, allow_local_overwrite=allow_local,
    )
    return settings, a


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    try:
        settings, args = parse_args(argv)
        if args.print_inventory:
            print_inventory(settings)
            return 0
        from google.cloud import storage  # Application Default Credentials
        bucket = storage.Client().bucket(settings.bucket)
        if args.verify_bucket:
            return verify_bucket(bucket, settings)
        result = run_job(bucket, settings)
    except JobError as exc:
        log.error("%s", exc)
        return 1
    except Exception as exc:  # any unexpected failure must still fail the job
        log.exception("Unexpected failure: %s", exc)
        return 1
    log.info("Job complete: %s", json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
