"""Tests for src/cloud/run_pipeline_job.py using an in-memory fake bucket.

No network, no GCP credentials, and the real pipeline is never run: the
pipeline runner is injected and writes small fixture outputs instead.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.cloud import run_pipeline_job as job
from src.utils.config import PROJECT_ROOT, get_config

REPO = Path(PROJECT_ROOT)
EVENTS_KEY = "irrigation_events_csv"


# --- fakes -------------------------------------------------------------------

class FakeBlob:
    def __init__(self, store, name):
        self._store, self.name = store, name

    @property
    def generation(self):
        return self._store.gens[self.name]

    @property
    def size(self):
        return len(self._store.objects[self.name])

    def download_to_filename(self, path):
        Path(path).write_bytes(self._store.objects[self.name])

    def download_as_bytes(self, start=0, end=None):
        data = self._store.objects[self.name]
        return data[start:(end + 1) if end is not None else None]

    def upload_from_filename(self, path, if_generation_match=None):
        current = self._store.gens.get(self.name, 0)
        if if_generation_match is not None and if_generation_match != current:
            raise RuntimeError("412 PreconditionFailed")
        self._store.objects[self.name] = Path(path).read_bytes()
        self._store.gens[self.name] = current + 1
        self._store.uploads.append(self.name)


class FakeBucket:
    def __init__(self, objects=None):
        self.objects = dict(objects or {})
        self.gens = {k: 1 for k in self.objects}
        self.uploads = []

    def get_blob(self, name):
        return FakeBlob(self, name) if name in self.objects else None

    def blob(self, name):
        return FakeBlob(self, name)


class FakeConfig:
    """Maps real config path keys into a temp project root."""

    def __init__(self, root):
        self.root, self._real = root, get_config()

    def path(self, key):
        return self.root / Path(self._real.path(key)).relative_to(REPO)


def csv_text(cols, rows=3):
    return ",".join(cols) + "\n" + "\n".join(",".join("1" for _ in cols) for _ in range(rows)) + "\n"


EVENTS = b"date,irrigation_mm\n2026-01-01,20\n"
GOOD_BUCKET = {
    "data/raw/muthukur_soilgrids.csv": csv_text(["a", "b"]).encode(),
    "data/manual/muthukur_irrigation_events.csv": EVENTS,
    "data/processed/muthukur_sentinel2_index_timeseries.csv": csv_text(["date", "ndvi"], 5).encode(),
}


@pytest.fixture
def env(tmp_path):
    cfg = FakeConfig(tmp_path)
    settings = job.JobSettings(project_root=tmp_path, refresh_sentinel2=False, dry_run=False)
    return cfg, settings, tmp_path


def fake_runner(cfg, extra=None, status="success", code=0, touch_events=False, skip=()):
    def runner(settings):
        for key in job.UPLOAD_KEYS:
            if key in skip or key in job.PROTECTED_KEYS:
                continue
            p = cfg.path(key)
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.suffix == ".csv":
                if not p.exists():
                    p.write_text(csv_text(["date", "v"]), encoding="utf-8")
            elif key == "pipeline_run_metadata_json":
                p.write_text(json.dumps({"status": status}), encoding="utf-8")
            else:
                p.write_text("x", encoding="utf-8")
        # a model binary and cache that must never be uploaded
        (settings.project_root / "models").mkdir(exist_ok=True)
        (settings.project_root / "models" / "m.joblib").write_bytes(b"bin")
        if touch_events:
            cfg.path(EVENTS_KEY).write_text("tampered", encoding="utf-8")
        for fn in (extra or []):
            fn()
        return code
    return runner


# --- mapping / config --------------------------------------------------------

def test_object_names_mirror_local_data_paths(env):
    cfg, settings, _ = env
    m = {f.key: f.object_name for f in job.build_file_map(["soilgrids_csv", EVENTS_KEY, "forecast_risk_csv"], cfg, settings)}
    assert m["soilgrids_csv"] == "data/raw/muthukur_soilgrids.csv"
    assert m[EVENTS_KEY] == "data/manual/muthukur_irrigation_events.csv"
    assert m["forecast_risk_csv"] == "data/processed/muthukur_open_meteo_forecast_risk.csv"


def test_every_manifest_key_exists_in_real_config():
    paths = get_config()
    for key in (*job.REQUIRED_INPUT_KEYS, *job.OPTIONAL_INPUT_KEYS, *job.UPLOAD_KEYS):
        assert Path(paths.path(key)), key


def test_allow_list_excludes_models_and_protected_files():
    cfg = get_config()
    for key in job.UPLOAD_KEYS:
        p = str(cfg.path(key)).replace("\\", "/")
        assert "/models/" not in p and not p.endswith((".joblib", ".pkl")), key
        assert "ml_model_metrics" not in key and "backtest" not in key and "audit" not in key
    assert EVENTS_KEY not in job.UPLOAD_KEYS


# --- download ----------------------------------------------------------------

def test_downloads_only_manifest_inputs(env):
    cfg, settings, root = env
    bucket = FakeBucket({**GOOD_BUCKET, "data/processed/unrelated.csv": b"a\n1\n", "other/x.csv": b"a\n1\n"})
    job.download_inputs(bucket, settings, cfg)
    got = sorted(str(p.relative_to(root)).replace("\\", "/") for p in (root / "data").rglob("*") if p.is_file())
    assert got == sorted(k for k in GOOD_BUCKET)


@pytest.mark.parametrize("missing", list(GOOD_BUCKET))
def test_missing_required_input_fails_before_anything_runs(env, missing):
    cfg, settings, root = env
    objs = {k: v for k, v in GOOD_BUCKET.items() if k != missing}
    ran = []
    with pytest.raises(job.JobError, match=re.escape(missing)):
        job.run_job(FakeBucket(objs), settings, cfg, runner=lambda s: ran.append(1) or 0)
    assert not ran and not (root / "data").exists()


def test_optional_inputs_may_be_absent(env):
    cfg, settings, _ = env
    info = job.download_inputs(FakeBucket(GOOD_BUCKET), settings, cfg)
    assert "open_meteo_csv" not in info and "soilgrids_csv" in info


# --- pipeline invocation -----------------------------------------------------

def test_pipeline_command_uses_existing_flags():
    cmd = job.pipeline_command(job.JobSettings(refresh_sentinel2=True))
    assert cmd[1:] == ["main.py", "--skip-soil-fetch", "--refresh-sentinel2"]
    assert job.pipeline_command(job.JobSettings(refresh_sentinel2=False))[1:] == ["main.py", "--skip-soil-fetch"]


def test_main_py_still_supports_those_flags():
    text = (REPO / "src" / "pipeline" / "run_pipeline.py").read_text(encoding="utf-8")
    assert '"--skip-soil-fetch"' in text and '"--refresh-sentinel2"' in text


# --- upload behaviour --------------------------------------------------------

def test_happy_path_uploads_only_allow_listed_outputs(env):
    cfg, settings, _ = env
    bucket = FakeBucket(GOOD_BUCKET)
    result = job.run_job(bucket, settings, cfg, runner=fake_runner(cfg))
    assert result["uploaded"]
    assert set(bucket.uploads) <= {f.object_name for f in job.build_file_map(job.UPLOAD_KEYS, cfg, settings)}
    assert not any("models/" in n or n.endswith(".joblib") for n in bucket.uploads)
    assert "data/manual/muthukur_irrigation_events.csv" not in bucket.uploads
    assert bucket.objects["data/manual/muthukur_irrigation_events.csv"] == EVENTS


def test_nonzero_pipeline_exit_uploads_nothing(env):
    cfg, settings, _ = env
    bucket = FakeBucket(GOOD_BUCKET)
    with pytest.raises(job.JobError, match="status 3"):
        job.run_job(bucket, settings, cfg, runner=fake_runner(cfg, code=3))
    assert bucket.uploads == []


def test_failed_metadata_status_uploads_nothing(env):
    cfg, settings, _ = env
    bucket = FakeBucket(GOOD_BUCKET)
    with pytest.raises(job.JobError, match="status"):
        job.run_job(bucket, settings, cfg, runner=fake_runner(cfg, status="failed"))
    assert bucket.uploads == []


def test_missing_expected_output_uploads_nothing(env):
    cfg, settings, _ = env
    bucket = FakeBucket(GOOD_BUCKET)
    with pytest.raises(job.JobError, match="expected output missing"):
        job.run_job(bucket, settings, cfg, runner=fake_runner(cfg, skip=("combined_feature_table_csv",)))
    assert bucket.uploads == []


def test_modified_irrigation_events_fails_and_uploads_nothing(env):
    cfg, settings, _ = env
    bucket = FakeBucket(GOOD_BUCKET)
    with pytest.raises(job.JobError, match="protected file changed"):
        job.run_job(bucket, settings, cfg, runner=fake_runner(cfg, touch_events=True))
    assert bucket.uploads == [] and bucket.objects["data/manual/muthukur_irrigation_events.csv"] == EVENTS


def test_schema_change_is_rejected_then_allowed_with_flag(env):
    cfg, settings, _ = env
    remote = "data/processed/muthukur_open_meteo_forecast_risk.csv"
    bucket = FakeBucket({**GOOD_BUCKET, remote: csv_text(["date", "OLD_COLUMN"]).encode()})
    with pytest.raises(job.JobError, match="schema changed"):
        job.run_job(bucket, settings, cfg, runner=fake_runner(cfg))
    assert bucket.uploads == []
    settings.allow_schema_change = True
    settings.allow_local_overwrite = True  # same temp dir is reused for the second run
    job.run_job(bucket, settings, cfg, runner=fake_runner(cfg))
    assert remote in bucket.uploads


def test_same_schema_passes_header_check(env):
    cfg, settings, _ = env
    remote = "data/processed/muthukur_open_meteo_forecast_risk.csv"
    bucket = FakeBucket({**GOOD_BUCKET, remote: csv_text(["date", "v"]).encode()})
    job.run_job(bucket, settings, cfg, runner=fake_runner(cfg))
    assert remote in bucket.uploads


def test_shrinking_timeseries_is_rejected(env):
    cfg, settings, _ = env

    def shrink():
        cfg.path("sentinel2_timeseries_csv").write_text(csv_text(["date", "ndvi"], 1), encoding="utf-8")

    settings.refresh_sentinel2 = True
    bucket = FakeBucket(GOOD_BUCKET)
    with pytest.raises(job.JobError, match="shrank"):
        job.run_job(bucket, settings, cfg, runner=fake_runner(cfg, extra=[shrink]))
    assert bucket.uploads == []


def test_empty_output_is_rejected(env):
    cfg, settings, _ = env

    def blank():
        cfg.path("combined_feature_table_csv").write_text("", encoding="utf-8")

    with pytest.raises(job.JobError, match="empty"):
        job.run_job(FakeBucket(GOOD_BUCKET), settings, cfg, runner=fake_runner(cfg, extra=[blank]))


def test_dry_run_uploads_nothing(env):
    cfg, settings, _ = env
    settings.dry_run = True
    bucket = FakeBucket(GOOD_BUCKET)
    result = job.run_job(bucket, settings, cfg, runner=fake_runner(cfg))
    assert bucket.uploads == [] and result["would_upload"]
    assert bucket.objects == dict(GOOD_BUCKET)  # bucket content untouched


def test_concurrent_writer_after_snapshot_is_not_overwritten(env):
    cfg, settings, _ = env
    remote = "data/processed/muthukur_open_meteo_forecast_risk.csv"
    bucket = FakeBucket({**GOOD_BUCKET, remote: csv_text(["date", "v"]).encode()})

    def someone_else_writes():
        bucket.objects[remote] = csv_text(["date", "v"], 4).encode()  # same schema, new generation
        bucket.gens[remote] += 1

    with pytest.raises(job.JobError, match="Upload failed"):
        job.run_job(bucket, settings, cfg, runner=fake_runner(cfg, extra=[someone_else_writes]))
    assert bucket.objects[remote] != cfg.path("forecast_risk_csv").read_bytes()  # their write survived


def test_new_object_created_by_someone_else_is_not_overwritten(env):
    cfg, settings, _ = env
    remote = "data/processed/muthukur_weather_risk_scores.csv"
    bucket = FakeBucket(GOOD_BUCKET)  # absent at snapshot time -> generation 0

    def appears():
        bucket.objects[remote] = b"date,v\n1,1\n"
        bucket.gens[remote] = 7

    with pytest.raises(job.JobError, match="Upload failed"):
        job.run_job(bucket, settings, cfg, runner=fake_runner(cfg, extra=[appears]))


def test_metadata_is_uploaded_last(env):
    cfg, settings, _ = env
    bucket = FakeBucket(GOOD_BUCKET)
    job.run_job(bucket, settings, cfg, runner=fake_runner(cfg))
    assert bucket.uploads[-1] == "data/processed/pipeline_run_metadata.json"


@pytest.mark.parametrize("key,suffix", [(EVENTS_KEY, ".csv")])
def test_upload_guard_refuses_protected_file_even_if_forced(env, key, suffix):
    cfg, settings, _ = env
    fm = job.build_file_map([key], cfg, settings)[0]
    with pytest.raises(job.JobError, match="protected"):
        job.upload_outputs(FakeBucket(), [fm], settings, cfg)


def test_upload_guard_refuses_model_artifacts(env):
    cfg, settings, root = env
    bad = job.FileMap("irrigation_priority_model_path", root / "models" / "m.joblib", "data/models/m.joblib")
    with pytest.raises(job.JobError, match="model"):
        job.upload_outputs(FakeBucket(), [bad], settings, cfg)


# --- exit status / entry point ----------------------------------------------

def test_main_returns_nonzero_on_failure(monkeypatch):
    monkeypatch.setattr(job, "run_job", lambda *a, **k: (_ for _ in ()).throw(job.JobError("boom")))
    fake_storage = SimpleNamespace(Client=lambda: SimpleNamespace(bucket=lambda n: object()))
    monkeypatch.setitem(__import__("sys").modules, "google.cloud.storage", fake_storage)
    monkeypatch.setitem(__import__("sys").modules, "google.cloud", SimpleNamespace(storage=fake_storage))
    assert job.main([]) == 1


def test_main_returns_nonzero_on_unexpected_exception(monkeypatch):
    monkeypatch.setattr(job, "run_job", lambda *a, **k: (_ for _ in ()).throw(ValueError("unexpected")))
    fake_storage = SimpleNamespace(Client=lambda: SimpleNamespace(bucket=lambda n: object()))
    monkeypatch.setitem(__import__("sys").modules, "google.cloud.storage", fake_storage)
    monkeypatch.setitem(__import__("sys").modules, "google.cloud", SimpleNamespace(storage=fake_storage))
    assert job.main([]) == 1


def test_defaults_are_safe_dry_run_with_sentinel_refresh():
    st, _ = job.parse_args([], environ={})
    assert (st.bucket, st.prefix, st.dry_run, st.refresh_sentinel2) == (
        "mango-digital-twin-vsp-data", "data", True, True)


def test_first_test_environment_variables():
    st, _ = job.parse_args([], environ={"MANGOTWIN_DRY_RUN": "true", "MANGOTWIN_REFRESH_SENTINEL2": "false"})
    assert st.dry_run and not st.refresh_sentinel2
    assert job.pipeline_command(st)[1:] == ["main.py", "--skip-soil-fetch"]


def test_upload_requires_explicit_opt_in():
    assert job.parse_args([], environ={"MANGOTWIN_DRY_RUN": "false"})[0].dry_run is False
    assert job.parse_args(["--upload"], environ={})[0].dry_run is False
    assert job.parse_args(["--dry-run"], environ={"MANGOTWIN_DRY_RUN": "false"})[0].dry_run is True


@pytest.mark.parametrize("name", ["MANGOTWIN_DRY_RUN", "MANGOTWIN_REFRESH_SENTINEL2", "MANGOTWIN_ALLOW_LOCAL_OVERWRITE"])
@pytest.mark.parametrize("bad", ["ture", "flase", "2", "maybe"])
def test_unrecognised_boolean_env_values_are_rejected(name, bad):
    with pytest.raises(job.JobError, match="not a recognised boolean"):
        job.parse_args([], environ={name: bad})


def test_main_exits_nonzero_on_typo_in_dry_run_flag(monkeypatch):
    monkeypatch.setenv("MANGOTWIN_DRY_RUN", "ture")
    assert job.main([]) == 1


def test_dry_run_bucket_is_read_only():
    ro = job.ReadOnlyBucket(FakeBucket(GOOD_BUCKET))
    assert ro.get_blob("data/raw/muthukur_soilgrids.csv") is not None
    with pytest.raises(job.JobError, match="read-only"):
        ro.blob("anything")


def test_upload_outputs_refuses_in_dry_run(env):
    cfg, settings, _ = env
    settings.dry_run = True
    with pytest.raises(job.JobError, match="dry run"):
        job.upload_outputs(FakeBucket(), [], settings, cfg)


def test_dry_run_still_fails_nonzero_on_pipeline_and_validation_failures(env):
    cfg, settings, _ = env
    settings.dry_run = True
    settings.allow_local_overwrite = True  # same temp dir is reused for several runs
    with pytest.raises(job.JobError):
        job.run_job(FakeBucket(GOOD_BUCKET), settings, cfg, runner=fake_runner(cfg, code=2))
    with pytest.raises(job.JobError):
        job.run_job(FakeBucket(GOOD_BUCKET), settings, cfg, runner=fake_runner(cfg, status="failed"))
    with pytest.raises(job.JobError, match="protected"):
        job.run_job(FakeBucket(GOOD_BUCKET), settings, cfg, runner=fake_runner(cfg, touch_events=True))


# --- satellite labelling ------------------------------------------------------

def test_cached_satellite_data_is_labelled_cached_not_refreshed(env):
    cfg, settings, _ = env
    settings.dry_run = True
    result = job.run_job(FakeBucket(GOOD_BUCKET), settings, cfg, runner=fake_runner(cfg))
    s2 = result["satellite_data"]["sentinel2"]
    assert s2["status"] == "cached" and s2["rows"] == s2["rows_before"] == 5
    assert "CACHED (not refreshed)" in job.describe_satellite_report(result["satellite_data"])
    meta = json.loads(cfg.path("pipeline_run_metadata_json").read_text(encoding="utf-8"))
    assert meta["cloud_execution"]["satellite_data"]["sentinel2"]["status"] == "cached"
    assert meta["cloud_execution"]["sentinel_refresh_requested"] is False


def test_satellite_change_with_refresh_disabled_fails(env):
    cfg, settings, _ = env

    def modify():
        cfg.path("sentinel2_timeseries_csv").write_text(csv_text(["date", "ndvi"], 9), encoding="utf-8")

    with pytest.raises(job.JobError, match="refresh was disabled"):
        job.run_job(FakeBucket(GOOD_BUCKET), settings, cfg, runner=fake_runner(cfg, extra=[modify]))


def test_refreshed_satellite_data_is_labelled_refreshed(env):
    cfg, settings, _ = env
    settings.refresh_sentinel2 = True
    settings.dry_run = True

    def grow():
        cfg.path("sentinel2_timeseries_csv").write_text(csv_text(["date", "ndvi"], 8), encoding="utf-8")

    refreshed = job.run_job(FakeBucket(GOOD_BUCKET), settings, cfg, runner=fake_runner(cfg, extra=[grow]))
    assert refreshed["satellite_data"]["sentinel2"]["status"] == "refreshed"


def test_unchanged_after_refresh_attempt_is_not_called_refreshed(env):
    cfg, settings, _ = env
    settings.refresh_sentinel2 = True
    settings.dry_run = True
    result = job.run_job(FakeBucket(GOOD_BUCKET), settings, cfg, runner=fake_runner(cfg))
    assert result["satellite_data"]["sentinel2"]["status"] == "unchanged_after_refresh_attempt_using_cached_data"


# --- metadata sanitising ------------------------------------------------------

def test_metadata_paths_are_made_relative_and_versions_recorded(env):
    cfg, settings, root = env
    leak = {
        "status": "success",
        "source_files": {"soil": str(root / "data" / "raw" / "muthukur_soilgrids.csv")},
        "step_results": [{"detail": "raised OSError: " + str(root) + "/data/x.csv missing"}],
    }

    def write_leaky():
        cfg.path("pipeline_run_metadata_json").write_text(json.dumps(leak), encoding="utf-8")

    job.run_job(FakeBucket(GOOD_BUCKET), settings, cfg, runner=fake_runner(cfg, extra=[write_leaky]))
    text = cfg.path("pipeline_run_metadata_json").read_text(encoding="utf-8")
    assert str(root) not in text and not job.scan_for_sensitive(text)
    meta = json.loads(text)
    assert meta["source_files"]["soil"] == "data/raw/muthukur_soilgrids.csv"
    env_info = meta["cloud_execution"]["environment"]
    assert re.fullmatch(r"3\.\d+\.\d+", env_info["python"])
    assert env_info["libraries"]["pandas"] and env_info["libraries"]["numpy"]
    assert "scikit-learn" in env_info["libraries"]


@pytest.mark.parametrize("secret", [
    '{"private_key": "x"}', "-----BEGIN PRIVATE KEY-----", "token: ya29.abcdefghijklmnop",
    "someone@example.com", "AIza" + "a" * 30, "ghp_" + "a" * 30, "password = hunter2",
])
def test_metadata_with_secret_like_content_blocks_upload(env, secret):
    cfg, settings, _ = env

    def write_secret():
        cfg.path("pipeline_run_metadata_json").write_text(
            json.dumps({"status": "success", "note": secret}), encoding="utf-8")

    bucket = FakeBucket(GOOD_BUCKET)
    with pytest.raises(job.JobError, match="sensitive-content scan"):
        job.run_job(bucket, settings, cfg, runner=fake_runner(cfg, extra=[write_secret]))
    assert bucket.uploads == []


def test_unremovable_foreign_local_path_blocks_upload(env):
    cfg, settings, _ = env

    def write_path():
        cfg.path("pipeline_run_metadata_json").write_text(
            json.dumps({"status": "success", "x": "C:\\Users\\someone\\file.csv"}), encoding="utf-8")

    with pytest.raises(job.JobError, match="sensitive-content scan"):
        job.run_job(FakeBucket(GOOD_BUCKET), settings, cfg, runner=fake_runner(cfg, extra=[write_path]))


# --- initial upload restriction -----------------------------------------------

def test_ml_artifacts_are_not_in_upload_allowlist():
    for key in job.EXCLUDED_ML_KEYS:
        assert key not in job.UPLOAD_KEYS
    assert "ml_training_dataset_csv" not in job.UPLOAD_KEYS
    assert "ml_training_dataset_metadata_json" not in job.UPLOAD_KEYS


def test_ml_dataset_and_model_never_uploaded_even_if_produced(env):
    cfg, settings, root = env
    bucket = FakeBucket(GOOD_BUCKET)

    def make_ml():
        for k in ("ml_training_dataset_csv", "ml_training_dataset_metadata_json"):
            p = cfg.path(k)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("a,b\n1,2\n", encoding="utf-8")

    job.run_job(bucket, settings, cfg, runner=fake_runner(cfg, extra=[make_ml]))
    assert not any("ml_" in n or "models" in n for n in bucket.uploads)
    for key in job.EXCLUDED_ML_KEYS:
        fm = job.FileMap(key, cfg.path(key), "data/x")
        with pytest.raises(job.JobError):
            job.assert_uploadable(fm, settings, cfg)


# --- local overwrite guard ----------------------------------------------------

def test_refuses_to_overwrite_existing_local_files(env):
    cfg, settings, root = env
    events = cfg.path(EVENTS_KEY)
    events.parent.mkdir(parents=True)
    events.write_text("my local events", encoding="utf-8")
    with pytest.raises(job.JobError, match="Refusing to overwrite existing local"):
        job.run_job(FakeBucket(GOOD_BUCKET), settings, cfg, runner=fake_runner(cfg))
    assert events.read_text(encoding="utf-8") == "my local events"


# --- inventory ----------------------------------------------------------------

def test_inventory_lists_required_objects_under_data_prefix(env, capsys):
    cfg, settings, _ = env
    inv = job.inventory(settings, cfg)
    assert inv["required"] == [
        "data/raw/muthukur_soilgrids.csv",
        "data/manual/muthukur_irrigation_events.csv",
        "data/processed/muthukur_sentinel2_index_timeseries.csv",
    ]
    assert all(n.startswith("data/") for grp in inv.values() for n in grp)
    assert "data/manual/muthukur_irrigation_events.csv" not in inv["upload"]
    job.print_inventory(settings, cfg)
    assert "gcloud storage ls" in capsys.readouterr().out


def test_every_required_and_optional_input_is_a_tracked_repo_data_file():
    import subprocess
    tracked = set(subprocess.run(["git", "ls-files", "data"], cwd=REPO, capture_output=True, text=True).stdout.split())
    inv = job.inventory(job.JobSettings(), get_config())
    for obj in inv["required"] + inv["optional"]:
        assert obj in tracked, obj


def test_verify_bucket_is_read_only_and_reports_missing(env, capsys):
    cfg, settings, _ = env
    bucket = FakeBucket({k: v for k, v in GOOD_BUCKET.items() if "soilgrids" not in k})
    assert job.verify_bucket(bucket, settings, cfg) == 1
    out = capsys.readouterr().out
    assert "MISSING" in out and bucket.uploads == []
    assert job.verify_bucket(FakeBucket(GOOD_BUCKET), settings, cfg) == 0


def test_print_inventory_cli_needs_no_gcp(capsys):
    assert job.main(["--print-inventory"]) == 0
    assert "REQUIRED (3)" in capsys.readouterr().out


# --- dependency pins ----------------------------------------------------------

def _pin_lines():
    text = (REPO / "requirements-cloud.txt").read_text(encoding="utf-8")
    return [l.strip() for l in text.splitlines() if l.strip() and not l.lstrip().startswith("#")]


def test_cloud_requirements_are_fully_pinned_and_independent():
    lines = _pin_lines()
    assert lines and all(re.fullmatch(r"[A-Za-z0-9_.\-]+==[0-9][0-9A-Za-z.\-+]*", l) for l in lines), lines
    names = {l.split("==")[0].lower() for l in lines}
    assert {"pandas", "numpy", "requests", "pyyaml", "earthengine-api", "google-cloud-storage"} <= names
    assert not names & {"streamlit", "plotly", "pytest"}
    assert not any(l.startswith("-r") for l in lines)


def test_streamlit_requirements_file_is_unchanged_and_unpinned():
    text = (REPO / "requirements.txt").read_text(encoding="utf-8")
    assert "==" not in text and "streamlit" in text and "plotly>=5.24" in text


def test_dockerfile_installs_only_pinned_file():
    text = (REPO / "Dockerfile.pipeline").read_text(encoding="utf-8")
    assert "pip install --no-cache-dir -r requirements-cloud.txt" in text
    assert "requirements.txt" not in text.replace("Streamlit requirements.txt", "")


# --- credential exclusion from build contexts -----------------------------------

def _dockerignore_regex(pat: str) -> "re.Pattern":
    """Translate one .dockerignore pattern: '**/' = any depth, '*' stays inside a
    path segment, '?' = one non-separator char. Anchored at the context root."""
    out, i = [], 0
    while i < len(pat):
        if pat.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pat.startswith("**", i):
            out.append(".*")
            i += 2
        elif pat[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pat[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pat[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def _ignored_by_dockerignore(rel_path: str) -> bool:
    """Last matching rule wins; '!' re-includes; a rule naming a parent dir applies."""
    parts = rel_path.split("/")
    candidates = ["/".join(parts[: i + 1]) for i in range(len(parts))]
    ignored = False
    for raw in (REPO / ".dockerignore").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        negate = line.startswith("!")
        rx = _dockerignore_regex((line[1:] if negate else line).rstrip("/"))
        if any(rx.match(c) for c in candidates):
            ignored = not negate
    return ignored


@pytest.mark.parametrize("path", [
    "elite-list-421616-d961dc95aa2f.json",           # the real credential's name pattern
    "my-project-service-account.json",
    "gcp-credentials.json",
    "deploy/prod-key.json",
    "configs/service_account.json",
    "secrets/id.pem", ".env", "app/.env.local",
    "anything.json",                                  # any top-level json
])
def test_credential_style_files_are_excluded_from_docker_contexts(path):
    assert _ignored_by_dockerignore(path), path


@pytest.mark.parametrize("path", [
    "data/processed/muthukur_ml_model_metrics.json",   # dashboard needs these
    "data/processed/muthukur_ml_backtest_summary.json",
    "configs/config.yaml", "src/cloud/run_pipeline_job.py", "data/raw/muthukur_soilgrids.csv",
])
def test_needed_files_are_not_excluded_from_dashboard_image(path):
    assert not _ignored_by_dockerignore(path), path


def test_real_credential_file_is_gitignored_and_untracked_if_present():
    import subprocess
    present = [p.name for p in REPO.glob("*.json")]
    for name in present:
        ignored = subprocess.run(["git", "check-ignore", "-q", name], cwd=REPO).returncode == 0
        tracked = bool(subprocess.run(["git", "ls-files", name], cwd=REPO, capture_output=True, text=True).stdout.strip())
        assert ignored and not tracked, f"{name}: ignored={ignored} tracked={tracked}"
        assert _ignored_by_dockerignore(name), name


def test_pipeline_dockerfile_copies_only_explicit_directories():
    copies = [l.split()[1] for l in (REPO / "Dockerfile.pipeline").read_text(encoding="utf-8").splitlines()
              if l.startswith("COPY ")]
    assert set(copies) <= {"requirements-cloud.txt", "main.py", "configs", "src"}, copies
    for d in ("configs", "src"):
        leaked = [p for p in (REPO / d).rglob("*.json")] + [p for p in (REPO / d).rglob("*.pem")]
        assert not leaked, leaked


def test_dashboard_dockerfile_copy_context_is_protected_by_dockerignore():
    text = (REPO / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY . ." in text  # reason the .dockerignore rules above matter


def test_job_module_handles_no_secrets_or_streamlit():
    src = (REPO / "src" / "cloud" / "run_pipeline_job.py").read_text(encoding="utf-8")
    assert "streamlit" not in src
    assert not re.search(r"GEE_SERVICE_ACCOUNT_KEY|from_service_account|GOOGLE_APPLICATION_CREDENTIALS|getenv\(\"[A-Z_]*(KEY|TOKEN|SECRET)", src)


# --- container files ---------------------------------------------------------

def test_dockerfile_pipeline_is_python312_pipeline_not_streamlit():
    text = (REPO / "Dockerfile.pipeline").read_text(encoding="utf-8")
    assert "FROM python:3.12" in text
    assert "src.cloud.run_pipeline_job" in text
    assert "streamlit run" not in text.lower() and "EXPOSE" not in text
    assert "COPY data" not in text and "COPY . " not in text and "COPY models" not in text
    assert "google-cloud-storage" in (REPO / "requirements-cloud.txt").read_text(encoding="utf-8")


def test_dockerignore_blocks_credential_files():
    text = (REPO / ".dockerignore").read_text(encoding="utf-8")
    assert "elite-list-*.json" in text and ".env" in text
