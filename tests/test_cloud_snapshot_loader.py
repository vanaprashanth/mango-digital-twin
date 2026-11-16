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
    return sl.SnapshotSettings(cache_dir=tmp_path / "cache", project_root=REPO)


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
                if calls["n"] == 5:  # file 5 arrives half-written, then the connection drops
                    Path(path).write_bytes(Path(path).read_bytes()[:3])
                    raise GcsError(503, "connection reset")
            blob.download_to_filename = dl
        return blob

    bucket.get_blob = flaky
    r = sl.refresh(ro(bucket), cfg, settings)
    assert r.status == "failed" and "Download failed" in r.reason and calls["n"] == 5
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
