"""
Versioned, all-or-nothing publishing of a verified pipeline run to GCS.

Layout (all under ``pipeline-runs/``; nothing else in the bucket is ever written):

    pipeline-runs/<run-id>/data/processed/<file>.csv ...   the verified outputs
    pipeline-runs/<run-id>/manifest.json                   completion marker
    pipeline-runs/latest.json                              pointer to the newest COMPLETE run

Protocol (each step is covered by tests/test_cloud_publish.py):

  1. Every output is uploaded under a run-unique prefix with
     ``if_generation_match=0`` ("must not exist"), so a published run object is
     never overwritten, and then read back (size + MD5) to prove it landed.
  2. Only after ALL outputs are uploaded and verified is ``manifest.json``
     written (also create-only, also verified). A run without a manifest is
     incomplete by definition and nothing ever points at it.
  3. Only after the manifest is verified is ``latest.json`` promoted, by
     compare-and-swap on its GCS generation. A concurrent promotion makes the
     swap fail; the loser re-reads and never moves the pointer backwards.
  4. Any failure before step 3 leaves the previous ``latest.json`` untouched.
     Objects already uploaded for the failed run are left in place, unreferenced
     (this job has no delete permission need; use a lifecycle rule to expire
     ``pipeline-runs/<id>/`` prefixes that have no manifest).

Transient errors are retried with exponential backoff. An upload that fails with
"already exists" is accepted only if the existing object is byte-identical
(a previous attempt whose response was lost); otherwise it is an error.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from src.cloud.errors import JobError

RUNS_PREFIX = "pipeline-runs"
LATEST_NAME = "latest.json"
MANIFEST_NAME = "manifest.json"
SCHEMA_VERSION = 1
RUN_ID_RE = re.compile(r"^\d{8}T\d{6}Z-[0-9a-f]{8}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_SUFFIXES = (".joblib", ".pkl", ".pickle", ".pt", ".h5", ".onnx")
PROTECTED_FILENAMES = ("muthukur_irrigation_events.csv",)

UPLOAD_ATTEMPTS = 4
BACKOFF_SECONDS = 1.0
PROMOTE_ATTEMPTS = 4


class PublishError(JobError):
    """A publishing step failed; previous latest pointer is preserved."""


# --- identifiers / names ------------------------------------------------------

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_run_id(now: Optional[datetime] = None, token: Optional[str] = None) -> str:
    """UTC timestamp + random token. Sorts chronologically (same fixed width)."""
    now = now or utc_now()
    return f"{now.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{token or secrets.token_hex(4)}"


def check_run_id(run_id: str) -> str:
    if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
        raise PublishError(f"Invalid run id {run_id!r}; expected YYYYMMDDTHHMMSSZ-<8 hex>.")
    return run_id


def run_prefix(run_id: str, runs_prefix: str = RUNS_PREFIX) -> str:
    return f"{runs_prefix.strip('/')}/{check_run_id(run_id)}/"


def manifest_object(run_id: str, runs_prefix: str = RUNS_PREFIX) -> str:
    return run_prefix(run_id, runs_prefix) + MANIFEST_NAME


def latest_object(runs_prefix: str = RUNS_PREFIX) -> str:
    return f"{runs_prefix.strip('/')}/{LATEST_NAME}"


def run_object_name(rel_under_data: str, run_id: str, runs_prefix: str = RUNS_PREFIX) -> str:
    """pipeline-runs/<run-id>/data/<relative path under data/>  (path preserved)."""
    return run_prefix(run_id, runs_prefix) + "data/" + rel_under_data.replace("\\", "/").lstrip("/")


# --- hashing -------------------------------------------------------------------

def md5_b64_of_file(path: Path) -> str:
    h = hashlib.md5(usedforsecurity=False)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return base64.b64encode(h.digest()).decode("ascii")


def md5_b64_of_bytes(data: bytes) -> str:
    return base64.b64encode(hashlib.md5(data, usedforsecurity=False).digest()).decode("ascii")


def canonical_json(obj: Any) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8")


# --- error classification / retry ------------------------------------------------

def classify_error(exc: BaseException) -> str:
    """'precondition' (HTTP 412), 'transient' (retry) or 'permanent' (do not retry)."""
    if isinstance(exc, (FileNotFoundError, PermissionError, PublishError, JobError)):
        return "permanent"
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        if code == 412:
            return "precondition"
        if code in (408, 429) or code >= 500:
            return "transient"
        if 400 <= code < 500:
            return "permanent"
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return "transient"
    return "permanent"


def with_retries(fn: Callable[[], Any], what: str, attempts: int = UPLOAD_ATTEMPTS,
                 sleep: Callable[[float], None] = time.sleep, base: float = BACKOFF_SECONDS) -> Any:
    """Run fn(); retry transient failures with exponential backoff.

    Non-transient exceptions propagate unchanged. Exhausted retries raise PublishError.
    """
    last: Optional[BaseException] = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - classified below
            if classify_error(exc) != "transient":
                raise
            last = exc
            if i < attempts - 1:
                sleep(base * (2 ** i))
    raise PublishError(f"{what} failed after {attempts} attempt(s): {type(last).__name__}: {last}") from last


# --- write scope ----------------------------------------------------------------

class WriteScopedBucket:
    """Defence in depth: .blob() (the only write entry point) only opens objects
    under ``<runs_prefix>/``. Reads (.get_blob) are unrestricted. A bug can
    therefore never write to data/raw, data/processed or data/manual."""

    def __init__(self, bucket, runs_prefix: str = RUNS_PREFIX):
        self._bucket = bucket
        self._scope = runs_prefix.strip("/") + "/"

    def get_blob(self, name):
        return self._bucket.get_blob(name)

    def blob(self, name):
        parts = name.split("/")
        if not name.startswith(self._scope) or ".." in parts or "" in parts[:-1]:
            raise PublishError(f"Refusing to write outside gs://.../{self._scope}: {name!r}")
        if parts[-1] in PROTECTED_FILENAMES or name.lower().endswith(FORBIDDEN_SUFFIXES):
            raise PublishError(f"Refusing to write protected or model file: {name!r}")
        return self._bucket.blob(name)


# --- upload with verification ----------------------------------------------------

def remote_matches(bucket, name: str, size: int, md5_b64: str, sha256: Optional[str] = None) -> bool:
    blob = bucket.get_blob(name)
    if blob is None or int(blob.size) != size:
        return False
    remote_md5 = getattr(blob, "md5_hash", None)
    if remote_md5:
        return remote_md5 == md5_b64
    if sha256:  # no server-side hash available: compare content
        return hashlib.sha256(blob.download_as_bytes()).hexdigest() == sha256
    return False


def _upload_create_only(bucket, name: str, do_upload: Callable[[Any], None], size: int, md5_b64: str,
                        sha256: Optional[str], attempts: int, sleep) -> None:
    def attempt():
        try:
            do_upload(bucket.blob(name))
        except Exception as exc:  # noqa: BLE001
            if classify_error(exc) == "precondition":
                if remote_matches(bucket, name, size, md5_b64, sha256):
                    return  # an earlier attempt landed; identical content
                raise PublishError(
                    f"{name} already exists with different content; refusing to overwrite a published run object."
                ) from exc
            raise

    with_retries(attempt, f"upload of {name}", attempts, sleep)
    if not with_retries(lambda: remote_matches(bucket, name, size, md5_b64, sha256),
                        f"verification of {name}", attempts, sleep):
        raise PublishError(f"Post-upload verification failed for {name}: size/MD5 do not match the local file.")


def upload_file_verified(bucket, name: str, local: Path, size: int, md5_b64: str, sha256: str,
                         attempts: int = UPLOAD_ATTEMPTS, sleep=time.sleep) -> None:
    _upload_create_only(
        bucket, name,
        lambda blob: blob.upload_from_filename(str(local), if_generation_match=0),
        size, md5_b64, sha256, attempts, sleep)


def upload_bytes_verified(bucket, name: str, data: bytes, content_type: str = "application/json",
                          attempts: int = UPLOAD_ATTEMPTS, sleep=time.sleep) -> None:
    _upload_create_only(
        bucket, name,
        lambda blob: blob.upload_from_string(data, content_type=content_type, if_generation_match=0),
        len(data), md5_b64_of_bytes(data), hashlib.sha256(data).hexdigest(), attempts, sleep)


# --- manifest -----------------------------------------------------------------------

def build_manifest(*, run_id: str, runs_prefix: str, started_at: str, executed_at: str,
                   pipeline_status: str, outputs: list[dict[str, Any]], skipped_optional: list[str],
                   inputs: dict[str, Any], satellite_data: dict[str, Any],
                   scientific_validation: dict[str, Any], runtime: dict[str, Any],
                   irrigation_events: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
    csvs = [o for o in outputs if o["filename"].endswith(".csv")]
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "run_prefix": run_prefix_for(run_id, runs_prefix),
        "started_at": started_at,
        "executed_at": executed_at,
        "pipeline_status": pipeline_status,
        "execution": execution,
        "input_observation_dates": {k: v.get("latest_date") for k, v in sorted(inputs.items())},
        "inputs": inputs,
        "irrigation_events": irrigation_events,
        "satellite_data": satellite_data,
        "scientific_validation": scientific_validation,
        "runtime": runtime,
        "outputs": sorted(outputs, key=lambda o: o["object"]),
        "skipped_optional_outputs": sorted(skipped_optional),
        "output_counts": {
            "files": len(outputs),
            "csv_files": len(csvs),
            "total_csv_rows": sum(int(o.get("rows") or 0) for o in csvs),
            "total_bytes": sum(int(o["bytes"]) for o in outputs),
            "rows_by_file": {o["filename"]: o.get("rows") for o in csvs},
        },
    }


def run_prefix_for(run_id: str, runs_prefix: str) -> str:
    return run_prefix(run_id, runs_prefix)


_REQUIRED_TOP = ("schema_version", "run_id", "run_prefix", "started_at", "executed_at", "pipeline_status",
                 "input_observation_dates", "inputs", "irrigation_events", "satellite_data",
                 "scientific_validation", "runtime", "outputs", "output_counts")


def validate_manifest(manifest: Any, runs_prefix: str = RUNS_PREFIX, allowed_keys: Optional[Iterable[str]] = None,
                      require_key: Optional[str] = None) -> None:
    """Raise PublishError listing every problem. Pure; no I/O."""
    problems: list[str] = []
    if not isinstance(manifest, dict):
        raise PublishError("Manifest is not a JSON object.")
    for k in _REQUIRED_TOP:
        if k not in manifest:
            problems.append(f"missing field: {k}")
    if problems:
        raise PublishError("Manifest invalid: " + "; ".join(problems))

    if manifest["schema_version"] != SCHEMA_VERSION:
        problems.append(f"unsupported schema_version {manifest['schema_version']!r}")
    run_id = manifest["run_id"]
    if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
        problems.append(f"bad run_id {run_id!r}")
        raise PublishError("Manifest invalid: " + "; ".join(problems))
    prefix = run_prefix(run_id, runs_prefix)
    if manifest["run_prefix"] != prefix:
        problems.append(f"run_prefix {manifest['run_prefix']!r} != {prefix!r}")
    for field in ("started_at", "executed_at"):
        try:
            datetime.strptime(str(manifest[field]), "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            problems.append(f"{field} is not an ISO UTC timestamp: {manifest[field]!r}")
    if manifest["pipeline_status"] != "success":
        problems.append(f"pipeline_status is {manifest['pipeline_status']!r}, not 'success'")
    if not isinstance(manifest["input_observation_dates"], dict) or not manifest["input_observation_dates"]:
        problems.append("input_observation_dates is empty")
    sv = manifest["scientific_validation"]
    if not isinstance(sv, dict) or not sv.get("status"):
        problems.append("scientific_validation.status missing")
    rt = manifest["runtime"]
    if not isinstance(rt, dict) or not rt.get("python") or not isinstance(rt.get("libraries"), dict) or not rt["libraries"]:
        problems.append("runtime.python / runtime.libraries missing")
    if not isinstance(manifest["satellite_data"], dict):
        problems.append("satellite_data must be an object")

    outputs = manifest["outputs"]
    if not isinstance(outputs, list) or not outputs:
        problems.append("outputs is empty")
        outputs = []
    seen: set[str] = set()
    allowed = set(allowed_keys) if allowed_keys is not None else None
    for o in outputs:
        if not isinstance(o, dict):
            problems.append("output entry is not an object")
            continue
        obj = str(o.get("object", ""))
        label = obj or "<no object>"
        if not obj.startswith(prefix + "data/") or ".." in obj.split("/"):
            problems.append(f"{label}: not under {prefix}data/")
        if obj in seen:
            problems.append(f"{label}: duplicate object")
        seen.add(obj)
        if o.get("filename") != obj.rsplit("/", 1)[-1] or not o.get("filename"):
            problems.append(f"{label}: filename does not match object name")
        if o.get("filename") in PROTECTED_FILENAMES:
            problems.append(f"{label}: protected file in manifest")
        if obj.lower().endswith(FORBIDDEN_SUFFIXES):
            problems.append(f"{label}: model artifact in manifest")
        if not SHA256_RE.match(str(o.get("sha256", ""))):
            problems.append(f"{label}: sha256 missing or malformed")
        if not o.get("md5_base64"):
            problems.append(f"{label}: md5_base64 missing")
        if not isinstance(o.get("bytes"), int) or o["bytes"] <= 0:
            problems.append(f"{label}: bytes must be a positive integer")
        if allowed is not None and o.get("key") not in allowed:
            problems.append(f"{label}: key {o.get('key')!r} is not publishable")
    counts = manifest["output_counts"]
    if not isinstance(counts, dict) or counts.get("files") != len(outputs):
        problems.append(f"output_counts.files {counts.get('files') if isinstance(counts, dict) else None!r} "
                        f"!= {len(outputs)} listed outputs")
    if require_key and not any(o.get("key") == require_key for o in outputs if isinstance(o, dict)):
        problems.append(f"required output {require_key!r} not in manifest")
    if problems:
        raise PublishError("Manifest invalid: " + "; ".join(problems))


def verify_run_objects(bucket, manifest: dict[str, Any], attempts: int = UPLOAD_ATTEMPTS, sleep=time.sleep) -> None:
    """Every listed output must exist in the bucket with the recorded size and MD5."""
    bad = []
    for o in manifest["outputs"]:
        ok = with_retries(
            lambda o=o: remote_matches(bucket, o["object"], o["bytes"], o["md5_base64"], o["sha256"]),
            f"verification of {o['object']}", attempts, sleep)
        if not ok:
            bad.append(o["object"])
    if bad:
        raise PublishError("Run objects missing or different from the manifest: " + ", ".join(bad))


# --- latest pointer -------------------------------------------------------------------

def parse_pointer(data: bytes, runs_prefix: str = RUNS_PREFIX) -> dict[str, Any]:
    try:
        ptr = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise PublishError(f"{latest_object(runs_prefix)} is not valid JSON ({exc}); not overwriting it. "
                           "Inspect it manually.") from exc
    problems = []
    if not isinstance(ptr, dict):
        problems.append("not an object")
    else:
        if ptr.get("schema_version") != SCHEMA_VERSION:
            problems.append("schema_version")
        if not isinstance(ptr.get("run_id"), str) or not RUN_ID_RE.match(ptr["run_id"]):
            problems.append("run_id")
        elif ptr.get("manifest_object") != manifest_object(ptr["run_id"], runs_prefix):
            problems.append("manifest_object")
        if not SHA256_RE.match(str(ptr.get("manifest_sha256", ""))):
            problems.append("manifest_sha256")
    if problems:
        raise PublishError(f"{latest_object(runs_prefix)} has an unexpected shape ({', '.join(problems)}); "
                           "not overwriting it. Inspect it manually.")
    return ptr


def promote_latest(bucket, manifest: dict[str, Any], manifest_sha256: str, runs_prefix: str = RUNS_PREFIX,
                   attempts: int = PROMOTE_ATTEMPTS, sleep=time.sleep, now: Callable[[], datetime] = utc_now) -> dict[str, Any]:
    """Compare-and-swap latest.json to this run. Never moves the pointer backwards.

    Returns {"promoted": bool, "reason": str, ...}. Raises PublishError if it
    could not be decided safely (previous pointer is left in place).
    """
    run_id = manifest["run_id"]
    name = latest_object(runs_prefix)
    last_error: Optional[BaseException] = None
    for i in range(attempts):
        blob = with_retries(lambda: bucket.get_blob(name), f"read of {name}", sleep=sleep)
        generation, previous = 0, None
        if blob is not None:
            generation = int(blob.generation)
            previous = parse_pointer(with_retries(blob.download_as_bytes, f"read of {name}", sleep=sleep), runs_prefix)
            if previous["run_id"] == run_id:
                return {"promoted": True, "reason": "already_latest", "previous_run_id": previous.get("previous_run_id")}
            if previous["run_id"] > run_id:
                return {"promoted": False, "reason": "newer_run_already_latest", "current_run_id": previous["run_id"]}
        pointer = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "manifest_object": manifest_object(run_id, runs_prefix),
            "manifest_sha256": manifest_sha256,
            "executed_at": manifest["executed_at"],
            "promoted_at": iso(now()),
            "previous_run_id": previous["run_id"] if previous else None,
        }
        try:
            bucket.blob(name).upload_from_string(canonical_json(pointer), content_type="application/json",
                                                 if_generation_match=generation)
            return {"promoted": True, "reason": "promoted", "previous_run_id": pointer["previous_run_id"]}
        except Exception as exc:  # noqa: BLE001
            kind = classify_error(exc)
            if kind == "permanent":
                raise PublishError(f"Could not update {name}: {type(exc).__name__}: {exc}") from exc
            last_error = exc  # precondition (someone promoted first) or transient: re-read and decide again
            if kind == "transient":
                sleep(BACKOFF_SECONDS * (2 ** i))
    raise PublishError(
        f"Could not promote {run_id} to {name} after {attempts} attempt(s) "
        f"({type(last_error).__name__}: {last_error}). The previous latest pointer is unchanged; "
        f"the run is complete under {run_prefix(run_id, runs_prefix)} and can be promoted by re-running verification."
    ) from last_error


def read_latest(bucket, runs_prefix: str = RUNS_PREFIX) -> Optional[dict[str, Any]]:
    blob = bucket.get_blob(latest_object(runs_prefix))
    return None if blob is None else parse_pointer(blob.download_as_bytes(), runs_prefix)


def verify_latest(bucket, runs_prefix: str = RUNS_PREFIX, allowed_keys=None, require_key=None,
                  attempts: int = UPLOAD_ATTEMPTS, sleep=time.sleep) -> dict[str, Any]:
    """Read-only: latest.json -> manifest -> every listed object. Raises PublishError."""
    ptr = read_latest(bucket, runs_prefix)
    if ptr is None:
        raise PublishError(f"{latest_object(runs_prefix)} does not exist.")
    blob = bucket.get_blob(ptr["manifest_object"])
    if blob is None:
        raise PublishError(f"latest.json points at a missing manifest: {ptr['manifest_object']}")
    data = blob.download_as_bytes()
    if hashlib.sha256(data).hexdigest() != ptr["manifest_sha256"]:
        raise PublishError("Manifest content does not match manifest_sha256 recorded in latest.json.")
    manifest = json.loads(data.decode("utf-8"))
    validate_manifest(manifest, runs_prefix, allowed_keys, require_key)
    if manifest["run_id"] != ptr["run_id"]:
        raise PublishError("Manifest run_id does not match latest.json.")
    verify_run_objects(bucket, manifest, attempts, sleep)
    return {"run_id": ptr["run_id"], "files": len(manifest["outputs"]), "executed_at": manifest["executed_at"]}


# --- orchestration ------------------------------------------------------------------

def publish_run(bucket, manifest: dict[str, Any], files: list[tuple[Path, dict[str, Any]]],
                runs_prefix: str = RUNS_PREFIX, attempts: int = UPLOAD_ATTEMPTS, sleep=time.sleep,
                now: Callable[[], datetime] = utc_now, last_key: Optional[str] = None) -> dict[str, Any]:
    """Upload outputs -> verify -> manifest -> promote. `files` pairs each local
    path with its manifest output entry. `bucket` is scoped to runs_prefix here."""
    validate_manifest(manifest, runs_prefix)
    scoped = bucket if isinstance(bucket, WriteScopedBucket) else WriteScopedBucket(bucket, runs_prefix)
    ordered = sorted(files, key=lambda f: f[1].get("key") == last_key)  # stable; last_key goes last
    uploaded: list[str] = []
    try:
        for local, entry in ordered:
            upload_file_verified(scoped, entry["object"], local, entry["bytes"], entry["md5_base64"],
                                 entry["sha256"], attempts, sleep)
            uploaded.append(entry["object"])
        verify_run_objects(scoped, manifest, attempts, sleep)
        manifest_bytes = canonical_json(manifest)
        name = manifest_object(manifest["run_id"], runs_prefix)
        upload_bytes_verified(scoped, name, manifest_bytes, attempts=attempts, sleep=sleep)
        uploaded.append(name)
    except Exception as exc:  # noqa: BLE001 - any failure here must leave latest.json alone
        raise PublishError(
            f"{exc} | run {manifest['run_id']} is INCOMPLETE ({len(uploaded)} object(s) uploaded, no manifest "
            f"published); latest.json was not changed."
        ) from exc
    promotion = promote_latest(scoped, manifest, hashlib.sha256(manifest_bytes).hexdigest(),
                               runs_prefix, sleep=sleep, now=now)
    return {"run_id": manifest["run_id"], "uploaded": uploaded, "manifest_object": name, **promotion}
