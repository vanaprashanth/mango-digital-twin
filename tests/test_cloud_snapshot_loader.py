"""Tests for the optional read-only GCS snapshot loader (src/cloud/snapshot_loader.py).

Mocked bucket + local filesystem only. The published runs are produced by the
real publishing code (run_job) against the in-memory fake, so manifests and
pointers have exactly the schema the loader must consume.
"""

from __future__ import annotations

import hashlib
import json
import sys
import types
from pathlib import Path

import pytest

from cloud_fakes import GOOD_BUCKET, FakeBucket, FakeConfig, GcsError, fake_runner
from src.cloud import publish
from src.cloud import run_pipeline_job as job
from src.cloud import snapshot_loader as sl
from src.utils.config import PROJECT_ROOT, Config, get_config

REPO = Path(PROJECT_ROOT)
RUN_A = "20261114T100000Z-aaaaaaaa"
RUN_B = "20261114T110000Z-bbbbbbbb"
LATEST = "pipeline-runs/latest.json"


# --- published fixtures (built once with the real publisher) ---------------------------

@pytest.fixture(scope="module")
def published(tmp_path_factory):
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


def make_bucket(published, rid):
    return FakeBucket(published[rid])


@pytest.fixture
def cfg():
    return get_config()


@pytest.fixture
def settings(tmp_path):
    return sl.SnapshotSettings(cache_dir=tmp_path / "cache", project_root=REPO, sleep=lambda seconds: None)


def ro(bucket):
    return sl.ReadOnlyBucket(bucket)


def active_id(settings):
    a = sl.read_active(settings)
    return None if a is None else a[1]["run_id"]


def repoint(bucket, rid, manifest_bytes):
    """Replace the manifest AND fix the pointer hash, to test manifest-content checks."""
    bucket.objects[publish.manifest_object(rid)] = manifest_bytes
    ptr = json.loads(bucket.objects[LATEST])
    ptr["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
    bucket.objects[LATEST] = publish.canonical_json(ptr)


def no_leftovers(settings):
    staging = settings.cache_dir / "staging"
    assert not staging.exists() or not list(staging.iterdir())


# --- happy path ----------------------------------------------------------------------------

def test_refresh_activates_a_verified_snapshot(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    result = sl.refresh(ro(bucket), cfg, settings)
    assert (result.status, result.run_id) == ("activated", RUN_A)
    run_dir, prov = sl.read_active(settings)
    assert run_dir == settings.cache_dir / "runs" / RUN_A
    assert len(prov["files"]) == len(job.UPLOAD_KEYS) == 21
    for f in prov["files"]:
        data = (run_dir / f["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == f["sha256"] and len(data) == f["bytes"]
    no_leftovers(settings)


def test_files_land_at_paths_taken_from_existing_config_keys(published, cfg, settings):
    sl.refresh(ro(make_bucket(published, RUN_A)), cfg, settings)
    run_dir, prov = sl.read_active(settings)
    for f in prov["files"]:
        assert f["path"] == Path(cfg.path(f["key"])).relative_to(REPO).as_posix()
        assert (run_dir / f["path"]).is_file()


def test_provenance_carries_run_dates_validation_and_input_versions(published, cfg, settings):
    sl.refresh(ro(make_bucket(published, RUN_A)), cfg, settings)
    _, prov = sl.read_active(settings)
    assert prov["run_id"] == RUN_A and prov["executed_at"].endswith("Z") and prov["pipeline_status"] == "success"
    assert prov["satellite_observation"]["sentinel2"]["status"] == "cached"
    assert "latest_observation_date" in prov["satellite_observation"]["sentinel2"]
    assert prov["validation_status"] == "integrity_checks_passed_not_field_validated"
    assert prov["field_validated"] is False
    assert "NOT field validation" in prov["integrity_note"]
    assert set(prov["input_versions"]) >= {"soilgrids_csv", "irrigation_events_csv", "sentinel2_timeseries_csv"}
    assert prov["input_versions"]["irrigation_events_csv"]["generation"] == 1
    assert prov["input_observation_dates"]["irrigation_events_csv"] == "2026-01-01"
    assert prov["irrigation_events_provenance"]["verified_against_github"] is False


def test_loader_uses_only_read_methods(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    wrapped = ro(bucket)
    for attr in ("blob", "upload_from_filename", "delete", "copy_blob"):
        assert not hasattr(wrapped, attr)
    assert not any(hasattr(wrapped.get_blob(LATEST), a) for a in ("upload_from_string", "upload_from_filename", "delete"))
    before = (dict(bucket.objects), dict(bucket.gens))
    sl.refresh(wrapped, cfg, settings)
    assert (bucket.objects, bucket.gens) == before and bucket.uploads == []


def test_second_refresh_is_unchanged_and_downloads_nothing(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    sl.refresh(ro(bucket), cfg, settings)
    calls = []
    orig = sl._ReadOnlyBlob.download_to_filename
    sl._ReadOnlyBlob.download_to_filename = lambda self, p: calls.append(p) or orig(self, p)
    try:
        assert sl.refresh(ro(bucket), cfg, settings).status == "unchanged"
    finally:
        sl._ReadOnlyBlob.download_to_filename = orig
    assert calls == []


# --- pointer / manifest failures -------------------------------------------------------------

def test_missing_pointer(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    del bucket.objects[LATEST]
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "failed" and "not found" in r.reason and sl.read_active(settings) is None


@pytest.mark.parametrize("payload,match", [
    (b"{not json", "unusable"),
    (b'{"run_id": "latest"}', "unusable"),
    (json.dumps({"schema_version": 1, "run_id": RUN_A, "manifest_object": "pipeline-runs/evil/manifest.json",
                 "manifest_sha256": "0" * 64}).encode(), "unusable"),
])
def test_corrupt_or_malformed_pointer(published, cfg, settings, payload, match):
    bucket = make_bucket(published, RUN_A)
    bucket.objects[LATEST] = payload
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "failed" and match in r.reason and sl.read_active(settings) is None


def test_missing_manifest_object(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    del bucket.objects[publish.manifest_object(RUN_A)]
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "failed" and "manifest.json" in r.reason


def test_manifest_hash_mismatch_with_pointer(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    bucket.objects[publish.manifest_object(RUN_A)] += b" "
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "failed" and "does not match latest.json" in r.reason
    assert sl.read_active(settings) is None


def test_manifest_not_json_even_with_matching_hash(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    repoint(bucket, RUN_A, b"<<<not json>>>")
    assert "not valid JSON" in sl.refresh(ro(bucket), cfg, settings).reason


def _tamper(bucket, rid, fn):
    m = json.loads(bucket.objects[publish.manifest_object(rid)])
    fn(m)
    repoint(bucket, rid, publish.canonical_json(m))


@pytest.mark.parametrize("name,fn,match", [
    ("failed status", lambda m: m.update(pipeline_status="failed"), "Manifest invalid"),
    ("no outputs", lambda m: m.update(outputs=[]), "Manifest invalid"),
    ("ml key", lambda m: m["outputs"][0].update(key="ml_model_metrics_json"), "not publishable"),
    ("bad sha", lambda m: m["outputs"][0].update(sha256="xyz"), "sha256"),
    ("run id swap", lambda m: m.update(run_id=RUN_B, run_prefix=f"pipeline-runs/{RUN_B}/"), "Manifest invalid"),
])
def test_invalid_manifest_content_is_rejected(published, cfg, settings, name, fn, match):
    bucket = make_bucket(published, RUN_A)
    _tamper(bucket, RUN_A, fn)
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "failed" and match in r.reason, r.reason
    assert sl.read_active(settings) is None


def test_manifest_path_that_disagrees_with_config_is_rejected(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    _tamper(bucket, RUN_A, lambda m: m["outputs"][0].update(path="data/processed/somewhere_else.csv"))
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "failed" and "differs from config path" in r.reason


def test_manifest_missing_a_required_output_is_rejected(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)

    def drop(m):
        m["outputs"] = [o for o in m["outputs"] if o["key"] != "combined_feature_table_csv"]
        m["output_counts"]["files"] = len(m["outputs"])

    _tamper(bucket, RUN_A, drop)
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "failed" and "combined_feature_table_csv" in r.reason


# --- object-level failures -------------------------------------------------------------------------

def _first_output(bucket, rid):
    return json.loads(bucket.objects[publish.manifest_object(rid)])["outputs"][0]["object"]


def test_missing_data_object(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    victim = _first_output(bucket, RUN_A)
    del bucket.objects[victim]
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "failed" and "not found" in r.reason and victim in r.reason
    assert sl.read_active(settings) is None and not (settings.cache_dir / "runs" / RUN_A).exists()
    no_leftovers(settings)


def test_size_mismatch(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    victim = _first_output(bucket, RUN_A)
    bucket.objects[victim] += b"extra"
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "failed" and "Size mismatch" in r.reason
    no_leftovers(settings)


def test_sha256_mismatch_with_same_size(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    victim = _first_output(bucket, RUN_A)
    data = bytearray(bucket.objects[victim])
    data[0] ^= 0x01
    bucket.objects[victim] = bytes(data)
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "failed" and "SHA-256 mismatch" in r.reason
    assert sl.read_active(settings) is None


def test_download_interrupted_midway_leaves_no_partial_snapshot(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    calls = {"n": 0}
    orig = bucket.get_blob

    def flaky(name):
        blob = orig(name)
        if blob is not None and "/data/" in name:
            real = blob.download_to_filename

            def dl(path):
                calls["n"] += 1
                real(path)
                if calls["n"] >= 5:  # from file 5 on, every attempt arrives half-written, then the connection drops
                    Path(path).write_bytes(Path(path).read_bytes()[:3])
                    raise GcsError(503, "connection reset")
            blob.download_to_filename = dl
        return blob

    bucket.get_blob = flaky
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "failed" and "Download failed for" in r.reason and "4 attempt(s)" in r.reason
    assert calls["n"] == 4 + 4   # four files succeeded; the fifth was attempted 4 times (bounded) and then abandoned
    assert sl.read_active(settings) is None
    assert not (settings.cache_dir / "runs").exists() or not list((settings.cache_dir / "runs").iterdir())
    no_leftovers(settings)


def test_silently_truncated_download_is_caught_by_size(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    orig = bucket.get_blob

    def trunc(name):
        blob = orig(name)
        if blob is not None and name.endswith("weather_risk_scores.csv"):
            real = blob.download_to_filename
            blob.download_to_filename = lambda p: (real(p), Path(p).write_bytes(Path(p).read_bytes()[:10]))[0]
        return blob

    bucket.get_blob = trunc
    assert "Size mismatch" in sl.refresh(ro(bucket), cfg, settings).reason


# --- last verified snapshot is preserved --------------------------------------------------------------

def test_failed_update_preserves_last_verified_snapshot(published, cfg, settings):
    sl.refresh(ro(make_bucket(published, RUN_A)), cfg, settings)
    run_dir, _ = sl.read_active(settings)
    before = {p.relative_to(run_dir).as_posix(): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()}
    bad = make_bucket(published, RUN_B)
    bad.objects[_first_output(bad, RUN_B)] += b"corrupt"
    r = sl.refresh(ro(bad), cfg, settings)
    assert r.status == "failed"
    assert active_id(settings) == RUN_A
    assert {p.relative_to(run_dir).as_posix(): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()} == before
    assert not (settings.cache_dir / "runs" / RUN_B).exists()
    no_leftovers(settings)


def test_failure_while_switching_active_pointer_keeps_old_snapshot(published, cfg, settings, monkeypatch):
    sl.refresh(ro(make_bucket(published, RUN_A)), cfg, settings)
    monkeypatch.setattr(sl, "_atomic_write_json", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))
    r = sl.refresh(ro(make_bucket(published, RUN_B)), cfg, settings)
    assert r.status == "failed"
    monkeypatch.undo()
    assert active_id(settings) == RUN_A


def test_new_snapshot_is_invisible_until_fully_verified(published, cfg, settings):
    sl.refresh(ro(make_bucket(published, RUN_A)), cfg, settings)
    bucket = make_bucket(published, RUN_B)
    seen = []
    orig = bucket.get_blob

    def spy(name):
        blob = orig(name)
        if blob is not None and "/data/" in name:
            real = blob.download_to_filename

            def dl(path):
                seen.append((active_id(settings), sorted(p.name for p in (settings.cache_dir / "runs").iterdir())))
                real(path)
            blob.download_to_filename = dl
        return blob

    bucket.get_blob = spy
    assert sl.refresh(ro(bucket), cfg, settings).status == "activated"
    assert seen and all(a == RUN_A and runs == [RUN_A] for a, runs in seen)  # readers only ever saw run A
    assert active_id(settings) == RUN_B


# --- pointer changes ----------------------------------------------------------------------------------------

def test_new_published_run_replaces_active_without_mixing(published, cfg, settings):
    sl.refresh(ro(make_bucket(published, RUN_A)), cfg, settings)
    r = sl.refresh(ro(make_bucket(published, RUN_B)), cfg, settings)
    assert (r.status, r.run_id) == ("activated", RUN_B)
    run_dir, prov = sl.read_active(settings)
    mB = json.loads(published[RUN_B][publish.manifest_object(RUN_B)])
    by_path = {o["path"]: o["sha256"] for o in mB["outputs"]}
    on_disk = {p.relative_to(run_dir).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in run_dir.rglob("*") if p.is_file() and p.name != sl.PROVENANCE_FILE}
    assert on_disk == by_path  # every file belongs to run B, nothing left over from run A


def test_pointer_moving_during_download_still_activates_one_consistent_run(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    for n, v in published[RUN_B].items():
        if RUN_B in n:
            bucket.objects[n], bucket.gens[n] = v, 1
    orig = bucket.get_blob
    state = {"moved": False}

    def mover(name):
        blob = orig(name)
        if blob is not None and "/data/" in name and not state["moved"]:
            state["moved"] = True
            bucket.objects[LATEST] = published[RUN_B][LATEST]
            bucket.gens[LATEST] += 1
        return blob

    bucket.get_blob = mover
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "activated" and r.run_id == RUN_A and r.superseded_by == RUN_B
    assert sl.refresh(ro(bucket), cfg, settings).run_id == RUN_B  # next refresh picks up the newer run


def test_pointer_swapped_for_wrong_manifest_is_rejected(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    bucket.objects[publish.manifest_object(RUN_A)] = published[RUN_B][publish.manifest_object(RUN_B)]
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "failed" and "does not match latest.json" in r.reason


def test_older_pointer_does_not_downgrade_unless_allowed(published, cfg, settings):
    sl.refresh(ro(make_bucket(published, RUN_B)), cfg, settings)
    r = sl.refresh(ro(make_bucket(published, RUN_A)), cfg, settings)
    assert r.status == "kept_active" and active_id(settings) == RUN_B
    settings.allow_downgrade = True
    assert sl.refresh(ro(make_bucket(published, RUN_A)), cfg, settings).status == "activated"
    assert active_id(settings) == RUN_A


def test_old_runs_are_pruned_but_active_is_kept(published, cfg, settings):
    settings.keep = 1
    sl.refresh(ro(make_bucket(published, RUN_A)), cfg, settings)
    sl.refresh(ro(make_bucket(published, RUN_B)), cfg, settings)
    assert sorted(p.name for p in (settings.cache_dir / "runs").iterdir()) == [RUN_B]


def test_damaged_active_snapshot_is_detected_and_redownloaded(published, cfg, settings):
    bucket = make_bucket(published, RUN_A)
    sl.refresh(ro(bucket), cfg, settings)
    run_dir, prov = sl.read_active(settings)
    (run_dir / prov["files"][0]["path"]).write_bytes(b"bit rot")
    with pytest.raises(sl.SnapshotError, match="failed re-verification"):
        sl.read_active(settings)
    assert sl.refresh(ro(bucket), cfg, settings).status == "activated"   # heals itself
    assert sl.read_active(settings)[1]["run_id"] == RUN_A
    assert any(p.name.startswith("_damaged-") for p in (settings.cache_dir / "runs").iterdir())


# --- fallback + selection ------------------------------------------------------------------------------------------

def test_local_mode_is_the_default_and_touches_nothing(cfg, settings):
    ds = sl.select_data_source(cfg, environ={}, settings=settings)
    assert ds.mode == "local" and ds.config is cfg and ds.provenance is None
    assert not settings.cache_dir.exists()


def test_unknown_data_source_value_is_an_error():
    with pytest.raises(sl.SnapshotError, match="Refusing to guess"):
        sl.data_source_mode({"MANGOTWIN_DATA_SOURCE": "gcs"})


def test_snapshot_mode_serves_verified_snapshot(published, cfg, settings):
    ds = sl.select_data_source(cfg, {"MANGOTWIN_DATA_SOURCE": "gcs_snapshot"}, settings,
                               bucket_factory=lambda s: ro(make_bucket(published, RUN_A)))
    assert ds.mode == "gcs_snapshot" and ds.provenance["run_id"] == RUN_A and not ds.warnings
    p = ds.config.path("historical_risk_csv")
    assert p.is_file() and settings.cache_dir in p.parents


def test_no_credentials_falls_back_to_local_files(cfg, settings):
    def no_adc(_):
        raise sl.SnapshotError("No Application Default Credentials available")
    ds = sl.select_data_source(cfg, {"MANGOTWIN_DATA_SOURCE": "gcs_snapshot"}, settings, bucket_factory=no_adc)
    assert ds.mode == "local_fallback" and ds.config is cfg
    assert any("No Application Default Credentials" in w for w in ds.warnings)
    assert ds.config.path("historical_risk_csv") == REPO / "data/processed/muthukur_weather_risk_scores.csv"


def test_failed_refresh_serves_last_verified_snapshot_not_local_files(published, cfg, settings):
    env = {"MANGOTWIN_DATA_SOURCE": "gcs_snapshot"}
    sl.select_data_source(cfg, env, settings, bucket_factory=lambda s: ro(make_bucket(published, RUN_A)))
    broken = make_bucket(published, RUN_B)
    broken.objects[_first_output(broken, RUN_B)] += b"x"
    ds = sl.select_data_source(cfg, env, settings, bucket_factory=lambda s: ro(broken))
    assert ds.mode == "gcs_snapshot" and ds.provenance["run_id"] == RUN_A
    assert "last verified snapshot" in ds.reason and any("refresh failed" in w for w in ds.warnings)


def test_unreachable_bucket_without_cache_falls_back_to_local(cfg, settings):
    class Down:
        def get_blob(self, name):
            raise GcsError(503, "unavailable")

    ds = sl.select_data_source(cfg, {"MANGOTWIN_DATA_SOURCE": "gcs_snapshot"}, settings, bucket_factory=lambda s: Down())
    assert ds.mode == "local_fallback" and ds.config is cfg and ds.warnings


def test_snapshot_config_never_mixes_sources(published, cfg, settings):
    ds = sl.select_data_source(cfg, {"MANGOTWIN_DATA_SOURCE": "gcs_snapshot"}, settings,
                               bucket_factory=lambda s: ro(make_bucket(published, RUN_A)))
    sc = ds.config
    run_dir = settings.cache_dir / "runs" / RUN_A
    for key in job.UPLOAD_KEYS:      # every published output comes from the single snapshot
        assert run_dir in sc.path(key).parents, key
    for key in ("soilgrids_csv", "irrigation_events_csv", "irrigation_priority_model_path",
                "ml_model_metrics_json", "ml_training_dataset_csv", "ml_feature_importance_csv", "models_dir"):
        assert sc.path(key) == cfg.path(key), key       # existing sources, unchanged
    assert sc.study_area is cfg.study_area             # everything else delegates
    assert sc.provenance["run_id"] == RUN_A


def test_snapshot_config_has_no_per_file_local_fallback(published, cfg, settings):
    sl.refresh(ro(make_bucket(published, RUN_A)), cfg, settings)
    run_dir, prov = sl.read_active(settings)
    sc = sl.SnapshotConfig(cfg, run_dir, prov)
    gone = sc.path("fao56_sensitivity_summary_md")
    gone.unlink()  # even if absent in the snapshot, the path stays inside it (never the local file)
    assert run_dir in sc.path("fao56_sensitivity_summary_md").parents and not sc.path("fao56_sensitivity_summary_md").exists()


def test_config_path_behaviour_is_unchanged_in_local_mode(cfg):
    assert isinstance(cfg, Config)
    assert cfg.path("historical_risk_csv") == REPO / "data" / "processed" / "muthukur_weather_risk_scores.csv"
    assert cfg.path("irrigation_events_csv") == REPO / "data" / "manual" / "muthukur_irrigation_events.csv"


def test_external_dependency_report(tmp_path):
    soil = tmp_path / "soil.csv"
    events = tmp_path / "events.csv"
    soil.write_bytes(b"s")
    events.write_bytes(b"e")

    class C:
        def path(self, k):
            return {"soilgrids_csv": soil, "irrigation_events_csv": events}[k]

    sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731
    manifest = {"inputs": {"soilgrids_csv": {"sha256": sha(b"s"), "generation": 3},
                           "irrigation_events_csv": {"sha256": sha(b"OLD"), "generation": 7}}}
    rep = sl.external_dependency_report(manifest, C())
    assert rep["soilgrids_csv"]["status"] == "matches_run_input"
    assert rep["irrigation_events_csv"]["status"] == "differs_from_run_input"   # GCS copy stale vs GitHub-backed file
    events.unlink()
    assert sl.external_dependency_report(manifest, C())["irrigation_events_csv"]["status"] == "local_file_missing"
    assert sl.external_dependency_report({"inputs": {}}, C())["soilgrids_csv"]["status"] == "not_recorded_in_manifest"
    assert rep["ml_model_and_unpublished_ml_artifacts"]["status"] == "not_versioned_by_snapshot"


def test_provenance_reports_external_dependency_versions(published, cfg, settings):
    sl.refresh(ro(make_bucket(published, RUN_A)), cfg, settings)
    ext = sl.read_active(settings)[1]["external_dependencies"]
    assert set(ext) >= {"soilgrids_csv", "irrigation_events_csv"}
    assert ext["irrigation_events_csv"]["run_input_sha256"]


# --- authentication ----------------------------------------------------------------------------------------------------

def _fake_google(monkeypatch, default):
    google = types.ModuleType("google")
    auth = types.ModuleType("google.auth")
    cloud = types.ModuleType("google.cloud")
    storage = types.ModuleType("google.cloud.storage")
    auth.default = default
    captured = {}

    class Client:
        def __init__(self, credentials=None, project=None):
            captured["credentials"], captured["project"] = credentials, project

        def bucket(self, name):
            return FakeBucket(GOOD_BUCKET)

    storage.Client = Client
    google.auth, google.cloud, cloud.storage = auth, cloud, storage
    for n, m in (("google", google), ("google.auth", auth), ("google.cloud", cloud), ("google.cloud.storage", storage)):
        monkeypatch.setitem(sys.modules, n, m)
    return captured


def test_adc_is_requested_with_the_read_only_scope(monkeypatch):
    seen = {}

    def default(scopes=None):
        seen["scopes"] = scopes
        return "CREDS", "proj"

    captured = _fake_google(monkeypatch, default)
    bucket = sl.open_readonly_bucket()
    assert seen["scopes"] == [sl.READ_ONLY_SCOPE] and captured["credentials"] == "CREDS"
    assert not hasattr(bucket, "blob")


def test_missing_adc_raises_a_clear_error_without_asking_for_keys(monkeypatch):
    def default(scopes=None):
        raise RuntimeError("DefaultCredentialsError")

    _fake_google(monkeypatch, default)
    with pytest.raises(sl.SnapshotError, match="gcloud auth application-default login"):
        sl.open_readonly_bucket()


# --- scope guards ---------------------------------------------------------------------------------------------------------

def test_loader_source_has_no_write_or_key_file_handling():
    src = (REPO / "src" / "cloud" / "snapshot_loader.py").read_text(encoding="utf-8")
    for banned in (".upload_from", ".delete(", "from_service_account", "GOOGLE_APPLICATION_CREDENTIALS",
                   "service_account", "make_public", "allUsers", "streamlit", "bigquery", "aiplatform"):
        assert banned not in src, banned


def test_dashboard_and_production_requirements_are_untouched_by_the_loader():
    for p in (REPO / "app").rglob("*.py"):
        assert "snapshot_loader" not in p.read_text(encoding="utf-8"), p
    assert "google" not in (REPO / "requirements.txt").read_text(encoding="utf-8")
    assert not list((REPO / ".github").rglob("*snapshot*"))


# =============================================================================
# Network resilience: bounded retries, per-request timeouts, generation pinning,
# fresh client sessions (src/cloud/snapshot_loader.py)
# =============================================================================

import errno  # noqa: E402

import requests  # noqa: E402


class _Faults:
    """Per-object fault queue: entries are (exception, side_effect_or_None), consumed in order."""

    def __init__(self):
        self.q: dict[str, list] = {}

    def add(self, name_part, exc, times=1, side_effect=None):
        self.q.setdefault(name_part, []).extend([(exc, side_effect)] * times)

    def take(self, name):
        for part, items in self.q.items():
            if part in name and items:
                return items.pop(0)
        return None


class NetState:
    def __init__(self, objects):
        self.objects = dict(objects)
        self.gens = {k: 1 for k in objects}
        self.get_calls: list[tuple[str, dict]] = []
        self.dl_calls: list[tuple[str, dict]] = []
        self.dl_faults, self.get_faults, self.byte_faults = _Faults(), _Faults(), _Faults()
        self.before_dl: dict[str, callable] = {}
        self.opened = 0
        self.closed = 0

    def dl_count(self, part):
        return sum(1 for n, _ in self.dl_calls if part in n)

    def get_count(self, part):
        return sum(1 for n, _ in self.get_calls if part in n)


class NetBlob:
    def __init__(self, st, name):
        self.st, self.name = st, name

    generation = property(lambda self: self.st.gens[self.name])
    size = property(lambda self: len(self.st.objects[self.name]))

    def download_as_bytes(self, timeout=None, retry=None):
        fault = self.st.byte_faults.take(self.name)
        if fault:
            raise fault[0]
        return self.st.objects[self.name]

    def download_to_filename(self, filename, timeout=None, retry=None, if_generation_match=None, checksum="auto"):
        st = self.st
        st.dl_calls.append((self.name, {"timeout": timeout, "retry": retry, "if_generation_match": if_generation_match}))
        assert not Path(filename).exists(), "an attempt must start without leftovers from the previous one"
        for part, fn in list(st.before_dl.items()):
            if part in self.name:
                st.before_dl.pop(part)()
        data = st.objects[self.name]
        fault = st.dl_faults.take(self.name)
        if fault:
            Path(filename).write_bytes(data[: max(len(data) // 2, 1)])   # half-written file, then the failure
            if fault[1]:
                fault[1]()
            raise fault[0]
        if if_generation_match is not None and st.gens[self.name] != if_generation_match:
            raise GcsError(412, "conditionNotMet")
        Path(filename).write_bytes(data)


class NetInner:
    def __init__(self, st):
        self.st = st

    def get_blob(self, name, timeout=None):
        self.st.get_calls.append((name, {"timeout": timeout}))
        fault = self.st.get_faults.take(name)
        if fault:
            raise fault[0]
        return NetBlob(self.st, name) if name in self.st.objects else None


class NetClient:
    def __init__(self, st):
        self.st = st

    def close(self):
        self.st.closed += 1


def net_bucket(st):
    def factory():
        st.opened += 1
        return NetInner(st), NetClient(st)
    return sl.ReadOnlyBucket(*factory(), factory)


@pytest.fixture
def net(published):
    return NetState(published[RUN_A])


def first_data_object(st):
    return next(n for n in st.objects if "/data/processed/" in n and n.endswith("muthukur_weather_risk_scores.csv"))


def leftovers(settings):
    return [p for p in settings.cache_dir.rglob("*") if p.is_file() and p.name.endswith(".part")]


def api_core():
    return pytest.importorskip("google.api_core.exceptions")


TRANSIENT_FACTORIES = {
    "requests.ReadTimeout": lambda: requests.exceptions.ReadTimeout("Read timed out. (read timeout=60)"),
    "requests.ConnectionError": lambda: requests.exceptions.ConnectionError("HTTPSConnectionPool: Max retries exceeded"),
    "requests.ChunkedEncodingError": lambda: requests.exceptions.ChunkedEncodingError("IncompleteRead"),
    "TimeoutError": lambda: TimeoutError("timed out"),
    "ConnectionResetError": lambda: ConnectionResetError("reset by peer"),
    "HTTP 503": lambda: GcsError(503, "backend error"),
    "HTTP 429": lambda: GcsError(429, "slow down"),
    "HTTP 408": lambda: GcsError(408, "request timeout"),
    "api_core.RetryError (the reported failure)": lambda: api_core().RetryError(
        "Timeout of 120.0s exceeded, last exception: HTTPSConnectionPool(host='storage.googleapis.com', port=443): Read timed out.",
        cause=requests.exceptions.ReadTimeout("Read timed out")),
    "api_core.ServiceUnavailable": lambda: api_core().ServiceUnavailable("503"),
}


# --- transient recovery ---------------------------------------------------------------------------------

@pytest.mark.parametrize("name", list(TRANSIENT_FACTORIES))
def test_transient_download_failure_recovers_with_backoff(published, cfg, settings, net, name):
    sleeps = []
    settings.sleep = sleeps.append
    victim = first_data_object(net)
    net.dl_faults.add(victim, TRANSIENT_FACTORIES[name](), times=2)
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "activated", r.reason
    assert sleeps == [1.0, 2.0] and net.dl_count(victim) == 3
    assert leftovers(settings) == [] and sl.read_active(settings)[1]["run_id"] == RUN_A
    no_leftovers(settings)


def test_pointer_and_manifest_reads_are_retried_too(published, cfg, settings, net):
    net.byte_faults.add("latest.json", requests.exceptions.ReadTimeout("t"), times=2)
    net.get_faults.add("manifest.json", requests.exceptions.ConnectionError("c"), times=1)
    assert sl.refresh(net_bucket(net), cfg, settings).status == "activated"


def test_every_request_carries_explicit_timeouts_and_no_library_retry(published, cfg, settings, net):
    settings.connect_timeout, settings.read_timeout = 7.0, 21.0
    sl.refresh(net_bucket(net), cfg, settings)
    assert net.get_calls and all(kw["timeout"] == (7.0, 21.0) for _, kw in net.get_calls)
    assert len(net.dl_calls) == 21
    assert all(kw["timeout"] == (7.0, 21.0) and kw["retry"] is None for _, kw in net.dl_calls)


# --- retry exhaustion --------------------------------------------------------------------------------------

def test_retry_exhaustion_is_bounded_and_clean(published, cfg, settings, net):
    sleeps = []
    settings.sleep = sleeps.append
    victim = first_data_object(net)
    net.dl_faults.add(victim, requests.exceptions.ReadTimeout("Read timed out"), times=99)
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "failed" and "after 4 attempt(s) [transient]" in r.reason and victim in r.reason
    assert net.dl_count(victim) == 4 and sleeps == [1.0, 2.0, 4.0]
    assert sl.read_active(settings) is None and leftovers(settings) == []
    assert not (settings.cache_dir / "runs").exists() or not list((settings.cache_dir / "runs").iterdir())
    no_leftovers(settings)


def test_attempt_count_is_configurable(published, cfg, settings, net):
    settings.download_attempts = 2
    victim = first_data_object(net)
    net.dl_faults.add(victim, TimeoutError("t"), times=99)
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "failed" and net.dl_count(victim) == 2 and "after 2 attempt(s)" in r.reason
    settings.download_attempts = 1
    net2 = NetState(net.objects)
    net2.dl_faults.add(victim, TimeoutError("t"), times=99)
    assert sl.refresh(net_bucket(net2), cfg, settings).status == "failed" and net2.dl_count(victim) == 1


def test_overall_deadline_stops_retrying(published, cfg, settings, net):
    settings.overall_deadline_seconds = 0.5      # the first backoff (1.0s) would already exceed it
    victim = first_data_object(net)
    net.dl_faults.add(victim, TimeoutError("t"), times=99)
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "failed" and "overall deadline" in r.reason and net.dl_count(victim) == 1


def test_retry_exhaustion_preserves_last_verified_snapshot(published, cfg, settings):
    env_ = {"MANGOTWIN_DATA_SOURCE": "gcs_snapshot"}
    sl.select_data_source(cfg, env_, settings, bucket_factory=lambda s: ro(make_bucket(published, RUN_A)))
    run_dir, _ = sl.read_active(settings)
    before = {p.relative_to(run_dir).as_posix(): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()}
    st = NetState(published[RUN_B])
    st.dl_faults.add(f"pipeline-runs/{RUN_B}/data/processed/muthukur_weather_risk_scores.csv",
                     requests.exceptions.ReadTimeout("t"), times=99)
    ds = sl.select_data_source(cfg, env_, settings, bucket_factory=lambda s: net_bucket(st))
    assert ds.mode == "gcs_snapshot" and ds.provenance["run_id"] == RUN_A
    assert any("refresh failed" in w.lower() for w in ds.warnings)
    assert {p.relative_to(run_dir).as_posix(): p.read_bytes() for p in run_dir.rglob("*") if p.is_file()} == before
    assert not (settings.cache_dir / "runs" / RUN_B).exists() and leftovers(settings) == []
    no_leftovers(settings)


# --- non-transient failures are NOT retried ----------------------------------------------------------------------

class DataCorruption(Exception):
    """Same class name as google.resumable_media.DataCorruption (checksum mismatch during download)."""


PERMANENT_FACTORIES = {
    "HTTP 403": lambda: GcsError(403, "forbidden"),
    "HTTP 401": lambda: GcsError(401, "unauthenticated"),
    "HTTP 404": lambda: GcsError(404, "not found"),
    "HTTP 400": lambda: GcsError(400, "bad request"),
    "api_core.Forbidden": lambda: api_core().Forbidden("denied"),
    "auth RefreshError name": lambda: type("RefreshError", (Exception,), {})("token refresh failed"),
    "DataCorruption (library checksum)": lambda: DataCorruption("md5/crc32c mismatch"),
    "disk full": lambda: OSError(errno.ENOSPC, "No space left on device"),
    "bug": lambda: ValueError("unexpected"),
}


@pytest.mark.parametrize("name", list(PERMANENT_FACTORIES))
def test_non_transient_errors_are_not_retried(published, cfg, settings, net, name):
    sleeps = []
    settings.sleep = sleeps.append
    victim = first_data_object(net)
    net.dl_faults.add(victim, PERMANENT_FACTORIES[name](), times=99)
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "failed" and "not retried" in r.reason, r.reason
    assert net.dl_count(victim) == 1 and sleeps == [] and leftovers(settings) == []
    assert sl.read_active(settings) is None


def test_auth_failure_message_points_at_adc_not_keys(published, cfg, settings, net):
    net.get_faults.add("latest.json", GcsError(403, "forbidden"))
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "failed" and "Application Default Credentials" in r.reason and "key" not in r.reason.lower().replace("keys", "")
    assert net.get_count("latest.json") == 1


def test_checksum_mismatch_is_not_retried(published, cfg, settings, net):
    victim = first_data_object(net)
    data = bytearray(net.objects[victim])
    data[0] ^= 0x01
    net.objects[victim] = bytes(data)
    sleeps = []
    settings.sleep = sleeps.append
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "failed" and "SHA-256 mismatch" in r.reason
    assert net.dl_count(victim) == 1 and sleeps == [] and leftovers(settings) == []


def test_size_mismatch_is_detected_from_metadata_without_downloading(published, cfg, settings, net):
    victim = first_data_object(net)
    net.objects[victim] += b"x"
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "failed" and "Size mismatch" in r.reason and net.dl_count(victim) == 0


def test_missing_object_and_invalid_manifest_are_not_retried(published, cfg, settings, net):
    sleeps = []
    settings.sleep = sleeps.append
    victim = first_data_object(net)
    del net.objects[victim]
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "failed" and "not found" in r.reason and net.get_count(victim) == 1 and sleeps == []

    st2 = NetState(published[RUN_A])
    manifest_name = publish.manifest_object(RUN_A)
    bad = json.loads(st2.objects[manifest_name])
    bad["pipeline_status"] = "failed"
    repoint_state(st2, RUN_A, publish.canonical_json(bad))
    r2 = sl.refresh(net_bucket(st2), cfg, settings)
    assert r2.status == "failed" and "Manifest invalid" in r2.reason
    assert st2.get_count("manifest.json") == 1 and sleeps == []


def repoint_state(st, rid, manifest_bytes):
    st.objects[publish.manifest_object(rid)] = manifest_bytes
    ptr = json.loads(st.objects[LATEST])
    ptr["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
    st.objects[LATEST] = publish.canonical_json(ptr)


def test_missing_required_output_is_not_retried(published, cfg, settings, net):
    m = json.loads(net.objects[publish.manifest_object(RUN_A)])
    m["outputs"] = [o for o in m["outputs"] if o["key"] != "combined_feature_table_csv"]
    m["output_counts"]["files"] = len(m["outputs"])
    repoint_state(net, RUN_A, publish.canonical_json(m))
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "failed" and "combined_feature_table_csv" in r.reason and not net.dl_calls


# --- generation pinning ------------------------------------------------------------------------------------------------

def test_downloads_are_pinned_to_the_observed_generation(published, cfg, settings, net):
    for name in list(net.gens):
        net.gens[name] = 1000 + len(name)             # distinct, realistic-looking generations
    sl.refresh(net_bucket(net), cfg, settings)
    assert len(net.dl_calls) == 21
    for name, kw in net.dl_calls:
        assert kw["if_generation_match"] == net.gens[name], name


def test_object_replaced_between_metadata_and_download_is_rejected(published, cfg, settings, net):
    sleeps = []
    settings.sleep = sleeps.append
    victim = first_data_object(net)

    def replace():
        net.objects[victim] = b"a different object written in between"
        net.gens[victim] += 1

    net.before_dl[victim] = replace
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "failed" and "replaced" in r.reason and "not retried" in r.reason
    assert net.dl_count(victim) == 1 and sleeps == [] and sl.read_active(settings) is None
    assert leftovers(settings) == []


def test_object_replaced_between_attempts_is_rejected(published, cfg, settings, net):
    victim = first_data_object(net)

    def replace():
        net.gens[victim] += 1                         # same bytes, new generation: still not the object we pinned

    net.dl_faults.add(victim, requests.exceptions.ReadTimeout("t"), times=1, side_effect=replace)
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "failed" and "replaced between download attempts" in r.reason
    assert net.dl_count(victim) == 1 and sl.read_active(settings) is None


def test_manifest_declared_generation_is_enforced_when_present(published, cfg, settings, net):
    m = json.loads(net.objects[publish.manifest_object(RUN_A)])
    m["outputs"][0]["generation"] = 99
    repoint_state(net, RUN_A, publish.canonical_json(m))
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "failed" and "manifest generation 99" in r.reason

    ok = NetState(published[RUN_A])
    m2 = json.loads(ok.objects[publish.manifest_object(RUN_A)])
    for o in m2["outputs"]:
        o["generation"] = ok.gens[o["object"]]
    repoint_state(ok, RUN_A, publish.canonical_json(m2))
    assert sl.refresh(net_bucket(ok), cfg, settings).status == "activated"


@pytest.mark.parametrize("bad", [0, -3, "7", True, 1.5])
def test_malformed_manifest_generation_is_rejected(published, cfg, settings, net, bad):
    m = json.loads(net.objects[publish.manifest_object(RUN_A)])
    m["outputs"][0]["generation"] = bad
    repoint_state(net, RUN_A, publish.canonical_json(m))
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "failed" and "not a positive integer" in r.reason and not net.dl_calls


# --- partial files ---------------------------------------------------------------------------------------------------------------

def test_partial_downloads_never_survive_retries_or_success(published, cfg, settings, net):
    victim = first_data_object(net)
    net.dl_faults.add(victim, requests.exceptions.ReadTimeout("t"), times=3)   # the fake asserts a clean start each attempt
    r = sl.refresh(net_bucket(net), cfg, settings)
    assert r.status == "activated" and leftovers(settings) == []
    run_dir, prov = sl.read_active(settings)
    assert sl.verify_snapshot_dir(run_dir)["run_id"] == RUN_A
    assert not [p for p in run_dir.rglob("*") if p.suffix == ".part"]


# --- client / session lifetime --------------------------------------------------------------------------------------------------

def test_each_request_uses_a_fresh_client_that_is_closed(published, cfg, settings, net):
    sl.refresh(net_bucket(net), cfg, settings)
    requests_made = 2 + 21 + 1                          # pointer + manifest + 21 outputs + post-activation pointer check
    assert net.opened - 1 == requests_made              # minus the long-lived base bucket
    assert net.closed == requests_made


def test_failed_attempts_also_close_their_clients(published, cfg, settings, net):
    net.dl_faults.add(first_data_object(net), TimeoutError("t"), times=2)
    sl.refresh(net_bucket(net), cfg, settings)
    assert net.closed == net.opened - 1 == 2 + 21 + 1 + 2   # incl. the 2 failed attempts


def test_fresh_clients_can_be_disabled(published, cfg, settings, net):
    settings.fresh_client_per_request = False
    assert sl.refresh(net_bucket(net), cfg, settings).status == "activated"
    assert net.opened == 1 and net.closed == 0


def test_close_errors_never_mask_the_result(published, cfg, settings, net):
    class BadClose(NetClient):
        def close(self):
            raise RuntimeError("close failed")

    def factory():
        net.opened += 1
        return NetInner(net), BadClose(net)

    assert sl.refresh(sl.ReadOnlyBucket(*factory(), factory), cfg, settings).status == "activated"


def test_open_readonly_bucket_builds_fresh_clients_from_one_set_of_adc(monkeypatch):
    created, closed, default_calls = [], [], []

    def default(scopes=None):
        default_calls.append(scopes)
        return "CREDS", "proj"

    _fake_google(monkeypatch, default)
    import google.cloud.storage as fake_storage

    class Client:
        def __init__(self, credentials=None, project=None):
            created.append((credentials, project))

        def bucket(self, name):
            return FakeBucket(GOOD_BUCKET)

        def close(self):
            closed.append(1)

    monkeypatch.setattr(fake_storage, "Client", Client)
    bucket = sl.open_readonly_bucket()
    fresh = bucket.fresh()
    assert fresh is not bucket and len(created) == 2 and default_calls == [[sl.READ_ONLY_SCOPE]]
    assert {c for c, _ in created} == {"CREDS"}           # same ADC, new client/session each time
    fresh.close()
    assert closed == [1]
    assert sl.ReadOnlyBucket(FakeBucket(GOOD_BUCKET)).fresh() is not None   # no factory: no-op, still usable


# --- backward compatibility + classification -----------------------------------------------------------------------------------

def test_call_supported_filters_unsupported_keywords():
    def legacy(path):
        return path

    def modern(path, timeout=None, retry=0, if_generation_match=None):
        return (path, timeout, retry, if_generation_match)

    def generic(path, **kw):
        return kw

    assert sl.call_supported(legacy, "p", timeout=1, retry=None, if_generation_match=3) == "p"
    assert sl.call_supported(modern, "p", timeout=1, retry=None, if_generation_match=3) == ("p", 1, None, 3)
    assert sl.call_supported(generic, "p", timeout=1) == {"timeout": 1}


def test_legacy_fakes_without_new_keywords_still_work(published, cfg, settings):
    assert sl.refresh(ro(make_bucket(published, RUN_A)), cfg, settings).status == "activated"


@pytest.mark.parametrize("exc,expected", [
    (requests.exceptions.ReadTimeout("t"), "transient"),
    (requests.exceptions.ConnectionError("c"), "transient"),
    (TimeoutError(), "transient"),
    (GcsError(500), "transient"), (GcsError(503), "transient"), (GcsError(429), "transient"),
    (GcsError(412), "replaced"), (GcsError(401), "auth"), (GcsError(403), "auth"),
    (GcsError(404), "permanent"), (GcsError(400), "permanent"),
    (DataCorruption("x"), "permanent"), (OSError(errno.ENOSPC, "full"), "permanent"),
    (ValueError("x"), "permanent"), (sl.SnapshotError("x"), "permanent"),
])
def test_error_classification(exc, expected):
    assert sl.classify_download_error(exc) == expected


def test_network_settings_from_environment():
    s = sl.settings_from_env({})
    assert (s.download_attempts, s.connect_timeout, s.read_timeout, s.fresh_client_per_request) == (4, 10.0, 30.0, True)
    s = sl.settings_from_env({"MANGOTWIN_SNAPSHOT_DOWNLOAD_ATTEMPTS": "6", "MANGOTWIN_SNAPSHOT_CONNECT_TIMEOUT_SECONDS": "5",
                              "MANGOTWIN_SNAPSHOT_READ_TIMEOUT_SECONDS": "45.5", "MANGOTWIN_SNAPSHOT_DEADLINE_SECONDS": "120",
                              "MANGOTWIN_SNAPSHOT_FRESH_CLIENT": "false"})
    assert (s.download_attempts, s.connect_timeout, s.read_timeout, s.overall_deadline_seconds, s.fresh_client_per_request) == (6, 5.0, 45.5, 120.0, False)


@pytest.mark.parametrize("name,value", [
    ("MANGOTWIN_SNAPSHOT_DOWNLOAD_ATTEMPTS", "0"), ("MANGOTWIN_SNAPSHOT_DOWNLOAD_ATTEMPTS", "99"),
    ("MANGOTWIN_SNAPSHOT_DOWNLOAD_ATTEMPTS", "three"), ("MANGOTWIN_SNAPSHOT_READ_TIMEOUT_SECONDS", "-1"),
    ("MANGOTWIN_SNAPSHOT_CONNECT_TIMEOUT_SECONDS", "abc"), ("MANGOTWIN_SNAPSHOT_FRESH_CLIENT", "maybe"),
])
def test_bad_network_settings_are_rejected(name, value):
    with pytest.raises(sl.SnapshotError, match="Refusing to guess|must be between"):
        sl.settings_from_env({name: value})


def test_loader_uses_only_public_client_apis():
    src = (REPO / "src" / "cloud" / "snapshot_loader.py").read_text(encoding="utf-8")
    assert "._http" not in src and "_http." not in src and "AuthorizedSession" not in src
    assert ".close()" in src and "if_generation_match" in src and "retry=None" in src
