"""
Optional, read-only loader for versioned GCS pipeline snapshots (development use).

NOTHING imports this module by default: the dashboard keeps reading local files
through ``config.path()`` unless a caller explicitly asks for a snapshot data
source (``MANGOTWIN_DATA_SOURCE=gcs_snapshot``). Production (Streamlit Community
Cloud) stays in local mode.

Flow (see docs/gcs_snapshot_loader.md):

  latest.json --sha256--> manifest.json --size+sha256--> every output object
        resolve            verify against pointer            download to STAGING,
                                                             verify, then activate

  * Read-only: only ``get_blob`` + downloads are ever called on the bucket.
  * Application Default Credentials with the read-only storage scope. No key
    files are read, created or requested.
  * A snapshot is ONE published run. Eligible scientific outputs are all served
    from that run or (in local mode) all from local files; there is no per-file
    fallback, so runs are never mixed.
  * Downloads land in a run-specific staging directory. Only after every
    file's size and SHA-256 match the manifest is the directory renamed into
    place and ``ACTIVE.json`` atomically switched. A failure at any point
    leaves the previously verified snapshot untouched.
  * SHA-256 verification proves the files are the ones the pipeline published.
    It says nothing about field validation or scientific accuracy; labels
    remain surrogate.

Not in a snapshot (stay on their existing sources): SoilGrids, the manual
irrigation events (GitHub-backed), ML model binaries and unpublished ML artifacts.
Their versions are compared with the manifest and reported, never merged.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import logging
import os
import shutil
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from src.cloud import publish
from src.cloud.run_pipeline_job import METADATA_KEY, MUST_EXIST_KEYS, UPLOAD_KEYS
from src.utils.config import PROJECT_ROOT

log = logging.getLogger("mangotwin.snapshot")

DEFAULT_BUCKET = "mango-digital-twin-vsp-data"
READ_ONLY_SCOPE = "https://www.googleapis.com/auth/devstorage.read_only"
ACTIVE_FILE = "ACTIVE.json"
PROVENANCE_FILE = "SNAPSHOT.json"
MODES = ("local", "gcs_snapshot")
# Inputs that live outside a snapshot; their versions are compared and reported.
EXTERNAL_DEPENDENCY_KEYS = ("soilgrids_csv", "irrigation_events_csv")
INTEGRITY_NOTE = (
    "SHA-256 verification shows these files are exactly what the pipeline published. It is NOT field "
    "validation or evidence of scientific accuracy; irrigation labels are surrogate."
)
STAGING_MAX_AGE_SECONDS = 3600

_refresh_lock = threading.Lock()


class SnapshotError(RuntimeError):
    """A snapshot could not be resolved, verified or activated."""


@dataclass
class SnapshotSettings:
    bucket: str = DEFAULT_BUCKET
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".cache" / "mangotwin" / "snapshots")
    runs_prefix: str = publish.RUNS_PREFIX
    keep: int = 3                      # verified runs kept on disk (active one is never pruned)
    allow_downgrade: bool = False      # moving to an OLDER run than the active one needs this
    project_root: Path = PROJECT_ROOT
    # --- network behaviour (all bounded) ---
    download_attempts: int = 4                        # per object / per read, transient failures only
    connect_timeout: float = 10.0                     # seconds, per request
    read_timeout: float = 30.0                        # seconds, per request
    retry_backoff_seconds: float = 1.0                # doubles each retry
    overall_deadline_seconds: float = 600.0           # whole refresh gives up after this
    fresh_client_per_request: bool = True             # new client + HTTP session per request, closed after
    sleep: Callable[[float], None] = field(default=time.sleep, repr=False)
    clock: Callable[[], float] = field(default=time.monotonic, repr=False)

    @property
    def request_timeout(self) -> tuple[float, float]:
        return (self.connect_timeout, self.read_timeout)


@dataclass(frozen=True)
class PlannedFile:
    key: str
    object: str
    rel_path: str      # repo-relative, e.g. data/processed/x.csv (from config, not from the manifest)
    size: int
    sha256: str
    generation: Optional[int] = None   # only if the manifest declares one (current publisher does not)


# --- read-only bucket access --------------------------------------------------

def call_supported(fn, *args, **kwargs):
    """Call ``fn`` passing only the keyword arguments its signature accepts.

    Real google-cloud-storage methods accept ``timeout``/``retry``/``if_generation_match``;
    simple mocked clients that predate them keep working unchanged.
    """
    try:
        params = inspect.signature(fn).parameters.values()
    except (TypeError, ValueError):
        return fn(*args, **kwargs)
    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params):
        return fn(*args, **kwargs)
    names = {p.name for p in params}
    return fn(*args, **{k: v for k, v in kwargs.items() if k in names})


class _ReadOnlyBlob:
    """Exposes only what verification needs; no upload/delete/patch methods."""

    def __init__(self, blob):
        self._blob = blob

    generation = property(lambda self: self._blob.generation)
    size = property(lambda self: self._blob.size)

    def download_as_bytes(self, **kwargs):
        return call_supported(self._blob.download_as_bytes, **kwargs)

    def download_to_filename(self, path, **kwargs):
        return call_supported(self._blob.download_to_filename, path, **kwargs)


class ReadOnlyBucket:
    """Read-only view of a bucket.

    ``factory`` (optional) returns a new ``(bucket, client)`` pair; ``fresh()`` uses it so
    callers can give each request its own client and HTTP session, and ``close()`` releases
    them through the client's public ``close()``. Without a factory both are no-ops.
    """

    def __init__(self, bucket, client=None, factory: Optional[Callable[[], tuple[Any, Any]]] = None):
        self._bucket, self._client, self._factory = bucket, client, factory

    def get_blob(self, name, **kwargs):
        blob = call_supported(self._bucket.get_blob, name, **kwargs)
        return None if blob is None else _ReadOnlyBlob(blob)

    def fresh(self) -> "ReadOnlyBucket":
        if self._factory is None:
            return self
        bucket, client = self._factory()
        return ReadOnlyBucket(bucket, client, self._factory)

    def close(self) -> None:
        close = getattr(self._client, "close", None)
        if callable(close):
            close()


def open_readonly_bucket(bucket_name: str = DEFAULT_BUCKET, project: Optional[str] = None):
    """Application Default Credentials, read-only scope. Never loads a key file here.

    Locally, run ``gcloud auth application-default login`` once. Raises
    SnapshotError if no ADC are available (callers then fall back to local mode).
    Credentials are resolved once; each ``fresh()`` bucket gets a new ``storage.Client``
    (new HTTP session) that uses them and is closed with ``close()``.
    """
    try:
        import google.auth
        from google.cloud import storage
    except ImportError as exc:
        raise SnapshotError("google-cloud-storage is not installed; GCS snapshot mode is unavailable.") from exc
    try:
        credentials, default_project = google.auth.default(scopes=[READ_ONLY_SCOPE])
    except Exception as exc:  # noqa: BLE001 - google.auth.exceptions.DefaultCredentialsError et al.
        raise SnapshotError(f"No Application Default Credentials available ({type(exc).__name__}). "
                            "Run 'gcloud auth application-default login' for local development.") from exc

    def make() -> tuple[Any, Any]:
        client = storage.Client(credentials=credentials, project=project or default_project)
        return client.bucket(bucket_name), client

    bucket, client = make()
    return ReadOnlyBucket(bucket, client, make)


@contextmanager
def _session(bucket, settings: "SnapshotSettings"):
    """A bucket for ONE request: fresh client/session when supported, closed afterwards."""
    fresh = getattr(bucket, "fresh", None) if settings.fresh_client_per_request else None
    session = fresh() if callable(fresh) else bucket
    try:
        yield session
    finally:
        if session is not bucket:
            try:
                session.close()
            except Exception as exc:  # noqa: BLE001 - closing must never mask the real result
                log.debug("Ignoring error while closing a storage client: %s", exc)


# --- transient-failure classification and bounded retry ------------------------------

_TRANSIENT_NAMES = frozenset({
    "RetryError", "DeadlineExceeded", "ServiceUnavailable", "InternalServerError", "BadGateway", "GatewayTimeout",
    "TooManyRequests", "ServerError", "ReadTimeout", "ConnectTimeout", "Timeout", "ConnectionError",
    "ChunkedEncodingError", "ProtocolError", "IncompleteRead", "ReadTimeoutError", "ConnectTimeoutError",
    "TransportError", "ConnectionResetError", "ConnectionAbortedError", "BrokenPipeError",
})
_AUTH_NAMES = frozenset({"Unauthenticated", "Forbidden", "RefreshError", "DefaultCredentialsError", "PermissionDenied"})


def classify_download_error(exc: BaseException) -> str:
    """'transient' (retry), 'auth', 'replaced' (generation precondition) or 'permanent'.

    Only network-level and HTTP 408/429/5xx failures are transient. Everything unknown is
    permanent: fail closed rather than retry something we do not understand.
    """
    if isinstance(exc, SnapshotError):
        return "permanent"
    names = {c.__name__ for c in type(exc).__mro__}
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        if code == 412:
            return "replaced"
        if code in (401, 403):
            return "auth"
        if code in (408, 429) or code >= 500:
            return "transient"
        return "permanent"
    if names & _AUTH_NAMES:
        return "auth"
    if names & _TRANSIENT_NAMES or isinstance(exc, (TimeoutError, ConnectionError)):
        return "transient"
    return "permanent"      # includes DataCorruption (checksum mismatch), disk errors, bugs


def _retry(fn: Callable[[], Any], label: str, settings: "SnapshotSettings", started: Optional[float] = None) -> Any:
    """Run ``fn`` with bounded retries of transient failures only.

    SnapshotError and non-transient errors propagate immediately (wrapped with context).
    """
    started = settings.clock() if started is None else started
    attempts = max(int(settings.download_attempts), 1)
    last: Optional[BaseException] = None
    for i in range(attempts):
        try:
            return fn()
        except SnapshotError:
            raise
        except Exception as exc:  # noqa: BLE001 - classified below
            kind = classify_download_error(exc)
            if kind != "transient":
                hint = {"auth": " Check Application Default Credentials / bucket read access.",
                        "replaced": " The object was replaced after its metadata was read (generation precondition failed)."}.get(kind, "")
                raise SnapshotError(f"{label} (not retried, {kind}): {type(exc).__name__}: {exc}.{hint}") from exc
            last = exc
            if i == attempts - 1:
                break
            delay = settings.retry_backoff_seconds * (2 ** i)
            if settings.clock() - started + delay > settings.overall_deadline_seconds:
                raise SnapshotError(f"{label}: overall deadline of {settings.overall_deadline_seconds:.0f}s exceeded "
                                    f"after {i + 1} attempt(s): {type(exc).__name__}: {exc}") from exc
            log.warning("%s: transient %s (attempt %d/%d); retrying in %.1fs", label, type(exc).__name__, i + 1, attempts, delay)
            settings.sleep(delay)
    raise SnapshotError(f"{label} after {attempts} attempt(s) [transient]: {type(last).__name__}: {last}") from last


# --- helpers ------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read(bucket, name: str, settings: Optional["SnapshotSettings"] = None) -> bytes:
    settings = settings or SnapshotSettings()

    def once() -> bytes:
        with _session(bucket, settings) as b:
            blob = call_supported(b.get_blob, name, timeout=settings.request_timeout)
            if blob is None:
                raise SnapshotError(f"Object not found in Cloud Storage: {name}")
            return call_supported(blob.download_as_bytes, timeout=settings.request_timeout, retry=None)

    return _retry(once, f"Could not read {name}", settings)


# --- 1. resolve pointer + manifest ------------------------------------------------------

def fetch_verified_manifest(bucket, settings: SnapshotSettings) -> tuple[dict[str, Any], dict[str, Any], bytes]:
    """latest.json -> manifest.json, checking the manifest's SHA-256 against the pointer.

    Returns (pointer, manifest, manifest_bytes). Consumed pointer fields:
    schema_version, run_id, manifest_object, manifest_sha256.
    """
    pointer_bytes = _read(bucket, publish.latest_object(settings.runs_prefix), settings)
    try:
        pointer = publish.parse_pointer(pointer_bytes, settings.runs_prefix)
    except publish.PublishError as exc:
        raise SnapshotError(f"latest.json is unusable: {exc}") from exc

    manifest_bytes = _read(bucket, pointer["manifest_object"], settings)
    actual = sha256_bytes(manifest_bytes)
    if actual != pointer["manifest_sha256"]:
        raise SnapshotError(
            f"Manifest SHA-256 does not match latest.json (pointer {pointer['manifest_sha256']}, "
            f"manifest {actual}); the pointer moved or the manifest is corrupt. Not loading."
        )
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise SnapshotError(f"Manifest is not valid JSON: {exc}") from exc
    try:
        publish.validate_manifest(manifest, settings.runs_prefix, allowed_keys=UPLOAD_KEYS, require_key=METADATA_KEY)
    except publish.PublishError as exc:
        raise SnapshotError(str(exc)) from exc
    if manifest["run_id"] != pointer["run_id"]:
        raise SnapshotError(f"Manifest run_id {manifest['run_id']} differs from pointer run_id {pointer['run_id']}.")
    return pointer, manifest, manifest_bytes


# --- 2. plan: map manifest outputs to local paths using the existing config keys ---------------

def plan_files(manifest: dict[str, Any], config, settings: SnapshotSettings) -> list[PlannedFile]:
    """Map each manifest output to its repo-relative path via ``config.path(key)``.

    No second set of scientific paths exists here: the key is the existing
    ``paths`` key, and the manifest's recorded path must agree with the config.
    """
    root = settings.project_root.resolve()
    prefix = publish.run_prefix(manifest["run_id"], settings.runs_prefix)
    plan: list[PlannedFile] = []
    problems: list[str] = []
    seen_keys: set[str] = set()
    for out in manifest["outputs"]:
        key = out["key"]
        if key not in UPLOAD_KEYS:
            problems.append(f"{key}: not an eligible published output")
            continue
        if key in seen_keys:
            problems.append(f"{key}: listed twice")
            continue
        seen_keys.add(key)
        try:
            rel = Path(config.path(key)).resolve().relative_to(root).as_posix()
        except (KeyError, ValueError):
            problems.append(f"{key}: no usable path in configs/config.yaml")
            continue
        if out.get("path") != rel:
            problems.append(f"{key}: manifest path {out.get('path')!r} differs from config path {rel!r}")
            continue
        if not out["object"].startswith(prefix):
            problems.append(f"{key}: object {out['object']!r} is outside run prefix {prefix}")
            continue
        gen = out.get("generation")
        if gen is not None and (not isinstance(gen, int) or isinstance(gen, bool) or gen <= 0):
            problems.append(f"{key}: manifest generation {gen!r} is not a positive integer")
            continue
        plan.append(PlannedFile(key, out["object"], rel, int(out["bytes"]), out["sha256"], gen))
    missing = [k for k in MUST_EXIST_KEYS if k not in seen_keys]
    if missing:
        problems.append("required output(s) absent from the manifest: " + ", ".join(missing))
    if problems:
        raise SnapshotError("Manifest cannot be mapped onto this configuration: " + "; ".join(problems))
    return plan


# --- 3. stage + verify ------------------------------------------------------------------------

def _download_file(bucket, pf: PlannedFile, target: Path, settings: "SnapshotSettings", started: float) -> None:
    """Download one object to ``target`` with bounded transient retries, pinned to one generation.

    The bytes go to ``<target>.part`` and are renamed into place only after size and
    SHA-256 both match the manifest, so a failed or retried attempt never leaves a
    corrupt file under its final name. Only transient network failures are retried.
    """
    part = target.with_name(target.name + ".part")
    seen_generation: list[Optional[int]] = []

    def once() -> None:
        part.unlink(missing_ok=True)                 # never resume from / keep a partial file
        with _session(bucket, settings) as b:
            blob = call_supported(b.get_blob, pf.object, timeout=settings.request_timeout)
            if blob is None:
                raise SnapshotError(f"Object not found in Cloud Storage: {pf.object}")
            gen = getattr(blob, "generation", None)
            if pf.generation is not None and gen != pf.generation:
                raise SnapshotError(f"Object {pf.object} was replaced: manifest generation {pf.generation}, "
                                    f"bucket has {gen}.")
            if seen_generation and seen_generation[0] != gen:
                raise SnapshotError(f"Object {pf.object} was replaced between download attempts "
                                    f"(generation {seen_generation[0]} -> {gen}).")
            seen_generation[:] = [gen]
            size = getattr(blob, "size", None)
            if isinstance(size, int) and size != pf.size:
                raise SnapshotError(f"Size mismatch for {pf.object}: manifest {pf.size} bytes, object in Cloud "
                                    f"Storage has {size}.")
            kwargs: dict[str, Any] = {"timeout": settings.request_timeout, "retry": None}   # we own the retry policy
            if gen is not None:
                kwargs["if_generation_match"] = gen   # fail (412) rather than fetch a replaced object
            call_supported(blob.download_to_filename, str(part), **kwargs)

    try:
        _retry(once, f"Download failed for {pf.object}", settings, started)
        if not part.is_file():
            raise SnapshotError(f"Download produced no file for {pf.object}")
        size = part.stat().st_size
        if size != pf.size:
            raise SnapshotError(f"Size mismatch for {pf.object}: manifest {pf.size} bytes, downloaded {size} (partial or corrupt).")
        digest = sha256_file(part)
        if digest != pf.sha256:
            raise SnapshotError(f"SHA-256 mismatch for {pf.object}: manifest {pf.sha256}, downloaded {digest}.")
        os.replace(part, target)
    finally:
        part.unlink(missing_ok=True)


def stage_snapshot(bucket, plan: list[PlannedFile], staging_dir: Path,
                   settings: Optional["SnapshotSettings"] = None) -> None:
    """Download every planned file into staging and verify size + SHA-256. Raises on any mismatch."""
    settings = settings or SnapshotSettings()
    started = settings.clock()
    for pf in plan:
        target = staging_dir / pf.rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        _download_file(bucket, pf, target, settings, started)


# --- 4. provenance ------------------------------------------------------------------------------

def external_dependency_report(manifest: dict[str, Any], base_config) -> dict[str, Any]:
    """Compare the local copies of non-snapshot inputs with the versions the run used.

    Reported only; a difference never changes which run is served and is
    never reconciled by mixing files.
    """
    out: dict[str, Any] = {}
    for key in EXTERNAL_DEPENDENCY_KEYS:
        recorded = (manifest.get("inputs") or {}).get(key)
        try:
            local = Path(base_config.path(key))
        except KeyError:
            local = None
        entry: dict[str, Any] = {"source": "local/GitHub (not part of the snapshot)",
                                 "run_input_sha256": recorded.get("sha256") if recorded else None,
                                 "run_input_generation": recorded.get("generation") if recorded else None}
        if recorded is None:
            entry["status"] = "not_recorded_in_manifest"
        elif local is None or not local.is_file():
            entry["status"] = "local_file_missing"
        else:
            entry["local_sha256"] = sha256_file(local)
            entry["status"] = "matches_run_input" if entry["local_sha256"] == recorded.get("sha256") else "differs_from_run_input"
        out[key] = entry
    out["ml_model_and_unpublished_ml_artifacts"] = {
        "source": "local (not part of the snapshot)", "status": "not_versioned_by_snapshot"}
    return out


def build_provenance(pointer, manifest, manifest_sha256: str, plan: list[PlannedFile], base_config,
                     now: Callable[[], datetime] = publish.utc_now) -> dict[str, Any]:
    sat = {name: {"status": s.get("status"), "latest_observation_date": s.get("latest_observation_date")}
           for name, s in (manifest.get("satellite_data") or {}).items() if isinstance(s, dict)}
    sv = manifest["scientific_validation"]
    return {
        "snapshot_schema_version": 1,
        "run_id": manifest["run_id"],
        "executed_at": manifest["executed_at"],
        "pipeline_status": manifest["pipeline_status"],
        "manifest_object": pointer["manifest_object"],
        "manifest_sha256": manifest_sha256,
        "fetched_at": publish.iso(now()),
        "satellite_observation": sat,
        "input_observation_dates": manifest["input_observation_dates"],
        "input_versions": {k: {"object": v.get("object"), "generation": v.get("generation"), "sha256": v.get("sha256")}
                           for k, v in manifest["inputs"].items()},
        "irrigation_events_provenance": manifest.get("irrigation_events"),
        "validation_status": sv.get("status"),
        "field_validated": bool(sv.get("field_validated", False)),
        "integrity_note": INTEGRITY_NOTE,
        "external_dependencies": external_dependency_report(manifest, base_config),
        "files": [{"key": p.key, "path": p.rel_path, "bytes": p.size, "sha256": p.sha256} for p in plan],
    }


# --- 5. local store: staging, atomic activation, active snapshot -------------------------------------

def _runs_dir(s: SnapshotSettings) -> Path:
    return s.cache_dir / "runs"


def _staging_root(s: SnapshotSettings) -> Path:
    return s.cache_dir / "staging"


def _atomic_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)  # atomic on POSIX and Windows


def verify_snapshot_dir(run_dir: Path) -> dict[str, Any]:
    """Re-verify an on-disk snapshot against its own provenance. Returns provenance or raises."""
    prov_path = run_dir / PROVENANCE_FILE
    try:
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        files = prov["files"]
    except (OSError, ValueError, KeyError) as exc:
        raise SnapshotError(f"Snapshot {run_dir.name} has no readable provenance: {exc}") from exc
    for f in files:
        p = run_dir / f["path"]
        if not p.is_file() or p.stat().st_size != f["bytes"] or sha256_file(p) != f["sha256"]:
            raise SnapshotError(f"Snapshot {run_dir.name} failed re-verification at {f['path']}.")
    return prov


def read_active(settings: SnapshotSettings) -> Optional[tuple[Path, dict[str, Any]]]:
    """The active, re-verified snapshot (dir, provenance), or None if there is none.

    Raises SnapshotError if ACTIVE.json exists but the snapshot it names is damaged.
    """
    ptr = settings.cache_dir / ACTIVE_FILE
    if not ptr.is_file():
        return None
    try:
        run_id = publish.check_run_id(json.loads(ptr.read_text(encoding="utf-8"))["run_id"])
    except (OSError, ValueError, KeyError, publish.PublishError) as exc:
        raise SnapshotError(f"{ACTIVE_FILE} is unreadable: {exc}") from exc
    run_dir = _runs_dir(settings) / run_id
    return run_dir, verify_snapshot_dir(run_dir)


def _cleanup_stale_staging(settings: SnapshotSettings) -> None:
    root = _staging_root(settings)
    if not root.is_dir():
        return
    for d in root.iterdir():
        try:
            if time.time() - d.stat().st_mtime > STAGING_MAX_AGE_SECONDS:
                shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass


def _prune(settings: SnapshotSettings, active_run_id: str) -> None:
    runs = sorted((d for d in _runs_dir(settings).iterdir() if d.is_dir() and publish.RUN_ID_RE.match(d.name)),
                  key=lambda d: d.name, reverse=True)
    for d in runs[max(settings.keep, 1):]:
        if d.name != active_run_id:
            shutil.rmtree(d, ignore_errors=True)


def activate(staging_dir: Path, run_id: str, settings: SnapshotSettings) -> Path:
    """Move a fully verified staging dir into runs/<run_id>, then switch ACTIVE.json atomically.

    Readers only ever follow ACTIVE.json, so they see the old snapshot or the new
    one, never a partial one.
    """
    runs = _runs_dir(settings)
    runs.mkdir(parents=True, exist_ok=True)
    final = runs / run_id
    if final.exists():
        try:
            verify_snapshot_dir(final)           # identical run already on disk and intact: reuse it
            shutil.rmtree(staging_dir, ignore_errors=True)
        except SnapshotError:
            os.replace(final, runs / f"_damaged-{run_id}-{time.time_ns()}")  # keep for inspection
            os.replace(staging_dir, final)
    else:
        os.replace(staging_dir, final)           # same filesystem: atomic rename
    _atomic_write_json(settings.cache_dir / ACTIVE_FILE, {"run_id": run_id, "activated_at": publish.iso(publish.utc_now())})
    _prune(settings, run_id)
    return final


# --- 6. refresh ------------------------------------------------------------------------------------------

@dataclass
class RefreshResult:
    status: str                      # activated | unchanged | kept_active | failed
    run_id: Optional[str] = None
    reason: str = ""
    superseded_by: Optional[str] = None


def refresh(bucket, base_config, settings: SnapshotSettings,
            now: Callable[[], datetime] = publish.utc_now) -> RefreshResult:
    """Bring the local cache up to the published latest run, or leave it exactly as it was."""
    with _refresh_lock:
        try:
            return _refresh(bucket, base_config, settings, now)
        except SnapshotError as exc:
            return RefreshResult("failed", reason=str(exc))
        except Exception as exc:  # noqa: BLE001 - never let a loader bug break the dashboard
            return RefreshResult("failed", reason=f"{type(exc).__name__}: {exc}")


def _refresh(bucket, base_config, settings, now) -> RefreshResult:
    pointer, manifest, manifest_bytes = fetch_verified_manifest(bucket, settings)
    run_id = manifest["run_id"]

    try:
        active = read_active(settings)
    except SnapshotError as exc:
        log.warning("Active snapshot is damaged (%s); will re-download.", exc)
        active = None
    if active is not None:
        active_id = active[1]["run_id"]
        if active_id == run_id:
            return RefreshResult("unchanged", run_id, "already the latest published run")
        if active_id > run_id and not settings.allow_downgrade:
            return RefreshResult("kept_active", active_id,
                                 f"published latest {run_id} is older than active {active_id}; not downgrading")

    plan = plan_files(manifest, base_config, settings)
    _cleanup_stale_staging(settings)
    staging = _staging_root(settings) / f"{run_id}-{time.time_ns():x}"
    staging.mkdir(parents=True)
    try:
        stage_snapshot(bucket, plan, staging, settings)
        prov = build_provenance(pointer, manifest, sha256_bytes(manifest_bytes), plan, base_config, now)
        _atomic_write_json(staging / PROVENANCE_FILE, prov)
        verify_snapshot_dir(staging)             # final whole-snapshot check before it can become visible
        activate(staging, run_id, settings)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)   # last verified snapshot is untouched
        raise
    superseded = None
    try:  # informational: the run we activated is complete and immutable even if a newer one appeared
        one_shot = replace(settings, download_attempts=1)     # bounded: explicit timeout, no retries
        newer = publish.parse_pointer(_read(bucket, publish.latest_object(settings.runs_prefix), one_shot),
                                      settings.runs_prefix)
        if newer["run_id"] != run_id:
            superseded = newer["run_id"]
    except Exception:  # noqa: BLE001
        pass
    return RefreshResult("activated", run_id, "downloaded and verified", superseded_by=superseded)


# --- 7. data-source selection (what a dashboard would call) ---------------------------------------------------

class SnapshotConfig:
    """Drop-in for ``Config`` in snapshot mode.

    ``path(key)`` for eligible published outputs always points into the ONE
    active snapshot (even if that file is absent there: there is deliberately
    no per-file fallback to local files). Every other key (SoilGrids, events,
    ML, directories) delegates to the unchanged base config.
    """

    def __init__(self, base_config, snapshot_dir: Path, provenance: dict[str, Any], project_root: Path = PROJECT_ROOT):
        self._base = base_config
        self._dir = Path(snapshot_dir)
        self._root = Path(project_root).resolve()
        self.provenance = provenance

    def path(self, key: str) -> Path:
        base_path = self._base.path(key)
        if key in UPLOAD_KEYS:
            return self._dir / Path(base_path).resolve().relative_to(self._root)
        return base_path

    def __getattr__(self, name):
        if name.startswith("_"):          # avoid recursion before __init__ has run (copy/pickle)
            raise AttributeError(name)
        return getattr(self._base, name)


@dataclass
class DataSource:
    mode: str                        # local | gcs_snapshot | local_fallback
    config: Any                      # Config (local) or SnapshotConfig
    provenance: Optional[dict[str, Any]]
    reason: str
    warnings: list[str] = field(default_factory=list)


def data_source_mode(environ=None) -> str:
    raw = (environ if environ is not None else os.environ).get("MANGOTWIN_DATA_SOURCE")
    if raw is None or not raw.strip():
        return "local"
    value = raw.strip().lower()
    if value not in MODES:
        raise SnapshotError(f"MANGOTWIN_DATA_SOURCE={raw!r} is not one of {', '.join(MODES)}. Refusing to guess.")
    return value


def _env_number(env, name: str, default, kind, low, high):
    raw = env.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = kind(raw.strip())
    except ValueError as exc:
        raise SnapshotError(f"{name}={raw!r} is not a valid {kind.__name__}. Refusing to guess.") from exc
    if not low <= value <= high:
        raise SnapshotError(f"{name}={raw!r} must be between {low} and {high}.")
    return value


def settings_from_env(environ=None) -> SnapshotSettings:
    env = environ if environ is not None else os.environ
    s = SnapshotSettings(bucket=env.get("MANGOTWIN_GCS_BUCKET") or DEFAULT_BUCKET)
    if env.get("MANGOTWIN_SNAPSHOT_DIR"):
        s.cache_dir = Path(env["MANGOTWIN_SNAPSHOT_DIR"])
    s.download_attempts = _env_number(env, "MANGOTWIN_SNAPSHOT_DOWNLOAD_ATTEMPTS", s.download_attempts, int, 1, 10)
    s.connect_timeout = _env_number(env, "MANGOTWIN_SNAPSHOT_CONNECT_TIMEOUT_SECONDS", s.connect_timeout, float, 1, 120)
    s.read_timeout = _env_number(env, "MANGOTWIN_SNAPSHOT_READ_TIMEOUT_SECONDS", s.read_timeout, float, 1, 300)
    s.overall_deadline_seconds = _env_number(env, "MANGOTWIN_SNAPSHOT_DEADLINE_SECONDS", s.overall_deadline_seconds, float, 5, 3600)
    fresh = env.get("MANGOTWIN_SNAPSHOT_FRESH_CLIENT")
    if fresh is not None and fresh.strip():
        if fresh.strip().lower() not in ("true", "false"):
            raise SnapshotError(f"MANGOTWIN_SNAPSHOT_FRESH_CLIENT={fresh!r} must be true or false. Refusing to guess.")
        s.fresh_client_per_request = fresh.strip().lower() == "true"
    return s


def select_data_source(base_config, environ=None, settings: Optional[SnapshotSettings] = None,
                       bucket_factory: Optional[Callable[[SnapshotSettings], Any]] = None) -> DataSource:
    """Local by default. In snapshot mode: refresh, else last verified snapshot, else local.

    The result is always ONE coherent source: a single verified run, or the
    unchanged local files. Never a blend.
    """
    mode = data_source_mode(environ)
    if mode == "local":
        return DataSource("local", base_config, None, "local mode (default)")
    settings = settings or settings_from_env(environ)
    warnings: list[str] = []
    try:
        bucket = (bucket_factory or (lambda s: open_readonly_bucket(s.bucket)))(settings)
        result = refresh(bucket, base_config, settings)
        if result.status == "failed":
            warnings.append(f"Snapshot refresh failed: {result.reason}")
        elif result.superseded_by:
            warnings.append(f"A newer run ({result.superseded_by}) was published during download; it will load on next refresh.")
        elif result.status == "kept_active":
            warnings.append(result.reason)
    except Exception as exc:  # noqa: BLE001 - e.g. no ADC
        warnings.append(f"Snapshot refresh unavailable: {exc}")
    try:
        active = read_active(settings)
    except SnapshotError as exc:
        warnings.append(f"Cached snapshot unusable: {exc}")
        active = None
    if active is not None:
        run_dir, prov = active
        stale = any(w.startswith(("Snapshot refresh failed", "Snapshot refresh unavailable")) for w in warnings)
        reason = (f"serving last verified snapshot {prov['run_id']} (refresh failed)" if stale
                  else f"serving verified snapshot {prov['run_id']}")
        return DataSource("gcs_snapshot", SnapshotConfig(base_config, run_dir, prov, settings.project_root),
                          prov, reason, warnings)
    return DataSource("local_fallback", base_config, None,
                      "no verified snapshot available; using local files", warnings)
