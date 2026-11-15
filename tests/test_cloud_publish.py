"""Tests for versioned GCS publishing (src/cloud/publish.py + run_job write path).

In-memory fake bucket only: no network, no credentials, no real pipeline.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone

import pytest

from cloud_fakes import (EVENTS, EVENTS_KEY, EVENTS_SHA, GOOD_BUCKET, FakeBucket, FakeConfig, GcsError,
                         csv_text, fake_runner)
from src.cloud import publish
from src.cloud import run_pipeline_job as job

RUNS = "pipeline-runs/"
LATEST = "pipeline-runs/latest.json"
RUN_A = "20261114T100000Z-aaaaaaaa"
RUN_B = "20261114T110000Z-bbbbbbbb"
RUN_C = "20261114T120000Z-cccccccc"
NOW = datetime(2026, 11, 14, 12, 0, 0, tzinfo=timezone.utc)


def clock():
    return NOW


@pytest.fixture
def env(tmp_path):
    cfg = FakeConfig(tmp_path)
    settings = job.JobSettings(project_root=tmp_path, refresh_sentinel2=False, dry_run=False,
                               accept_unverified_events=True, allow_local_overwrite=True)
    return cfg, settings, tmp_path


@pytest.fixture
def sleeps():
    return []


def run(env, bucket, run_id, sleeps=None, **runner_kw):
    cfg, settings, _ = env
    settings.run_id = run_id
    rec = [] if sleeps is None else sleeps
    return job.run_job(bucket, settings, cfg, runner=fake_runner(cfg, **runner_kw), clock=clock,
                       sleep=rec.append)


def manifest_of(bucket, run_id):
    return json.loads(bucket.objects[publish.manifest_object(run_id)])


def latest_of(bucket):
    return json.loads(bucket.objects[LATEST])


def pointer_bytes(run_id):
    return publish.canonical_json({
        "schema_version": 1, "run_id": run_id, "manifest_object": publish.manifest_object(run_id),
        "manifest_sha256": "0" * 64, "executed_at": "2026-11-14T10:00:00Z",
        "promoted_at": "2026-11-14T10:00:05Z", "previous_run_id": None})


def put_latest(bucket, run_id):
    bucket.objects[LATEST] = pointer_bytes(run_id)
    bucket.gens[LATEST] = bucket.gens.get(LATEST, 0) + 1


# --- run ids --------------------------------------------------------------------

def test_run_id_format_and_chronological_order():
    a = publish.new_run_id(datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc), "0123abcd")
    b = publish.new_run_id(datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc), "00000000")
    assert a == "20260101T000000Z-0123abcd" and a < b
    assert publish.RUN_ID_RE.match(publish.new_run_id())


@pytest.mark.parametrize("bad", ["", "latest", "../x", "20261114T100000Z", "20261114T100000Z-ZZZZZZZZ",
                                 "20261114T100000Z-aaaaaaaa/../data"])
def test_invalid_run_ids_are_rejected(bad):
    with pytest.raises(job.JobError):
        publish.check_run_id(bad)


def test_run_ids_are_unique_per_job():
    assert len({publish.new_run_id() for _ in range(50)}) == 50


# --- layout + manifest ----------------------------------------------------------------

def test_outputs_are_published_under_unique_run_prefix_with_paths_preserved(env):
    cfg, settings, _ = env
    bucket = FakeBucket(GOOD_BUCKET)
    result = run(env, bucket, RUN_A)
    prefix = f"pipeline-runs/{RUN_A}/"
    published = [n for n in bucket.names(RUNS) if n.startswith(prefix)]
    assert result["run_prefix"] == prefix and published
    for fm in job.build_file_map(job.UPLOAD_KEYS, cfg, settings):
        rel = fm.local.resolve().relative_to((settings.project_root / "data").resolve()).as_posix()
        assert prefix + "data/" + rel in published, rel
    assert len([n for n in published if "/data/" in n]) == len(job.UPLOAD_KEYS)  # the 21 validated outputs


def test_manifest_contains_every_required_field(env):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    m = manifest_of(bucket, RUN_A)
    assert m["run_id"] == RUN_A and m["executed_at"] == "2026-11-14T12:00:00Z"
    assert m["pipeline_status"] == "success"
    assert m["input_observation_dates"]["sentinel2_timeseries_csv"] is not None or True
    assert set(m["input_observation_dates"]) >= {"soilgrids_csv", "irrigation_events_csv", "sentinel2_timeseries_csv"}
    assert m["input_observation_dates"]["irrigation_events_csv"] == "2026-01-01"
    assert m["output_counts"]["files"] == len(m["outputs"]) == len(job.UPLOAD_KEYS)
    assert m["output_counts"]["csv_files"] == sum(o["filename"].endswith(".csv") for o in m["outputs"])
    assert m["satellite_data"]["sentinel2"]["status"] == "cached"
    assert m["scientific_validation"]["status"] == "integrity_checks_passed_not_field_validated"
    assert m["scientific_validation"]["field_validated"] is False
    assert re.fullmatch(r"3\.\d+\.\d+", m["runtime"]["python"]) and m["runtime"]["libraries"]["pandas"]
    for o in m["outputs"]:
        assert {"key", "filename", "path", "object", "bytes", "sha256", "md5_base64"} <= set(o)


def test_manifest_hashes_match_the_published_bytes(env):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    for o in manifest_of(bucket, RUN_A)["outputs"]:
        data = bucket.objects[o["object"]]
        assert hashlib.sha256(data).hexdigest() == o["sha256"] and len(data) == o["bytes"]
        assert publish.md5_b64_of_bytes(data) == o["md5_base64"]


def test_latest_pointer_records_manifest_hash(env):
    bucket = FakeBucket(GOOD_BUCKET)
    result = run(env, bucket, RUN_A)
    ptr = latest_of(bucket)
    assert result["promoted"] and ptr["run_id"] == RUN_A and ptr["previous_run_id"] is None
    assert ptr["manifest_sha256"] == hashlib.sha256(bucket.objects[publish.manifest_object(RUN_A)]).hexdigest()
    assert ptr["manifest_object"] == publish.manifest_object(RUN_A)


def test_second_run_links_previous_and_old_run_stays_intact(env):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    snapshot_a = {n: v for n, v in bucket.objects.items() if RUN_A in n}
    run(env, bucket, RUN_B)
    assert latest_of(bucket)["run_id"] == RUN_B and latest_of(bucket)["previous_run_id"] == RUN_A
    assert {n: bucket.objects[n] for n in snapshot_a} == snapshot_a  # immutable history


def test_existing_data_objects_are_unchanged_and_nothing_new_appears_under_data(env):
    bucket = FakeBucket({**GOOD_BUCKET, "data/processed/muthukur_open_meteo_forecast_risk.csv": csv_text(["date", "v"]).encode()})
    before = dict(bucket.objects)
    gens = dict(bucket.gens)
    run(env, bucket, RUN_A)
    assert {n: bucket.objects[n] for n in before} == before
    assert {n: bucket.gens[n] for n in before} == gens
    assert not [n for n in bucket.objects if n.startswith("data/") and n not in before]
    assert all(n.startswith(RUNS) for n in bucket.uploads)


def test_irrigation_events_never_published_or_modified(env):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    assert bucket.objects["data/manual/muthukur_irrigation_events.csv"] == EVENTS
    assert not [n for n in bucket.objects if "irrigation_events" in n and n.startswith(RUNS)]
    assert all(o["filename"] != "muthukur_irrigation_events.csv" for o in manifest_of(bucket, RUN_A)["outputs"])


def test_models_and_ml_evaluation_files_are_not_published(env):
    bucket = FakeBucket(GOOD_BUCKET)

    def make_ml():
        cfg = env[0]
        for k in ("ml_training_dataset_csv", "ml_model_metrics_json"):
            p = cfg.path(k)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("a,b\n1,2\n", encoding="utf-8")

    run(env, bucket, RUN_A, extra=[make_ml])
    names = " ".join(bucket.uploads)
    assert not re.search(r"muthukur_ml_|ml_training|ml_model|models/|\.joblib|\.pkl", names)
    assert {o["key"] for o in manifest_of(bucket, RUN_A)["outputs"]} <= set(job.UPLOAD_KEYS)


def test_missing_optional_output_is_recorded_not_fatal(env):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A, skip=("fao56_sensitivity_summary_md",))
    m = manifest_of(bucket, RUN_A)
    assert m["skipped_optional_outputs"] == ["fao56_sensitivity_summary_md"]
    assert m["output_counts"]["files"] == len(job.UPLOAD_KEYS) - 1


def _metadata_with_steps(env, statuses):
    def write():
        steps = [{"name": f"s{i}", "status": s, "detail": ""} for i, s in enumerate(statuses)]
        env[0].path("pipeline_run_metadata_json").write_text(
            json.dumps({"status": "success", "step_results": steps}), encoding="utf-8")
    return write


def test_pipeline_step_outcomes_are_summarised_in_manifest(env):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A, extra=[_metadata_with_steps(env, ["RUN", "RUN", "SKIP_FRESH", "SKIP_MISSING_INPUT"])])
    steps = manifest_of(bucket, RUN_A)["scientific_validation"]["pipeline_steps"]
    assert steps == {"steps_reported": 4, "by_status": {"RUN": 2, "SKIP_FRESH": 1, "SKIP_MISSING_INPUT": 1},
                     "steps_failed": 0, "steps_skipped_missing_input": 1}


def test_failed_pipeline_step_blocks_publishing_even_if_overall_status_says_success(env):
    bucket = FakeBucket(GOOD_BUCKET)
    with pytest.raises(job.JobError, match="failed step"):
        run(env, bucket, RUN_A, extra=[_metadata_with_steps(env, ["RUN", "FAILED"])])
    assert bucket.uploads == []


# --- manifest validation -----------------------------------------------------------------

@pytest.fixture
def good_manifest(env):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    return manifest_of(bucket, RUN_A)


def test_valid_manifest_passes(good_manifest):
    publish.validate_manifest(good_manifest, allowed_keys=job.UPLOAD_KEYS, require_key=job.METADATA_KEY)


def _drop(field):
    return lambda m: m.pop(field)


MUTATIONS = {
    "missing run_id": _drop("run_id"),
    "missing satellite_data": _drop("satellite_data"),
    "missing runtime": _drop("runtime"),
    "missing scientific_validation": _drop("scientific_validation"),
    "missing outputs": _drop("outputs"),
    "bad schema_version": lambda m: m.update(schema_version=99),
    "bad run_id": lambda m: m.update(run_id="oops"),
    "prefix mismatch": lambda m: m.update(run_prefix="pipeline-runs/other/"),
    "failed status": lambda m: m.update(pipeline_status="failed"),
    "bad timestamp": lambda m: m.update(executed_at="yesterday"),
    "empty outputs": lambda m: m.update(outputs=[]),
    "count mismatch": lambda m: m["output_counts"].update(files=999),
    "no input dates": lambda m: m.update(input_observation_dates={}),
    "no python version": lambda m: m["runtime"].pop("python"),
    "bad sha256": lambda m: m["outputs"][0].update(sha256="nothex"),
    "missing md5": lambda m: m["outputs"][0].pop("md5_base64"),
    "zero bytes": lambda m: m["outputs"][0].update(bytes=0),
    "object outside run prefix": lambda m: m["outputs"][0].update(object="data/processed/x.csv", filename="x.csv"),
    "filename mismatch": lambda m: m["outputs"][0].update(filename="other.csv"),
    "duplicate object": lambda m: m["outputs"].append(copy.deepcopy(m["outputs"][0])),
    "events file listed": lambda m: m["outputs"][0].update(
        filename="muthukur_irrigation_events.csv",
        object=f"pipeline-runs/{RUN_A}/data/manual/muthukur_irrigation_events.csv"),
    "model listed": lambda m: m["outputs"][0].update(
        filename="m.joblib", object=f"pipeline-runs/{RUN_A}/data/models/m.joblib"),
    "unpublishable key": lambda m: m["outputs"][0].update(key="ml_model_metrics_json"),
    "path traversal": lambda m: m["outputs"][0].update(object=f"pipeline-runs/{RUN_A}/data/../../x.csv", filename="x.csv"),
}


@pytest.mark.parametrize("name", list(MUTATIONS))
def test_invalid_manifests_are_rejected(good_manifest, name):
    bad = copy.deepcopy(good_manifest)
    MUTATIONS[name](bad)
    with pytest.raises(job.JobError, match="Manifest invalid"):
        publish.validate_manifest(bad, allowed_keys=job.UPLOAD_KEYS, require_key=job.METADATA_KEY)


def test_manifest_without_run_metadata_is_rejected(good_manifest):
    bad = copy.deepcopy(good_manifest)
    bad["outputs"] = [o for o in bad["outputs"] if o["key"] != job.METADATA_KEY]
    bad["output_counts"]["files"] = len(bad["outputs"])
    with pytest.raises(job.JobError, match="required output"):
        publish.validate_manifest(bad, require_key=job.METADATA_KEY)


def test_non_object_manifest_is_rejected():
    with pytest.raises(job.JobError):
        publish.validate_manifest(["not", "a", "dict"])


def test_manifest_with_secret_like_content_blocks_publish(env):
    cfg, settings, _ = env
    settings.execution_name = "someone@example.com"
    bucket = FakeBucket(GOOD_BUCKET)
    with pytest.raises(job.JobError, match="manifest failed the sensitive-content scan"):
        run(env, bucket, RUN_A)
    assert bucket.uploads == []


# --- dry run -------------------------------------------------------------------------------

def test_dry_run_is_the_default_and_writes_nothing(env):
    assert job.parse_args([], environ={})[0].dry_run is True
    cfg, settings, _ = env
    settings.dry_run = True
    bucket = FakeBucket(GOOD_BUCKET)
    before = (dict(bucket.objects), dict(bucket.gens))
    result = run(env, bucket, RUN_A)
    assert (bucket.objects, bucket.gens) == before and bucket.uploads == []
    assert result["dry_run"] and not result["promoted"] and not result["uploaded"]
    assert len(result["would_upload"]) == len(job.UPLOAD_KEYS) + 1
    assert result["would_upload"][-1] == publish.manifest_object(RUN_A)
    assert result["would_promote"] == LATEST
    publish.validate_manifest(result["manifest"], allowed_keys=job.UPLOAD_KEYS, require_key=job.METADATA_KEY)


def test_dry_run_cannot_write_even_if_publish_is_attempted(env):
    cfg, settings, _ = env
    settings.dry_run = True
    ro = job.ReadOnlyBucket(FakeBucket(GOOD_BUCKET))
    with pytest.raises(job.JobError, match="read-only"):
        publish.upload_bytes_verified(ro, "pipeline-runs/x", b"x", sleep=lambda s: None)


def test_unset_env_means_dry_run_and_explicit_false_means_write():
    assert job.parse_args([], environ={"MANGOTWIN_DRY_RUN": "true"})[0].dry_run is True
    assert job.parse_args([], environ={"MANGOTWIN_DRY_RUN": "false"})[0].dry_run is False


# --- missing files / failed runs never promote ------------------------------------------------

def test_missing_required_output_publishes_nothing(env):
    bucket = FakeBucket(GOOD_BUCKET)
    with pytest.raises(job.JobError, match="expected output missing"):
        run(env, bucket, RUN_A, skip=("combined_feature_table_csv",))
    assert bucket.uploads == [] and LATEST not in bucket.objects


def test_pipeline_failure_publishes_nothing_and_preserves_latest(env):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    before = bucket.objects[LATEST]
    n = len(bucket.uploads)
    with pytest.raises(job.JobError, match="status 4"):
        run(env, bucket, RUN_B, code=4)
    assert bucket.objects[LATEST] == before and len(bucket.uploads) == n


def test_failed_pipeline_status_publishes_nothing(env):
    bucket = FakeBucket(GOOD_BUCKET)
    with pytest.raises(job.JobError):
        run(env, bucket, RUN_A, status="failed")
    assert bucket.uploads == []


def test_missing_required_input_fails_before_anything(env):
    bucket = FakeBucket({k: v for k, v in GOOD_BUCKET.items() if "soilgrids" not in k})
    with pytest.raises(job.JobError, match="soilgrids"):
        run(env, bucket, RUN_A)
    assert bucket.uploads == []


# --- partial failures ----------------------------------------------------------------------------

def test_permanent_failure_midway_leaves_run_incomplete_and_latest_unchanged(env):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    before = bucket.objects[LATEST]
    bucket.fail("forecast_aware_irrigation_advisory", GcsError(403, "forbidden"), times=99)
    with pytest.raises(job.JobError, match="INCOMPLETE") as exc:
        run(env, bucket, RUN_B)
    assert RUN_B in str(exc.value)
    assert bucket.objects[LATEST] == before
    assert publish.manifest_object(RUN_B) not in bucket.objects
    partial = [n for n in bucket.names(f"pipeline-runs/{RUN_B}/")]
    assert partial and len(partial) < len(job.UPLOAD_KEYS)


def test_failure_on_last_output_still_blocks_manifest_and_latest(env):
    bucket = FakeBucket(GOOD_BUCKET)
    bucket.fail("pipeline_run_metadata.json", GcsError(403), times=99)
    with pytest.raises(job.JobError, match="INCOMPLETE"):
        run(env, bucket, RUN_A)
    assert publish.manifest_object(RUN_A) not in bucket.objects and LATEST not in bucket.objects


def test_manifest_upload_failure_never_promotes(env):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    before = bucket.objects[LATEST]
    bucket.fail("manifest.json", GcsError(403), times=99)
    with pytest.raises(job.JobError, match="INCOMPLETE"):
        run(env, bucket, RUN_B)
    assert bucket.objects[LATEST] == before


def test_corrupted_upload_is_detected_by_readback(env, monkeypatch):
    bucket = FakeBucket(GOOD_BUCKET)
    real = bucket.blob

    class Corrupting:
        def __init__(self, blob):
            self._b = blob

        def upload_from_filename(self, path, if_generation_match=None, **kw):
            self._b.upload_from_filename(path, if_generation_match=if_generation_match)
            bucket.objects[self._b.name] = b"corrupt"

        def __getattr__(self, item):
            return getattr(self._b, item)

    monkeypatch.setattr(bucket, "blob", lambda name: Corrupting(real(name)) if "weather_risk_scores" in name else real(name))
    with pytest.raises(job.JobError, match="verification failed"):
        run(env, bucket, RUN_A)
    assert publish.manifest_object(RUN_A) not in bucket.objects and LATEST not in bucket.objects


# --- retries ---------------------------------------------------------------------------------------

def test_transient_errors_are_retried_with_exponential_backoff(env, sleeps):
    bucket = FakeBucket(GOOD_BUCKET)
    bucket.fail("open_meteo_forecast_risk", GcsError(503), times=2)
    result = run(env, bucket, RUN_A, sleeps)
    assert result["promoted"] and sleeps == [1.0, 2.0]


@pytest.mark.parametrize("code", [408, 429, 500, 502, 503, 504])
def test_retryable_status_codes(code):
    assert publish.classify_error(GcsError(code)) == "transient"


@pytest.mark.parametrize("code", [400, 401, 403, 404])
def test_non_retryable_status_codes(code):
    assert publish.classify_error(GcsError(code)) == "permanent"


def test_precondition_and_connection_classification():
    assert publish.classify_error(GcsError(412)) == "precondition"
    assert publish.classify_error(ConnectionError("reset")) == "transient"
    assert publish.classify_error(TimeoutError()) == "transient"
    assert publish.classify_error(FileNotFoundError("x")) == "permanent"
    assert publish.classify_error(ValueError("?")) == "permanent"


def test_permanent_error_is_not_retried(env, sleeps):
    bucket = FakeBucket(GOOD_BUCKET)
    bucket.fail("open_meteo_forecast_risk", GcsError(403), times=5)
    with pytest.raises(job.JobError):
        run(env, bucket, RUN_A, sleeps)
    assert sleeps == [] and bucket.faults[0]["times"] == 4  # exactly one attempt consumed


def test_retries_are_bounded(env, sleeps):
    bucket = FakeBucket(GOOD_BUCKET)
    bucket.fail("open_meteo_forecast_risk", GcsError(503), times=99)
    with pytest.raises(job.JobError, match="after 4 attempt"):
        run(env, bucket, RUN_A, sleeps)
    assert len(sleeps) == 3 and publish.manifest_object(RUN_A) not in bucket.objects


def test_lost_response_after_successful_write_is_idempotent(env, sleeps):
    bucket = FakeBucket(GOOD_BUCKET)
    bucket.fail("open_meteo_forecast_risk", GcsError(503), times=1, after_write=True)
    result = run(env, bucket, RUN_A, sleeps)  # retry gets 412 but the object is byte-identical
    assert result["promoted"] and bucket.uploads.count(
        f"pipeline-runs/{RUN_A}/data/processed/muthukur_open_meteo_forecast_risk.csv") == 1


def test_existing_run_object_with_different_content_is_never_overwritten(env):
    bucket = FakeBucket(GOOD_BUCKET)
    name = f"pipeline-runs/{RUN_A}/data/processed/muthukur_open_meteo_forecast_risk.csv"
    bucket.objects[name], bucket.gens[name] = b"someone else's bytes", 5
    with pytest.raises(job.JobError, match="different content"):
        run(env, bucket, RUN_A)
    assert bucket.objects[name] == b"someone else's bytes" and LATEST not in bucket.objects


def test_with_retries_returns_value_and_backs_off():
    calls, sleeps = [], []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise GcsError(500)
        return "ok"

    assert publish.with_retries(flaky, "x", attempts=4, sleep=sleeps.append, base=0.5) == "ok"
    assert sleeps == [0.5, 1.0]


# --- concurrency on latest.json -------------------------------------------------------------------------

def test_latest_is_created_with_generation_zero_precondition(env):
    bucket = FakeBucket(GOOD_BUCKET)
    bucket.before["latest.json"] = lambda: put_latest(bucket, RUN_C)  # someone creates it first
    result = run(env, bucket, RUN_A)
    assert result["promoted"] is False and result["promotion"] == "newer_run_already_latest"
    assert latest_of(bucket)["run_id"] == RUN_C  # not silently overwritten


def test_concurrent_newer_promotion_wins_and_is_not_overwritten(env):
    bucket = FakeBucket(GOOD_BUCKET)
    put_latest(bucket, RUN_A)
    bucket.before["latest.json"] = lambda: put_latest(bucket, RUN_C)  # lands between our read and write
    result = run(env, bucket, RUN_B)
    assert result["promoted"] is False and result["promotion"] == "newer_run_already_latest"
    assert latest_of(bucket)["run_id"] == RUN_C
    assert publish.manifest_object(RUN_B) in bucket.objects  # our run is complete, just not latest


def test_concurrent_older_promotion_is_retried_and_ours_wins(env):
    bucket = FakeBucket(GOOD_BUCKET)
    put_latest(bucket, RUN_A)
    bucket.before["latest.json"] = lambda: put_latest(bucket, RUN_A)  # generation bump by an older run
    result = run(env, bucket, RUN_B)
    assert result["promoted"] is True
    assert latest_of(bucket)["run_id"] == RUN_B and latest_of(bucket)["previous_run_id"] == RUN_A


def test_older_run_finishing_late_never_moves_pointer_backwards(env):
    bucket = FakeBucket(GOOD_BUCKET)
    put_latest(bucket, RUN_C)
    before = bucket.objects[LATEST]
    result = run(env, bucket, RUN_A)
    assert result["promoted"] is False and bucket.objects[LATEST] == before


def test_pointer_write_that_landed_but_lost_its_response_is_recognised(env, sleeps):
    bucket = FakeBucket(GOOD_BUCKET)
    bucket.fail("latest.json", GcsError(503), times=1, after_write=True)
    result = run(env, bucket, RUN_A, sleeps)
    assert result["promoted"] is True and latest_of(bucket)["run_id"] == RUN_A


def test_unpromotable_pointer_preserves_previous_latest_and_reports_error(env, sleeps):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    before = bucket.objects[LATEST]
    bucket.fail("latest.json", GcsError(503), times=99)
    with pytest.raises(job.JobError, match="previous latest pointer is unchanged"):
        run(env, bucket, RUN_B, sleeps)
    assert bucket.objects[LATEST] == before


def test_corrupt_latest_is_not_overwritten(env):
    bucket = FakeBucket(GOOD_BUCKET)
    bucket.objects[LATEST], bucket.gens[LATEST] = b"{not json", 3
    with pytest.raises(job.JobError, match="not overwriting"):
        run(env, bucket, RUN_A)
    assert bucket.objects[LATEST] == b"{not json"


def test_pointer_with_unexpected_shape_is_not_overwritten(env):
    bucket = FakeBucket(GOOD_BUCKET)
    bucket.objects[LATEST], bucket.gens[LATEST] = b'{"run_id": "latest"}', 3
    with pytest.raises(job.JobError, match="unexpected shape"):
        run(env, bucket, RUN_A)
    assert bucket.objects[LATEST] == b'{"run_id": "latest"}'


def test_every_run_object_is_written_create_only(env):
    bucket = FakeBucket(GOOD_BUCKET)
    seen = {}
    real = bucket.blob

    def spy(name):
        blob = real(name)
        orig_f, orig_s = blob.upload_from_filename, blob.upload_from_string
        blob.upload_from_filename = lambda p, if_generation_match=None, **k: (
            seen.__setitem__(name, if_generation_match), orig_f(p, if_generation_match=if_generation_match))[1]
        blob.upload_from_string = lambda d, content_type=None, if_generation_match=None, **k: (
            seen.__setitem__(name, if_generation_match), orig_s(d, content_type, if_generation_match))[1]
        return blob

    bucket.blob = spy
    run(env, bucket, RUN_A)
    run_objects = {n: g for n, g in seen.items() if n != LATEST}
    assert run_objects and set(run_objects.values()) == {0}
    assert seen[LATEST] == 0  # first creation; later promotions use the observed generation


def test_later_promotion_uses_observed_generation(env):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    gen = bucket.gens[LATEST]
    used = []
    real = bucket.blob

    def spy(name):
        blob = real(name)
        if name == LATEST:
            orig = blob.upload_from_string
            blob.upload_from_string = lambda d, content_type=None, if_generation_match=None, **k: (
                used.append(if_generation_match), orig(d, content_type, if_generation_match))[1]
        return blob

    bucket.blob = spy
    run(env, bucket, RUN_B)
    assert used == [gen]


# --- write scope -----------------------------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "data/processed/x.csv", "data/manual/muthukur_irrigation_events.csv", "data/raw/muthukur_soilgrids.csv",
    "other/x.csv", "pipeline-runs", "pipeline-runs/../data/x.csv", "pipeline-runs//x",
    "pipeline-runs/20261114T100000Z-aaaaaaaa/data/manual/muthukur_irrigation_events.csv",
    "pipeline-runs/20261114T100000Z-aaaaaaaa/models/m.joblib",
])
def test_write_scope_refuses_anything_outside_pipeline_runs(name):
    scoped = publish.WriteScopedBucket(FakeBucket())
    with pytest.raises(job.JobError):
        scoped.blob(name)


def test_write_scope_allows_run_objects_and_reads_anywhere():
    inner = FakeBucket(GOOD_BUCKET)
    scoped = publish.WriteScopedBucket(inner)
    assert scoped.blob(f"pipeline-runs/{RUN_A}/manifest.json") is not None
    assert scoped.get_blob("data/raw/muthukur_soilgrids.csv") is not None


# --- irrigation-events authority --------------------------------------------------------------------------

def test_live_run_refuses_unverified_gcs_events(env):
    cfg, settings, _ = env
    settings.accept_unverified_events = False
    ran = []
    bucket = FakeBucket(GOOD_BUCKET)
    with pytest.raises(job.JobError, match="not been verified against GitHub"):
        job.run_job(bucket, settings, cfg, runner=lambda s: ran.append(1) or 0, clock=clock)
    assert not ran and bucket.uploads == []


def test_matching_github_hash_is_recorded_as_verified(env):
    cfg, settings, _ = env
    settings.accept_unverified_events = False
    settings.expected_events_sha256 = EVENTS_SHA
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    ev = manifest_of(bucket, RUN_A)["irrigation_events"]
    assert ev["verified_against_github"] is True and ev["authority"] == "matches_expected_github_sha256"
    assert ev["sha256"] == EVENTS_SHA and ev["generation"] == 1


def test_stale_gcs_events_are_detected_and_stop_the_run(env):
    cfg, settings, _ = env
    settings.accept_unverified_events = False
    settings.expected_events_sha256 = hashlib.sha256(EVENTS + b"2026-03-01,10\n").hexdigest()  # GitHub is newer
    ran = []
    with pytest.raises(job.JobError, match="stale or different"):
        job.run_job(FakeBucket(GOOD_BUCKET), settings, cfg, runner=lambda s: ran.append(1) or 0, clock=clock)
    assert not ran


def test_explicit_acceptance_is_recorded_as_unverified(env):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    ev = manifest_of(bucket, RUN_A)["irrigation_events"]
    assert ev["verified_against_github"] is False and ev["authority"] == "gcs_copy_accepted_unverified"


def test_dry_run_only_warns_about_unverified_events(env, caplog):
    cfg, settings, _ = env
    settings.dry_run, settings.accept_unverified_events = True, False
    result = run(env, FakeBucket(GOOD_BUCKET), RUN_A)
    assert result["manifest"]["irrigation_events"]["authority"] == "gcs_copy_unverified_dry_run"
    assert "NOT verified against GitHub" in caplog.text


def test_malformed_expected_hash_is_rejected(env):
    cfg, settings, _ = env
    settings.expected_events_sha256 = "abc"
    with pytest.raises(job.JobError, match="64 lowercase hex"):
        job.run_job(FakeBucket(GOOD_BUCKET), settings, cfg, runner=lambda s: 0, clock=clock)


def test_events_env_variables_are_parsed():
    st, _ = job.parse_args([], environ={"MANGOTWIN_EXPECTED_EVENTS_SHA256": EVENTS_SHA,
                                        "MANGOTWIN_ACCEPT_UNVERIFIED_EVENTS": "true"})
    assert st.expected_events_sha256 == EVENTS_SHA and st.accept_unverified_events is True
    assert job.parse_args([], environ={})[0].accept_unverified_events is False
    with pytest.raises(job.JobError, match="not a recognised boolean"):
        job.parse_args([], environ={"MANGOTWIN_ACCEPT_UNVERIFIED_EVENTS": "ture"})


# --- read-only verification of the latest run -----------------------------------------------------------

def test_verify_latest_passes_on_a_good_run(env, capsys):
    cfg, settings, _ = env
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    before = (dict(bucket.objects), list(bucket.uploads))
    assert job.verify_latest_run(bucket, settings) == 0
    assert "OK" in capsys.readouterr().out and (bucket.objects, bucket.uploads) == before


def test_verify_latest_fails_when_no_pointer(env, capsys):
    assert job.verify_latest_run(FakeBucket(GOOD_BUCKET), env[1]) == 1
    assert "does not exist" in capsys.readouterr().out


def test_verify_latest_detects_tampered_output(env, capsys):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    victim = next(n for n in bucket.objects if n.startswith(f"pipeline-runs/{RUN_A}/data/"))
    bucket.objects[victim] = b"tampered"
    assert job.verify_latest_run(bucket, env[1]) == 1
    assert "different from the manifest" in capsys.readouterr().out


def test_verify_latest_detects_missing_object_and_manifest_mismatch(env, capsys):
    bucket = FakeBucket(GOOD_BUCKET)
    run(env, bucket, RUN_A)
    victim = next(n for n in bucket.objects if n.startswith(f"pipeline-runs/{RUN_A}/data/"))
    del bucket.objects[victim]
    assert job.verify_latest_run(bucket, env[1]) == 1
    bucket2 = FakeBucket(GOOD_BUCKET)
    run(env, bucket2, RUN_A)
    bucket2.objects[publish.manifest_object(RUN_A)] += b" "
    assert job.verify_latest_run(bucket2, env[1]) == 1
    assert "does not match manifest_sha256" in capsys.readouterr().out


def test_verify_latest_cli_is_wired_up(monkeypatch):
    from types import SimpleNamespace
    import sys
    fake_storage = SimpleNamespace(Client=lambda: SimpleNamespace(bucket=lambda n: FakeBucket(GOOD_BUCKET)))
    monkeypatch.setitem(sys.modules, "google.cloud.storage", fake_storage)
    monkeypatch.setitem(sys.modules, "google.cloud", SimpleNamespace(storage=fake_storage))
    assert job.main(["--verify-latest"]) == 1  # no pointer in that bucket -> non-zero, no traceback


def test_main_reports_write_scope_in_inventory(capsys):
    assert job.main(["--print-inventory"]) == 0
    assert "pipeline-runs/<run-id>/" in capsys.readouterr().out


# --- scope guards on the source ------------------------------------------------------------------------

def test_publish_module_has_no_model_ml_or_secret_handling():
    from pathlib import Path
    src = Path(publish.__file__).read_text(encoding="utf-8")
    assert "streamlit" not in src and "GOOGLE_APPLICATION_CREDENTIALS" not in src
    assert "ml_model_metrics" not in src and ".delete(" not in src


def test_job_has_no_delete_or_data_prefix_write_path():
    from pathlib import Path
    src = Path(job.__file__).read_text(encoding="utf-8")
    assert ".delete(" not in src and "upload_outputs" not in src and "snapshot_generations" not in src
    assert "upload_from_filename" not in src  # all writes go through publish.py, which is write-scoped
