"""Regression tests: the dashboard's cached CSV loader must notice when the CSV on disk changes.

Background: a Streamlit Cloud app kept showing the first historical-risk CSV it had loaded after
data-only commits, until the app was rebooted. ``load_data`` is now keyed by (path, file signature).
All files modified here are temp copies; nothing under data/ is touched.
"""

from __future__ import annotations

import ast
import inspect
import os
import re
import shutil
from pathlib import Path

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from app.file_signature import cache_signature, file_signature
from src.cloud import data_source_manager as dsm
from src.utils.config import PROJECT_ROOT, get_config

REPO = Path(PROJECT_ROOT)
APP = REPO / "app" / "streamlit_app.py"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in ("MANGOTWIN_DATA_SOURCE", "MANGOTWIN_SNAPSHOT_DIR", "MANGOTWIN_SNAPSHOT_REFRESH_SECONDS"):
        monkeypatch.delenv(k, raising=False)


# --- helper -----------------------------------------------------------------------------------------------

def test_signature_changes_with_content_and_is_none_for_missing_files(tmp_path):
    p = tmp_path / "a.csv"
    assert file_signature(p) is None
    p.write_text("date,v\n2026-01-01,1\n")
    first = file_signature(p)
    assert first[1] == p.stat().st_size
    p.write_text("date,v\n2026-01-01,1\n2026-01-02,2\n")
    assert file_signature(p) != first


def test_same_size_rewrite_is_still_detected_through_mtime(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("date,v\n2026-01-01,1\n")
    before = file_signature(p)
    p.write_text("date,v\n2026-01-01,9\n")                       # identical size, different content
    os.utime(p, ns=(before[0] + 5_000_000_000, before[0] + 5_000_000_000))
    after = file_signature(p)
    assert after[1] == before[1] and after != before


def test_snapshot_paths_never_get_a_local_file_signature(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("x")
    assert cache_signature(p, is_snapshot=False) == file_signature(p)
    assert cache_signature(p, is_snapshot=True) is None           # immutable run-id path: the path is the key


# --- Streamlit really keys on the signature ----------------------------------------------------------------

def test_loader_shaped_like_the_dashboards_returns_updated_content_after_the_file_changes(tmp_path):
    st.cache_data.clear()
    reads = []

    @st.cache_data(show_spinner=False)
    def load_data(path: Path, signature) -> pd.DataFrame:            # same shape as app/streamlit_app.py
        reads.append(str(path))
        return pd.read_csv(path)

    p = tmp_path / "risk.csv"
    p.write_text("date,v\n2026-11-10,1\n")
    a = load_data(p, file_signature(p))
    assert load_data(p, file_signature(p)).equals(a) and len(reads) == 1      # unchanged file: cache hit

    p.write_text("date,v\n2026-11-10,1\n2026-11-13,2\n")                       # data-only refresh lands
    b = load_data(p, file_signature(p))
    assert len(reads) == 2 and b["date"].tolist() == ["2026-11-10", "2026-11-13"]   # no reboot needed


def test_an_underscore_prefixed_signature_would_NOT_invalidate_the_cache(tmp_path):
    """Documents why the dashboard's parameter is named ``signature``: Streamlit skips ``_``-prefixed args."""
    st.cache_data.clear()

    @st.cache_data(show_spinner=False)
    def bad_load(path: Path, _signature) -> pd.DataFrame:
        return pd.read_csv(path)

    p = tmp_path / "risk.csv"
    p.write_text("date,v\n2026-11-10,1\n")
    bad_load(p, file_signature(p))
    p.write_text("date,v\n2026-11-10,1\n2026-11-13,2\n")
    assert len(bad_load(p, file_signature(p))) == 1                            # stale: the pitfall


def test_dashboard_loader_declares_a_hashed_signature_parameter():
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "load_data")
    names = [a.arg for a in fn.args.args]
    assert names == ["path", "signature"]                                      # first arg still the path
    assert not any(n.startswith("_") for n in names)
    assert any(isinstance(d, ast.Attribute) and d.attr == "cache_data" for d in fn.decorator_list)
    src = APP.read_text(encoding="utf-8")
    assert "load_data(path, cache_signature(path, data_source.is_snapshot))" in src
    assert not re.search(r"load_data\(path\)", src)


# --- the real dashboard, end to end -------------------------------------------------------------------------

class ProxyConfig:
    def __init__(self, base, overrides):
        self._base, self._o = base, overrides

    def path(self, key):
        return self._o.get(key, self._base.path(key))

    def __getattr__(self, name):
        return getattr(self._base, name)


def _run_app(monkeypatch, config, spy_path):
    from app import data_source_ui
    monkeypatch.setattr(data_source_ui, "_MANAGER", dsm.DataSourceManager(config, {}))
    reads: list[str] = []
    orig = pd.read_csv

    def spy(path, *a, **k):
        # count only reads made by the cached dashboard loader (other pages may peek at the same file)
        if str(path) == str(spy_path) and any(f.function == "load_data" for f in inspect.stack()):
            reads.append(str(path))
        return orig(path, *a, **k)

    monkeypatch.setattr(pd, "read_csv", spy)
    at = AppTest.from_file(str(APP), default_timeout=120)
    at.run()
    assert not at.exception, at.exception
    return at, reads


def _page_text(at):
    items = list(at.markdown) + list(at.caption) + list(at.info) + list(at.warning) + list(at.success)
    return " ".join(str(e.value) for e in items) + " " + " ".join(f"{m.label} {m.value}" for m in at.metric)


def test_dashboard_rereads_a_changed_historical_risk_csv_without_a_restart(monkeypatch, tmp_path):
    src = get_config().path("historical_risk_csv")
    local = tmp_path / "muthukur_weather_risk_scores.csv"
    shutil.copy(src, local)                                                   # a temp copy; data/ is never written
    config = ProxyConfig(get_config(), {"historical_risk_csv": local})
    st.cache_data.clear()

    at1, reads1 = _run_app(monkeypatch, config, local)
    assert len(reads1) == 1

    at2, reads2 = _run_app(monkeypatch, config, local)                        # nothing changed: cache hit
    assert reads2 == []

    frame = pd.read_csv(local)
    new_row = frame.iloc[[-1]].copy()
    new_date = (pd.Timestamp(frame["date"].iloc[-1]) + pd.Timedelta(days=3)).strftime("%Y-%m-%d")
    new_row["date"] = new_date
    pd.concat([frame, new_row], ignore_index=True).to_csv(local, index=False)  # the daily refresh lands

    at3, reads3 = _run_app(monkeypatch, config, local)                        # no reboot, no cache clear
    assert len(reads3) == 1                                                   # re-read exactly once
    _, reads4 = _run_app(monkeypatch, config, local)
    assert reads4 == []                                                       # cached again for the new signature


def test_snapshot_mode_does_not_stat_local_files_for_cache_keys(monkeypatch):
    calls = []
    from app import file_signature as fs
    monkeypatch.setattr(fs.os, "stat", lambda *a, **k: calls.append(a) or (_ for _ in ()).throw(AssertionError))
    assert cache_signature("any/run-id/path.csv", is_snapshot=True) is None
    assert calls == []
