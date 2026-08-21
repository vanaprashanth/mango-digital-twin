"""
tests/test_irrigation_persistence.py

Tests for src/irrigation/persistence.py — the read-only persistence-mode
status layer for irrigation event recording.

This module never writes anything and never contacts GitHub; these tests
only check the pure status/explanation logic.

Test inventory
--------------
1. get_irrigation_persistence_mode: defaults to "local_csv" when config is None
2. get_irrigation_persistence_mode: defaults to "local_csv" when key is absent
3. get_irrigation_persistence_mode: reads an explicit valid mode from a dict
4. get_irrigation_persistence_mode: reads an explicit valid mode from a Config-like object (_raw)
5. get_irrigation_persistence_mode: unknown/invalid mode falls back to "local_csv"
6. is_github_persistence_enabled: False when mode is local_csv (default)
7. is_github_persistence_enabled: False when mode is github_csv but no credentials
8. is_github_persistence_enabled: True when mode is github_csv and env credentials present
9. is_github_persistence_enabled: True when mode is github_csv and config-provided credentials present
10. is_github_persistence_enabled: False when mode is database
11. explain_persistence_mode: returns non-empty text for each valid mode
12. explain_persistence_mode: unknown mode returns an "unsupported" explanation, does not raise
13. persistence_mode_label: known modes get friendly labels
14. Dashboard import (app.sections.irrigation_events) still works after persistence wiring
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.irrigation.persistence import (
    DEFAULT_PERSISTENCE_MODE,
    VALID_PERSISTENCE_MODES,
    explain_persistence_mode,
    get_irrigation_persistence_mode,
    is_github_persistence_enabled,
    persistence_mode_label,
)


class _FakeConfig:
    """Mimics src.utils.config.Config's private `_raw` dict attribute."""

    def __init__(self, raw: dict):
        self._raw = raw


# ---------------------------------------------------------------------------
# get_irrigation_persistence_mode
# ---------------------------------------------------------------------------

def test_mode_defaults_to_local_csv_when_config_is_none():
    assert get_irrigation_persistence_mode(None) == "local_csv"
    assert DEFAULT_PERSISTENCE_MODE == "local_csv"


def test_mode_defaults_to_local_csv_when_key_absent():
    assert get_irrigation_persistence_mode({}) == "local_csv"
    assert get_irrigation_persistence_mode({"some_other_key": 1}) == "local_csv"


def test_mode_reads_explicit_valid_value_from_dict():
    assert get_irrigation_persistence_mode({"irrigation_persistence_mode": "github_csv"}) == "github_csv"
    assert get_irrigation_persistence_mode({"irrigation_persistence_mode": "database"}) == "database"
    assert get_irrigation_persistence_mode({"irrigation_persistence_mode": "local_csv"}) == "local_csv"


def test_mode_reads_from_config_like_object_with_raw_dict():
    cfg = _FakeConfig({"irrigation_persistence_mode": "database"})
    assert get_irrigation_persistence_mode(cfg) == "database"


def test_mode_falls_back_safely_on_unknown_value():
    assert get_irrigation_persistence_mode({"irrigation_persistence_mode": "smoke_signal"}) == "local_csv"
    assert get_irrigation_persistence_mode({"irrigation_persistence_mode": 123}) == "local_csv"
    assert get_irrigation_persistence_mode({"irrigation_persistence_mode": None}) == "local_csv"


# ---------------------------------------------------------------------------
# is_github_persistence_enabled
# ---------------------------------------------------------------------------

def test_github_disabled_when_mode_is_local_csv():
    assert is_github_persistence_enabled({"irrigation_persistence_mode": "local_csv"}) is False
    assert is_github_persistence_enabled(None) is False


def test_github_disabled_when_mode_is_github_csv_but_no_credentials(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPO", raising=False)
    assert is_github_persistence_enabled({"irrigation_persistence_mode": "github_csv"}) is False


def test_github_enabled_with_env_credentials(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_REPO", "someuser/somerepo")
    assert is_github_persistence_enabled({"irrigation_persistence_mode": "github_csv"}) is True


def test_github_enabled_with_config_provided_credentials(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPO", raising=False)
    cfg = {
        "irrigation_persistence_mode": "github_csv",
        "github": {"token": "cfg-token", "repo": "someuser/somerepo"},
    }
    assert is_github_persistence_enabled(cfg) is True


def test_github_disabled_when_mode_is_database(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_REPO", "someuser/somerepo")
    assert is_github_persistence_enabled({"irrigation_persistence_mode": "database"}) is False


# ---------------------------------------------------------------------------
# explain_persistence_mode
# ---------------------------------------------------------------------------

def test_explain_returns_nonempty_text_for_every_valid_mode():
    for mode in VALID_PERSISTENCE_MODES:
        text = explain_persistence_mode(mode)
        assert isinstance(text, str)
        assert len(text) > 20


def test_explain_unknown_mode_does_not_raise_and_mentions_unsupported():
    text = explain_persistence_mode("carrier_pigeon")
    assert isinstance(text, str)
    assert "carrier_pigeon" in text
    assert "local_csv" in text  # notes the fallback behavior


# ---------------------------------------------------------------------------
# persistence_mode_label
# ---------------------------------------------------------------------------

def test_labels_for_known_modes():
    assert persistence_mode_label("local_csv") == "Local CSV"
    assert persistence_mode_label("github_csv") == "GitHub-backed CSV"
    assert persistence_mode_label("database") == "Database"


# ---------------------------------------------------------------------------
# Dashboard import
# ---------------------------------------------------------------------------

def test_dashboard_import_still_works():
    mod = importlib.import_module("app.sections.irrigation_events")
    assert hasattr(mod, "render_irrigation_events_page")
    assert callable(mod.render_irrigation_events_page)
