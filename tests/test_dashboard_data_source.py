"""Tests for the optional GCS snapshot data source in the Streamlit dashboard.

Covers: local default, snapshot selection, provenance display, refresh interval, cache behaviour
across run changes, unavailable credentials, differing/missing external inputs, and full-app
AppTest runs. A mocked in-memory bucket and temp directories only: no network, no credentials.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from cloud_fakes import GOOD_BUCKET, EVENTS, FakeBucket, FakeConfig, fake_runner
from src.cloud import data_source_manager as dsm
from src.cloud import publish
from src.cloud import run_pipeline_job as job
from src.cloud import snapshot_loader as sl
from src.utils.config import PROJECT_ROOT, get_config

REPO = Path(PROJECT_ROOT)
APP = REPO / "app" / "streamlit_app.py"
RUN_A = "20261114T100000Z-aaaaaaaa"
RUN_B = "20261114T110000Z-bbbbbbbb"
LATEST = "pipeline-runs/latest.json"
ENV_KEYS = ("MANGOTWIN_DATA_SOURCE", "MANGOTWIN_SNAPSHOT_DIR", "MANGOTWIN_SNAPSHOT_REFRESH_SECONDS",
            "MANGOTWIN_GCS_BUCKET")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in ENV_KEYS:
        monkeypatch.delenv(k, raising=False)


# --- published fixtures -------------------------------------------------------------------------

@pytest.fixture(scope="module")
def published(tmp_path_factory):
    """Bucket contents after two real publishes (run A, then run B), built by the real publisher."""
    root = tmp_path_factory.mktemp("pub")
    cfg = FakeConfig(root)
    settings = job.JobSettings(project_root=root, refresh_sentinel2=False, dry_run=False,
                               accept_unverified_events=True, allow_local_overwrite=True)
    bucket = FakeBucket(GOOD_BUCKET)
    snaps = {}
    for rid in (RUN_A, RUN_B):
        settings.run_id = rid
        job.run_job(bucket, settings, cfg, runner=fake_runner(cfg))
        snaps[rid] = dict(bucket.objects)
    return snaps


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class Factory:
    """bucket_factory that counts how often GCS is contacted and can be switched between runs."""

    def __init__(self, objects):
        self.objects, self.calls, self.error = objects, 0, None

    def __call__(self, settings):
        self.calls += 1
        if self.error:
            raise self.error
        return sl.ReadOnlyBucket(FakeBucket(self.objects))


def manager(tmp_path, factory, env=None, base=None, clock=None):
    environ = {"MANGOTWIN_DATA_SOURCE": "gcs_snapshot", "MANGOTWIN_SNAPSHOT_DIR": str(tmp_path / "cache"),
               **(env or {})}
    return dsm.DataSourceManager(base or get_config(), environ, factory, clock or Clock()), environ


def texts(resolved, prominent=None):
    return [n.text for n in resolved.notices if prominent is None or n.prominent == prominent]


# --- local default ---------------------------------------------------------------------------------

@pytest.mark.parametrize("env", [{}, {"MANGOTWIN_DATA_SOURCE": ""}, {"MANGOTWIN_DATA_SOURCE": "local"},
                                 {"MANGOTWIN_DATA_SOURCE": " LOCAL "}])
def test_local_is_the_default_and_returns_the_unchanged_config(env):
    base = get_config()
    m = dsm.DataSourceManager(base, env, bucket_factory=lambda s: pytest.fail("GCS must not be contacted"))
    r = m.get()
    assert r.mode == "local" and r.config is base and r.provenance is None and r.notices == []
    assert m.get() is r                       # stable object for the whole process
    assert r.config.path("historical_risk_csv") == REPO / "data/processed/muthukur_weather_risk_scores.csv"


def test_local_mode_never_imports_gcs_or_loader_and_creates_nothing(tmp_path):
    code = ("import sys; from src.cloud.data_source_manager import DataSourceManager; "
            "r = DataSourceManager(environ={}).get(); "
            "bad = [m for m in sys.modules if m.startswith(('google.auth', 'google.cloud.storage', 'src.cloud.snapshot_loader', 'src.cloud.run_pipeline_job'))]; "
            "print(r.mode, bad)")
    env = {k: v for k, v in os.environ.items() if not k.startswith("MANGOTWIN_")}
    out = subprocess.run([sys.executable, "-c", code], cwd=REPO, env={**env, "HOME": str(tmp_path), "USERPROFILE": str(tmp_path)},
                         capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "local []"
    assert not (tmp_path / ".cache").exists()


def test_streamlit_requirements_unchanged_and_no_google_needed_for_local():
    assert "google" not in (REPO / "requirements.txt").read_text(encoding="utf-8")
    src = (REPO / "src" / "cloud" / "data_source_manager.py").read_text(encoding="utf-8")
    assert "import snapshot_loader" in src and "\nfrom src.cloud import snapshot_loader" not in src   # lazy only


# --- snapshot selection + provenance -------------------------------------------------------------------

def test_snapshot_mode_resolves_one_verified_run_and_reports_provenance(tmp_path, published):
    factory = Factory(published[RUN_A])
    m, _ = manager(tmp_path, factory)
    r = m.get()
    assert r.mode == "gcs_snapshot" and r.is_snapshot and r.run_id == RUN_A and r.refresh_ok
    cache = tmp_path / "cache"
    for key in job.UPLOAD_KEYS:
        assert cache in r.config.path(key).parents, key               # every published output is in the snapshot
    for key in ("soilgrids_csv", "irrigation_events_csv", "irrigation_priority_model_path", "ml_model_metrics_json"):
        assert r.config.path(key) == get_config().path(key), key       # existing sources untouched
    rows = dict(dsm.provenance_rows(r))
    assert rows["Data source"] == "Verified GCS snapshot" and rows["Run ID"] == RUN_A
    assert rows["Executed (UTC)"].endswith("Z") and rows["Pipeline status"] == "success"
    assert "SHA-256 + size verified for 21 files" in rows["Integrity"]
    assert "field validated: no" in rows["Validation status"]
    assert "cached" in rows["Satellite: sentinel2"]
    assert any(k.startswith("Input version: soilgrids") for k in rows) and any(k.startswith("Input date:") for k in rows)


def test_integrity_text_never_claims_field_validation():
    assert "not field validation" in dsm.INTEGRITY_NOTE and "surrogate" in dsm.INTEGRITY_NOTE


def test_local_provenance_rows_are_minimal():
    r = dsm.DataSourceManager(get_config(), {}).get()
    assert dsm.provenance_rows(r) == [("Data source", "Local files (default)")]


# --- refresh interval: no GCS traffic on every rerun ---------------------------------------------------------

def test_gcs_is_not_contacted_on_every_rerun(tmp_path, published):
    clock, factory = Clock(), Factory(published[RUN_A])
    m, _ = manager(tmp_path, factory, clock=clock)
    first = m.get()
    for _ in range(25):                                   # 25 reruns inside the interval
        assert m.get() is first
    assert factory.calls == 1
    clock.t += 299
    assert m.get() is first and factory.calls == 1
    clock.t += 2                                          # interval (300 s) elapsed
    m.get()
    assert factory.calls == 2


def test_refresh_interval_is_configurable_and_validated(tmp_path, published):
    clock, factory = Clock(), Factory(published[RUN_A])
    m, _ = manager(tmp_path, factory, {"MANGOTWIN_SNAPSHOT_REFRESH_SECONDS": "120"}, clock=clock)
    m.get(); clock.t += 121; m.get()
    assert factory.calls == 2
    m2, _ = manager(tmp_path / "x", Factory(published[RUN_A]), {"MANGOTWIN_SNAPSHOT_REFRESH_SECONDS": "5"})
    r = m2.get()
    assert r.mode == "local_fallback" and any("must be between" in t for t in texts(r))


def test_new_run_is_picked_up_after_the_interval_and_old_object_stays_coherent(tmp_path, published):
    clock, factory = Clock(), Factory(published[RUN_A])
    m, _ = manager(tmp_path, factory, clock=clock)
    a = m.get()
    path_a = a.config.path("historical_risk_csv")
    factory.objects = published[RUN_B]                    # a new run is published
    assert m.get() is a                                   # same execution window: still run A
    clock.t += 301
    b = m.get()
    assert b.run_id == RUN_B and b is not a
    assert a.run_id == RUN_A and a.config.path("historical_risk_csv") == path_a and path_a.is_file()  # A's view intact
    assert b.config.path("historical_risk_csv") != path_a and RUN_B in str(b.config.path("historical_risk_csv"))


# --- failures: previous snapshot preserved, otherwise local fallback ----------------------------------------------

def test_failed_refresh_keeps_serving_the_previous_verified_snapshot(tmp_path, published):
    clock, factory = Clock(), Factory(published[RUN_A])
    m, _ = manager(tmp_path, factory, clock=clock)
    a = m.get()
    broken = dict(published[RUN_B])
    victim = next(n for n in broken if n.startswith(f"pipeline-runs/{RUN_B}/data/"))
    broken[victim] += b"corrupt"
    factory.objects = broken
    clock.t += 301
    r = m.get()
    assert r.mode == "gcs_snapshot" and r.run_id == RUN_A and not r.refresh_ok
    assert r.config.path("historical_risk_csv") == a.config.path("historical_risk_csv")
    assert any("last verified snapshot" in t for t in texts(r, prominent=True))
    clock.t += 61                                         # failed refreshes retry after 60 s, not 300 s
    factory.objects = published[RUN_B]
    assert m.get().run_id == RUN_B


def test_unavailable_credentials_fall_back_to_local_with_a_visible_warning(tmp_path, published):
    factory = Factory(published[RUN_A])
    factory.error = sl.SnapshotError("No Application Default Credentials available (DefaultCredentialsError).")
    base = get_config()
    m, _ = manager(tmp_path, factory, base=base)
    r = m.get()
    assert r.mode == "local_fallback" and r.config is base and not r.refresh_ok
    prominent = texts(r, prominent=True)
    assert prominent and any("no verified snapshot" in t.lower() for t in prominent)
    assert any("Application Default Credentials" in t for t in texts(r))
    assert r.config.path("historical_risk_csv") == REPO / "data/processed/muthukur_weather_risk_scores.csv"
    assert dict(dsm.provenance_rows(r))["Data source"] == "Local files (snapshot unavailable)"


def test_default_bucket_factory_without_adc_falls_back(tmp_path, monkeypatch):
    def no_adc(*a, **k):
        raise sl.SnapshotError("No Application Default Credentials available")

    monkeypatch.setattr(sl, "open_readonly_bucket", no_adc)
    m = dsm.DataSourceManager(get_config(), {"MANGOTWIN_DATA_SOURCE": "gcs_snapshot",
                                             "MANGOTWIN_SNAPSHOT_DIR": str(tmp_path / "c")})
    assert m.get().mode == "local_fallback"


def test_invalid_mode_value_falls_back_visibly_instead_of_crashing(tmp_path):
    m = dsm.DataSourceManager(get_config(), {"MANGOTWIN_DATA_SOURCE": "gcs", "MANGOTWIN_SNAPSHOT_DIR": str(tmp_path)},
                              lambda s: pytest.fail("must not contact GCS"))
    r = m.get()
    assert r.mode == "local_fallback" and any("Refusing to guess" in t for t in texts(r))


def test_cached_snapshot_is_served_when_gcs_is_down_after_restart(tmp_path, published):
    m1, _ = manager(tmp_path, Factory(published[RUN_A]))
    m1.get()
    down = Factory(published[RUN_A])
    down.error = sl.SnapshotError("network unreachable")
    r = manager(tmp_path, down)[0].get()                  # new process, empty memory, disk cache present
    assert r.mode == "gcs_snapshot" and r.run_id == RUN_A and not r.refresh_ok
    assert any("refresh failed" in t.lower() for t in texts(r, prominent=True))


# --- external dependencies -------------------------------------------------------------------------------------------

class ProxyConfig:
    """Real config, except for chosen keys (used to simulate missing/matching local files)."""

    def __init__(self, base, overrides):
        self._base, self._o = base, overrides

    def path(self, key):
        return self._o.get(key, self._base.path(key))

    def __getattr__(self, name):
        return getattr(self._base, name)


def test_differing_local_irrigation_events_are_reported_not_hidden(tmp_path, published):
    events = tmp_path / "events.csv"
    events.write_bytes(EVENTS + b"2026-09-01,25\n")       # local GitHub-backed copy is newer than the run's input
    base = ProxyConfig(get_config(), {"irrigation_events_csv": events})
    r = manager(tmp_path, Factory(published[RUN_A]), base=base)[0].get()
    warn = [t for t in texts(r, prominent=True) if "Irrigation events" in t]
    assert warn and "differs from the version this run" in warn[0] and RUN_A in warn[0]
    assert not any("matches" in t.lower() for t in texts(r))
    ext = r.provenance["external_dependencies"]["irrigation_events_csv"]
    assert ext["status"] == "differs_from_run_input" and ext["local_sha256"] != ext["run_input_sha256"]


def test_matching_local_inputs_raise_no_warning_but_are_never_called_synchronised(tmp_path, published):
    events, soil = tmp_path / "events.csv", tmp_path / "soil.csv"
    events.write_bytes(EVENTS)
    soil.write_bytes(GOOD_BUCKET["data/raw/muthukur_soilgrids.csv"])
    base = ProxyConfig(get_config(), {"irrigation_events_csv": events, "soilgrids_csv": soil})
    r = manager(tmp_path, Factory(published[RUN_A]), base=base)[0].get()
    assert not [t for t in texts(r, prominent=True) if "differs" in t]
    assert r.provenance["external_dependencies"]["irrigation_events_csv"]["status"] == "matches_run_input"
    assert not any("synchron" in t.lower() for t in texts(r))


def test_missing_local_irrigation_events_and_soil_are_flagged(tmp_path, published):
    base = ProxyConfig(get_config(), {"irrigation_events_csv": tmp_path / "nope.csv", "soilgrids_csv": tmp_path / "nope2.csv"})
    r = manager(tmp_path, Factory(published[RUN_A]), base=base)[0].get()
    prominent = texts(r, prominent=True)
    assert any("Irrigation events" in t and "missing" in t for t in prominent)
    assert any("SoilGrids" in t and "missing" in t for t in prominent)


def test_missing_external_ml_artifacts_are_reported_not_fetched_from_gcs(tmp_path, published):
    missing = {k: tmp_path / f"{k}.absent" for k in dsm.EXTERNAL_ML_KEYS}
    base = ProxyConfig(get_config(), missing)
    r = manager(tmp_path, Factory(published[RUN_A]), base=base)[0].get()
    note = [t for t in texts(r) if t.startswith("Not part of the snapshot and not found locally")]
    assert note and all(k in note[0] for k in dsm.EXTERNAL_ML_KEYS)
    assert not any(k in n for n in published[RUN_A] for k in ("model", ".joblib") if n.endswith(".joblib"))
    assert r.external_artifacts == {k: False for k in dsm.EXTERNAL_ML_KEYS}
    assert r.config.path("irrigation_priority_model_path") == missing["irrigation_priority_model_path"]


def test_ml_artifacts_present_locally_produce_no_missing_notice(tmp_path, published):
    r = manager(tmp_path, Factory(published[RUN_A]))[0].get()
    assert not any("not found locally" in t for t in texts(r))
    assert any("ML artifacts, SoilGrids and irrigation events always come from local files" in t for t in texts(r))


# --- Streamlit caching across run changes -------------------------------------------------------------------------------

def test_st_cache_data_loaders_keyed_by_path_never_serve_an_older_run(tmp_path, published):
    import streamlit as st
    calls = []

    @st.cache_data(show_spinner=False)
    def load(path: Path) -> pd.DataFrame:          # same shape as the dashboard's loaders: keyed by path
        calls.append(str(path))
        return pd.read_csv(path)

    clock, factory = Clock(), Factory(published[RUN_A])
    m, _ = manager(tmp_path, factory, clock=clock)
    a = m.get()
    pa = a.config.path("historical_risk_csv")
    df_a1 = load(pa)
    df_a2 = load(pa)
    assert len(calls) == 1 and df_a1.equals(df_a2)                 # same run: cache hit

    # run B publishes a different file at the same repo-relative path
    objs = dict(published[RUN_B])
    name_b = f"pipeline-runs/{RUN_B}/data/processed/muthukur_weather_risk_scores.csv"
    assert objs[name_b] == published[RUN_A][name_b.replace(RUN_B, RUN_A)]   # fixture content is identical...
    factory.objects = published[RUN_B]
    clock.t += 301
    b = m.get()
    pb = b.config.path("historical_risk_csv")
    assert pa != pb and RUN_A in str(pa) and RUN_B in str(pb)
    load(pb)
    assert calls == [str(pa), str(pb)]                              # ...yet B is a separate cache entry
    load(pa)
    assert len(calls) == 2                                          # and A is still cached for old executions


def test_every_dashboard_loader_is_cached_by_path_argument():
    src = APP.read_text(encoding="utf-8")
    import re
    for m_ in re.finditer(r"@st\.cache_data\s*\ndef (\w+)\(([^)]*)\)", src):
        assert m_.group(2).split(":")[0].strip() == "path", m_.group(1)     # cache key is the (run-specific) path


def test_snapshot_directory_is_immutable_per_run_id(tmp_path, published):
    r = manager(tmp_path, Factory(published[RUN_A]))[0].get()
    assert r.config.path("historical_risk_csv").parent.parent.parent.name == RUN_A   # runs/<run-id>/data/processed


def test_freshness_has_no_mutable_module_global_selection():
    from app.sections import freshness
    src = (REPO / "app" / "sections" / "freshness.py").read_text(encoding="utf-8")
    assert "global " not in src and not hasattr(freshness, "set_metadata_path")
    default = freshness._METADATA_PATH
    assert default == get_config().path("pipeline_run_metadata_json")
    assert freshness.resolve_metadata_path(None, session_state={}) == default            # local default retained
    assert freshness.resolve_metadata_path(None, session_state={freshness.SESSION_METADATA_KEY: ""}) == default


def test_freshness_path_resolution_order():
    from app.sections import freshness
    sess = {freshness.SESSION_METADATA_KEY: "/snap/a/pipeline_run_metadata.json"}
    assert freshness.resolve_metadata_path(None, sess) == Path("/snap/a/pipeline_run_metadata.json")
    assert freshness.resolve_metadata_path(Path("/explicit.json"), sess) == Path("/explicit.json")


def _shown(at):
    return " ".join(str(e.value) for e in list(at.caption) + list(at.markdown) + list(at.info) + list(at.success))


def test_two_sessions_with_different_snapshots_never_see_each_others_metadata(tmp_path):
    """Regression: the footer path used to be a module global shared by every Streamlit session."""
    from app.sections import freshness
    paths = {}
    for name, run_ts in (("A", "2026-11-01T00:00:00Z"), ("B", "2026-11-09T00:00:00Z")):
        d = tmp_path / name
        d.mkdir()
        (d / "pipeline_run_metadata.json").write_text(
            json.dumps({"status": "success", "run_completed_at": run_ts}), encoding="utf-8")
        paths[name] = d / "pipeline_run_metadata.json"

    sessions = {}
    for name in ("A", "B"):
        script = (
            "from pathlib import Path\n"
            "from app.sections import freshness\n"
            f"freshness.select_session_metadata_path(Path({str(paths[name])!r}))\n"
            "freshness.show_freshness_indicator(label='X', staleness_warning_days=0)\n")
        sessions[name] = AppTest.from_string(script, default_timeout=60)
    # interleave runs in one process (shared modules): A, B, A again
    sessions["A"].run()
    sessions["B"].run()
    sessions["A"].run()

    a, b = _shown(sessions["A"]), _shown(sessions["B"])
    assert not sessions["A"].exception and not sessions["B"].exception
    assert "2026-11-01" in a and "2026-11-09" not in a
    assert "2026-11-09" in b and "2026-11-01" not in b
    # neither selection changed shared state: a fresh helper call still resolves to the local default
    assert freshness.resolve_metadata_path(None, session_state={}) == freshness._METADATA_PATH
    # a session that never selected a path keeps reading the original local default
    local = AppTest.from_string(
        "from app.sections import freshness\nfreshness.show_freshness_indicator(label='X', staleness_warning_days=0)\n",
        default_timeout=60)
    local.run()
    assert not local.exception and "2026-11-01" not in _shown(local) and "2026-11-09" not in _shown(local)


def test_explicit_metadata_path_argument_overrides_the_session_selection(tmp_path):
    p = tmp_path / "pipeline_run_metadata.json"
    p.write_text(json.dumps({"status": "success", "run_completed_at": "2026-10-05T00:00:00Z"}), encoding="utf-8")
    at = AppTest.from_string(
        "from pathlib import Path\nfrom app.sections import freshness\n"
        "freshness.select_session_metadata_path(Path('/nonexistent/other.json'))\n"
        f"freshness.show_freshness_indicator(label='X', staleness_warning_days=0, metadata_path=Path({str(p)!r}))\n",
        default_timeout=60)
    at.run()
    assert not at.exception and "2026-10-05" in _shown(at)


def test_app_footer_follows_the_selected_snapshot_metadata(monkeypatch, tmp_path, real_run):
    """The dashboard selects the snapshot's metadata for its footers (same run as the page data)."""
    from app.sections import freshness
    seen = []
    orig = freshness.load_metadata_json

    def spy(path):
        seen.append(str(path).replace("\\", "/"))
        return orig(path)

    monkeypatch.setattr(freshness, "load_metadata_json", spy)
    mgr, _ = manager(tmp_path, Factory(real_run))
    at, _ = run_app(monkeypatch, mgr)
    assert not at.exception and seen
    cache = str(tmp_path / "cache").replace("\\", "/")
    assert all(p.startswith(cache) and p.endswith("pipeline_run_metadata.json") for p in seen), seen


def test_app_in_local_mode_footer_reads_the_local_metadata(monkeypatch):
    from app.sections import freshness
    seen = []
    orig = freshness.load_metadata_json
    monkeypatch.setattr(freshness, "load_metadata_json", lambda p: (seen.append(Path(p)), orig(p))[1])
    at, _ = run_app(monkeypatch, dsm.DataSourceManager(get_config(), {}))
    assert not at.exception and seen and all(p == get_config().path("pipeline_run_metadata_json") for p in seen)


# --- full-dashboard AppTest runs -------------------------------------------------------------------------------------------------

from streamlit.testing.v1 import AppTest  # noqa: E402


def real_published(run_id, events_override: bytes | None = None):
    """A published run built from the repo's actual committed outputs (so the real dashboard can render it)."""
    cfg = get_config()
    objects, outputs, dates = {}, [], {}
    for key in job.UPLOAD_KEYS:
        p = Path(cfg.path(key))
        assert p.is_file(), f"fixture needs {p}"
        data = p.read_bytes()
        rel = p.relative_to(REPO / "data").as_posix()
        obj = publish.run_object_name(rel, run_id)
        objects[obj] = data
        entry = {"key": key, "filename": p.name, "path": f"data/{rel}", "object": obj, "bytes": len(data),
                 "sha256": hashlib.sha256(data).hexdigest(), "md5_base64": publish.md5_b64_of_bytes(data)}
        if p.suffix == ".csv":
            entry["rows"] = max(data.count(b"\n") - 1, 0)
        outputs.append(entry)
    inputs = {}
    for key in ("soilgrids_csv", "irrigation_events_csv"):
        data = Path(cfg.path(key)).read_bytes()
        if key == "irrigation_events_csv" and events_override is not None:
            data = events_override
        inputs[key] = {"object": f"data/{Path(cfg.path(key)).relative_to(REPO / 'data').as_posix()}", "generation": 1,
                       "sha256": hashlib.sha256(data).hexdigest(), "rows": 1, "latest_date": "2026-08-21"}
    manifest = publish.build_manifest(
        run_id=run_id, runs_prefix="pipeline-runs", started_at="2026-11-14T10:00:00Z", executed_at="2026-11-14T10:05:00Z",
        pipeline_status="success", outputs=outputs, skipped_optional=[], inputs=inputs,
        satellite_data={"sentinel2": {"status": "cached", "latest_observation_date": "2026-10-29"}},
        scientific_validation={"status": "integrity_checks_passed_not_field_validated", "field_validated": False},
        runtime={"python": "3.12.1", "libraries": {"pandas": "3.0.3"}},
        irrigation_events={"verified_against_github": False, "authority": "gcs_copy_accepted_unverified"},
        execution={"runner": "cloud-run-job"})
    mb = publish.canonical_json(manifest)
    objects[publish.manifest_object(run_id)] = mb
    objects[LATEST] = publish.canonical_json({
        "schema_version": 1, "run_id": run_id, "manifest_object": publish.manifest_object(run_id),
        "manifest_sha256": hashlib.sha256(mb).hexdigest(), "executed_at": "2026-11-14T10:05:00Z",
        "promoted_at": "2026-11-14T10:05:05Z", "previous_run_id": None})
    return objects


@pytest.fixture(scope="module")
def real_run():
    return real_published(RUN_A)


def run_app(monkeypatch, mgr):
    import streamlit as st
    from app import data_source_ui
    st.cache_data.clear()            # process-wide cache: start every app run cold so file reads are observable
    monkeypatch.setattr(data_source_ui, "_MANAGER", mgr)
    opened: list[str] = []
    orig = pd.read_csv

    def spy(path, *a, **k):
        opened.append(str(path))
        return orig(path, *a, **k)

    monkeypatch.setattr(pd, "read_csv", spy)
    at = AppTest.from_file(str(APP), default_timeout=120)
    at.run()
    return at, opened


def sidebar_text(at):
    parts = [m.value for m in at.sidebar.markdown] + [c.value for c in at.sidebar.caption]
    parts += [e.label for e in at.sidebar.expander]
    return "\n".join(parts)


def test_app_default_local_mode_has_no_snapshot_ui_and_reads_local_files(monkeypatch):
    mgr = dsm.DataSourceManager(get_config(), {}, lambda s: pytest.fail("GCS must not be contacted"))
    at, opened = run_app(monkeypatch, mgr)
    assert not at.exception
    assert "Data source: local files" in sidebar_text(at)
    assert not [w for w in at.warning if "snapshot" in w.value.lower()]
    assert not [e for e in at.sidebar.expander if "Data source" in e.label]
    norm = [o.replace("\\", "/") for o in opened]
    assert any(o.endswith("data/processed/muthukur_weather_risk_scores.csv") for o in norm)


def test_app_snapshot_mode_renders_from_the_snapshot_with_provenance(monkeypatch, tmp_path, real_run):
    mgr, _ = manager(tmp_path, Factory(real_run))
    at, opened = run_app(monkeypatch, mgr)
    assert not at.exception
    labels = [e.label for e in at.sidebar.expander]
    assert any("Data source: GCS snapshot" in lab for lab in labels)
    side = "\n".join(m.value for e in at.sidebar.expander for m in e.markdown)
    assert RUN_A in side and "2026-11-14T10:05:00Z" in side and "SHA-256 + size verified for 21 files" in side
    assert "field validated: no" in side and "cached" in side
    norm = [o.replace("\\", "/") for o in opened]
    cache = str(tmp_path / "cache").replace("\\", "/")
    assert any(o.startswith(cache) and o.endswith("muthukur_weather_risk_scores.csv") for o in norm)    # published output: snapshot
    assert any(o.endswith("data/raw/muthukur_soilgrids.csv") and not o.startswith(cache) for o in norm)  # soil: existing local path
    assert not any(o.startswith(cache) and "soilgrids" in o for o in norm)


def test_app_without_credentials_falls_back_to_local_and_warns(monkeypatch, tmp_path, real_run):
    factory = Factory(real_run)
    factory.error = sl.SnapshotError("No Application Default Credentials available")
    mgr, _ = manager(tmp_path, factory)
    at, opened = run_app(monkeypatch, mgr)
    assert not at.exception
    warns = [w.value for w in at.warning]
    assert any("no verified snapshot" in w.lower() for w in warns)
    assert any("Application Default Credentials" in w for w in warns)
    cache = str(tmp_path / "cache").replace("\\", "/")
    assert not any(o.replace("\\", "/").startswith(cache) for o in opened)
    assert any(o.replace("\\", "/").endswith("data/processed/muthukur_weather_risk_scores.csv") for o in opened)


def test_app_warns_when_local_irrigation_events_differ_from_the_run(monkeypatch, tmp_path):
    run = real_published(RUN_A, events_override=b"date,irrigation_mm\n1999-01-01,1\n")
    mgr, _ = manager(tmp_path, Factory(run))
    at, _ = run_app(monkeypatch, mgr)
    assert not at.exception
    assert any("Irrigation events" in w.value and "differs" in w.value for w in at.warning)


def test_app_keeps_every_existing_page_and_navigation(monkeypatch, tmp_path, real_run):
    from app import navigation as nav
    mgr, _ = manager(tmp_path, Factory(real_run))
    at, _ = run_app(monkeypatch, mgr)
    assert not at.exception
    buttons = [b.label for b in at.sidebar.button]
    for page in nav.all_pages():
        assert any(page in b for b in buttons), page


def test_integration_does_not_touch_irrigation_persistence_or_scientific_code():
    src = APP.read_text(encoding="utf-8")
    assert "data_source = resolve_dashboard_source()" in src and "config = data_source.config" in src
    assert 'IRRIGATION_EVENTS_PATH = config.path("irrigation_events_csv")' in src
    for p in (REPO / "src" / "irrigation").glob("*.py"):
        assert "data_source" not in p.read_text(encoding="utf-8"), p


def _soil_notices(status):
    prov = {"run_id": "R1", "external_dependencies": {"soilgrids_csv": {"status": status}}}
    return [n for n in dsm.build_notices("gcs_snapshot", prov, [], {}, True) if n.text.startswith("SoilGrids soil data:")]


def test_soilgrids_formatting_only_difference_is_not_a_warning():
    (n,) = _soil_notices("formatting_only_difference")
    assert n.level == "info" and not n.prominent and "only in formatting" in n.text


def test_soilgrids_real_difference_and_unconfirmed_comparisons_keep_a_prominent_warning():
    for status in ("differs_from_run_input", "reference_unavailable", "comparison_failed"):
        (n,) = _soil_notices(status)
        assert n.level == "warning" and n.prominent, status
        assert "only in formatting" not in n.text
