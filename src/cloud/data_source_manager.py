"""
Process-wide selection of the dashboard's data source (local files or a verified GCS snapshot).

Pure Python (no Streamlit import) so it can be tested directly. ``app/data_source_ui.py``
wraps it for the dashboard.

Behaviour
---------
* ``MANGOTWIN_DATA_SOURCE`` unset / empty / ``local``  -> the unchanged local ``Config``.
  This path imports nothing from the GCS stack, touches no network and creates no
  directories: it is what the Streamlit Community Cloud deployment runs.
* ``gcs_snapshot`` -> ``snapshot_loader.select_data_source`` (refresh -> last verified
  snapshot -> local files), re-run at most once per refresh interval (default 300 s;
  60 s after a failed refresh), never on every Streamlit rerun.
* One decision is returned per call and the caller keeps it for the whole script run,
  so one dashboard execution sees exactly one snapshot (or exactly the local files).
* If a later refresh cannot produce a verified snapshot, the previously resolved
  snapshot keeps being served, with a warning; it is never silently replaced by local files.
* Every problem becomes a visible ``Notice``; nothing here raises into the dashboard.

Snapshot paths contain the run id (``.../runs/<run-id>/data/...``), and the dashboard's
``st.cache_data`` loaders are keyed by path, so a new run can never be served from
DataFrames cached for an older run.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from src.utils.config import get_config

log = logging.getLogger("mangotwin.data_source")

ENV_MODE = "MANGOTWIN_DATA_SOURCE"
ENV_REFRESH = "MANGOTWIN_SNAPSHOT_REFRESH_SECONDS"
DEFAULT_REFRESH_SECONDS = 300.0
FAILED_REFRESH_RETRY_SECONDS = 60.0
MIN_REFRESH_SECONDS, MAX_REFRESH_SECONDS = 60.0, 86400.0
# Resources that always stay on their existing (local) sources.
EXTERNAL_ML_KEYS = ("irrigation_priority_model_path", "ml_model_metrics_json",
                    "ml_feature_importance_csv", "ml_training_dataset_csv")
EXTERNAL_INPUT_LABELS = {"soilgrids_csv": "SoilGrids soil data",
                         "irrigation_events_csv": "Irrigation events (GitHub-backed)"}
INTEGRITY_NOTE = ("Checksums (SHA-256) and sizes match what the pipeline published. This is an integrity check, "
                  "not field validation or evidence of scientific accuracy; irrigation labels are surrogate.")


@dataclass(frozen=True)
class Notice:
    level: str            # "info" | "warning"
    text: str
    prominent: bool = False   # shown in the main page area, not only in the sidebar


@dataclass
class ResolvedSource:
    mode: str                                   # local | gcs_snapshot | local_fallback
    config: Any                                 # Config or SnapshotConfig
    provenance: Optional[dict[str, Any]]
    reason: str
    notices: list[Notice] = field(default_factory=list)
    checked_at: Optional[datetime] = None
    refresh_ok: bool = True
    external_artifacts: dict[str, bool] = field(default_factory=dict)

    @property
    def is_snapshot(self) -> bool:
        return self.mode == "gcs_snapshot"

    @property
    def run_id(self) -> Optional[str]:
        return self.provenance["run_id"] if self.provenance else None


# --- notices / provenance rows (pure functions) ----------------------------------------------------

def external_artifact_status(base_config) -> dict[str, bool]:
    out = {}
    for key in EXTERNAL_ML_KEYS:
        try:
            out[key] = Path(base_config.path(key)).exists()
        except Exception:  # noqa: BLE001
            out[key] = False
    return out


def build_notices(mode: str, provenance: Optional[dict[str, Any]], warnings: list[str],
                  external_artifacts: dict[str, bool], refresh_ok: bool) -> list[Notice]:
    notices: list[Notice] = []
    if mode == "local_fallback":
        notices.append(Notice("warning", "GCS snapshot mode is enabled but no verified snapshot is available; "
                                         "showing the local files instead.", True))
    for w in warnings:
        notices.append(Notice("warning", w, mode == "local_fallback" or not refresh_ok))
    if mode == "gcs_snapshot" and provenance:
        if not refresh_ok:
            notices.append(Notice("warning", f"Showing the last verified snapshot ({provenance['run_id']}); "
                                             "the latest refresh failed.", True))
        ext = provenance.get("external_dependencies") or {}
        for key, label in EXTERNAL_INPUT_LABELS.items():
            status = (ext.get(key) or {}).get("status")
            if status == "differs_from_run_input":
                notices.append(Notice("warning",
                                      f"{label}: the local copy differs from the version this run "
                                      f"({provenance['run_id']}) was computed with. Snapshot outputs do not reflect "
                                      "the local data shown on other pages.", True))
            elif status == "formatting_only_difference":
                notices.append(Notice("info", f"{label}: the local copy differs from this run's input only in formatting "
                                              "(for example line endings); the CSV records are identical to the "
                                              "verified run input.", False))
            elif status in ("reference_unavailable", "comparison_failed"):
                notices.append(Notice("warning",
                                      f"{label}: the local copy's bytes differ from the version this run "
                                      f"({provenance['run_id']}) was computed with, and it could not be confirmed "
                                      "whether the difference is only formatting. Treat it as different.", True))
            elif status == "local_file_missing":
                notices.append(Notice("warning", f"{label}: the local file is missing; pages that need it will be unavailable.", True))
            elif status == "not_recorded_in_manifest":
                notices.append(Notice("info", f"{label}: this run did not record the version it used, so the local copy cannot be compared.", False))
        ev = provenance.get("irrigation_events_provenance") or {}
        if ev.get("verified_against_github") is False:
            notices.append(Notice("info", "The run used a GCS copy of the irrigation events that was not verified against GitHub.", False))
        missing = [k for k, ok in external_artifacts.items() if not ok]
        if missing:
            notices.append(Notice("info", "Not part of the snapshot and not found locally: " + ", ".join(missing)
                                  + ". The AI/ML preview will show these as unavailable.", False))
        notices.append(Notice("info", "ML artifacts, SoilGrids and irrigation events always come from local files and may "
                                      "have been produced from a different run than the snapshot.", False))
    return notices


def provenance_rows(resolved: ResolvedSource) -> list[tuple[str, str]]:
    """(label, value) pairs for the sidebar provenance panel."""
    rows: list[tuple[str, str]] = [("Data source", {"local": "Local files (default)",
                                                    "gcs_snapshot": "Verified GCS snapshot",
                                                    "local_fallback": "Local files (snapshot unavailable)"}[resolved.mode])]
    p = resolved.provenance
    if not p:
        return rows
    rows += [
        ("Run ID", p["run_id"]),
        ("Executed (UTC)", p["executed_at"]),
        ("Fetched (UTC)", p.get("fetched_at", "")),
        ("Pipeline status", p["pipeline_status"]),
        ("Integrity", f"SHA-256 + size verified for {len(p.get('files', []))} files"),
        ("Validation status", f"{p['validation_status']} (field validated: {'yes' if p.get('field_validated') else 'no'})"),
    ]
    for name, s in sorted((p.get("satellite_observation") or {}).items()):
        rows.append((f"Satellite: {name}", f"{s.get('status')}, latest observation {s.get('latest_observation_date')}"))
    for key, d in sorted((p.get("input_observation_dates") or {}).items()):
        rows.append((f"Input date: {key}", str(d)))
    for key, v in sorted((p.get("input_versions") or {}).items()):
        gen = v.get("generation")
        rows.append((f"Input version: {key}", f"generation {gen}" if gen is not None else "n/a"))
    return rows


# --- manager -------------------------------------------------------------------------------------------------

def _refresh_interval(env) -> float:
    raw = (env.get(ENV_REFRESH) or "").strip()
    if not raw:
        return DEFAULT_REFRESH_SECONDS
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{ENV_REFRESH}={raw!r} is not a number") from exc
    if not MIN_REFRESH_SECONDS <= value <= MAX_REFRESH_SECONDS:
        raise ValueError(f"{ENV_REFRESH}={raw!r} must be between {MIN_REFRESH_SECONDS:.0f} and {MAX_REFRESH_SECONDS:.0f}")
    return value


class DataSourceManager:
    def __init__(self, base_config=None, environ=None, bucket_factory: Optional[Callable[[Any], Any]] = None,
                 clock: Callable[[], float] = time.monotonic,
                 now: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self._base = base_config
        self._environ = environ
        self._bucket_factory = bucket_factory
        self._clock, self._now = clock, now
        self._lock = threading.Lock()
        self._current: Optional[ResolvedSource] = None
        self._expires = 0.0
        self._mode_key: Optional[str] = None

    # -- helpers --
    def _env(self):
        return self._environ if self._environ is not None else os.environ

    def _base_config(self):
        if self._base is None:
            self._base = get_config()
        return self._base

    def _local(self) -> ResolvedSource:
        if self._mode_key != "local" or self._current is None:
            self._current = ResolvedSource("local", self._base_config(), None, "local mode (default)", [], self._now())
            self._mode_key, self._expires = "local", float("inf")
        return self._current

    # -- public --
    def get(self, force: bool = False) -> ResolvedSource:
        """The data source for THIS script run. Cheap (no I/O) unless the refresh interval elapsed."""
        raw = (self._env().get(ENV_MODE) or "").strip().lower()
        if raw in ("", "local"):
            return self._local()
        cur = self._current
        if cur is not None and self._mode_key == raw and not force and self._clock() < self._expires:
            return cur
        have_same_mode = cur is not None and self._mode_key == raw
        if not self._lock.acquire(blocking=not have_same_mode):
            return cur          # another session is refreshing; keep serving the current coherent source
        try:
            if have_same_mode and not force and self._current is not None and self._clock() < self._expires:
                return self._current   # refreshed by someone else while we waited
            return self._refresh(raw)
        finally:
            self._lock.release()

    # -- internals --
    def _refresh(self, raw: str) -> ResolvedSource:
        env = self._env()
        previous = self._current if self._mode_key == raw else None
        try:
            interval = _refresh_interval(env)
            from src.cloud import snapshot_loader as sl      # lazy: never imported in local mode
            settings = sl.settings_from_env(env)
            source = sl.select_data_source(self._base_config(), env, settings, self._bucket_factory)
        except Exception as exc:  # noqa: BLE001 - invalid env, missing libs... must never break the dashboard
            log.warning("Data source selection failed: %s", exc)
            return self._failed(raw, previous, f"{type(exc).__name__}: {exc}", FAILED_REFRESH_RETRY_SECONDS)

        refresh_failed = any(w.startswith(("Snapshot refresh failed", "Snapshot refresh unavailable")) for w in source.warnings)
        if source.mode == "local_fallback" and previous is not None and previous.is_snapshot:
            return self._failed(raw, previous, "; ".join(source.warnings) or source.reason, FAILED_REFRESH_RETRY_SECONDS)
        ok = source.mode == "gcs_snapshot" and not refresh_failed
        external = external_artifact_status(self._base_config()) if source.mode == "gcs_snapshot" else {}
        resolved = ResolvedSource(source.mode, source.config, source.provenance, source.reason,
                                  build_notices(source.mode, source.provenance, source.warnings, external, ok),
                                  self._now(), ok, external)
        self._current, self._mode_key = resolved, raw
        self._expires = self._clock() + (interval if ok else min(interval, FAILED_REFRESH_RETRY_SECONDS))
        return resolved

    def _failed(self, raw: str, previous: Optional[ResolvedSource], why: str, retry_in: float) -> ResolvedSource:
        """Refresh could not produce a verified snapshot: keep the previous one, else local files."""
        if previous is not None and previous.is_snapshot:
            kept = ResolvedSource(previous.mode, previous.config, previous.provenance, previous.reason,
                                  [n for n in previous.notices if not n.text.startswith("Showing the last verified snapshot")]
                                  + [Notice("warning", f"Showing the last verified snapshot ({previous.run_id}); "
                                                       f"the latest refresh failed: {why}", True)],
                                  self._now(), False, previous.external_artifacts)
            self._current = kept
        else:
            base = self._base_config()
            self._current = ResolvedSource(
                "local_fallback", base, None, "no verified snapshot available; using local files",
                [Notice("warning", f"GCS snapshot mode is enabled but unavailable ({why}); showing the local files instead.", True)],
                self._now(), False)
        self._mode_key, self._expires = raw, self._clock() + retry_in
        return self._current
