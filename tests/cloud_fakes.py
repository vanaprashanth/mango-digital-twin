"""In-memory fakes shared by the Cloud Run job tests. No network, no GCP."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from src.cloud import run_pipeline_job as job
from src.utils.config import PROJECT_ROOT, get_config

REPO = Path(PROJECT_ROOT)
EVENTS_KEY = "irrigation_events_csv"


class GcsError(Exception):
    """Stand-in for google.api_core exceptions: carries an HTTP status in .code."""

    def __init__(self, code, msg=""):
        super().__init__(f"{code} {msg}")
        self.code = code


class FakeBlob:
    def __init__(self, store, name):
        self._store, self.name = store, name

    @property
    def generation(self):
        return self._store.gens[self.name]

    @property
    def size(self):
        return len(self._store.objects[self.name])

    @property
    def md5_hash(self):
        return base64.b64encode(hashlib.md5(self._store.objects[self.name]).digest()).decode()

    def download_to_filename(self, path):
        Path(path).write_bytes(self._store.objects[self.name])

    def download_as_bytes(self, start=0, end=None):
        data = self._store.objects[self.name]
        return data[start:(end + 1) if end is not None else None]

    def _write(self, data, if_generation_match):
        st = self._store
        st.fire_before(self.name)
        fault = st.take_fault(self.name, after_write=False)
        if fault:
            raise fault
        current = st.gens.get(self.name, 0)
        if if_generation_match is not None and if_generation_match != current:
            raise GcsError(412, "PreconditionFailed")
        st.objects[self.name] = data
        st.gens[self.name] = current + 1
        st.uploads.append(self.name)
        fault = st.take_fault(self.name, after_write=True)  # response lost AFTER the write landed
        if fault:
            raise fault

    def upload_from_filename(self, path, if_generation_match=None, **_):
        self._write(Path(path).read_bytes(), if_generation_match)

    def upload_from_string(self, data, content_type=None, if_generation_match=None, **_):
        self._write(data.encode() if isinstance(data, str) else bytes(data), if_generation_match)


class FakeBucket:
    def __init__(self, objects=None):
        self.objects = dict(objects or {})
        self.gens = {k: 1 for k in self.objects}
        self.uploads: list[str] = []
        self.faults: list[dict] = []
        self.before: dict[str, callable] = {}
        self.get_blob_faults: list[dict] = []

    # fault injection ---------------------------------------------------------
    def fail(self, name_contains, exc, times=1, after_write=False):
        self.faults.append({"match": name_contains, "exc": exc, "times": times, "after": after_write})

    def fail_reads(self, name_contains, exc, times=1):
        self.get_blob_faults.append({"match": name_contains, "exc": exc, "times": times})

    def take_fault(self, name, after_write):
        for f in self.faults:
            if f["match"] in name and f["after"] == after_write and f["times"] > 0:
                f["times"] -= 1
                return f["exc"]
        return None

    def fire_before(self, name):
        for key in list(self.before):
            if key in name:
                self.before.pop(key)()

    # bucket API --------------------------------------------------------------
    def get_blob(self, name):
        for f in self.get_blob_faults:
            if f["match"] in name and f["times"] > 0:
                f["times"] -= 1
                raise f["exc"]
        return FakeBlob(self, name) if name in self.objects else None

    def blob(self, name):
        return FakeBlob(self, name)

    # helpers -----------------------------------------------------------------
    def names(self, prefix=""):
        return sorted(n for n in self.objects if n.startswith(prefix))


class FakeConfig:
    """Maps real config path keys into a temp project root."""

    def __init__(self, root):
        self.root, self._real = root, get_config()

    def path(self, key):
        return self.root / Path(self._real.path(key)).relative_to(REPO)


def csv_text(cols, rows=3):
    return ",".join(cols) + "\n" + "\n".join(",".join("1" for _ in cols) for _ in range(rows)) + "\n"


EVENTS = b"date,irrigation_mm\n2026-01-01,20\n"
EVENTS_SHA = hashlib.sha256(EVENTS).hexdigest()
GOOD_BUCKET = {
    "data/raw/muthukur_soilgrids.csv": csv_text(["a", "b"]).encode(),
    "data/manual/muthukur_irrigation_events.csv": EVENTS,
    "data/processed/muthukur_sentinel2_index_timeseries.csv": csv_text(["date", "ndvi"], 5).encode(),
}


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


def run_prefix_objects(bucket, runs_prefix="pipeline-runs"):
    return [n for n in bucket.names(runs_prefix + "/")]
