"""
tests/test_github_persistence.py

Tests for the optional GitHub-backed irrigation event persistence layer:
  - src/irrigation/persistence.py::get_github_persistence_settings
  - src/irrigation/github_persistence.py::append_irrigation_event_github
  - src/irrigation/github_persistence.py::build_irrigation_event_row

All GitHub API calls are mocked — these tests never make real network
requests. `requests.get` / `requests.put` are patched inside
src.irrigation.github_persistence.

Test inventory
--------------
1. get_github_persistence_settings: disabled when mode is local_csv
2. get_github_persistence_settings: enabled only when mode is github_csv AND
   token + repo are both present (env vars); disabled if either is missing
3. append_irrigation_event_github: appending to existing CSV content
   preserves the header and all existing rows, and adds exactly one new row
4. append_irrigation_event_github: a missing GitHub file (404) results in a
   new file containing header + the new event only
5. append_irrigation_event_github / build_irrigation_event_row: negative
   irrigation_mm is rejected with ValueError BEFORE any network call
6. append_irrigation_event_github / build_irrigation_event_row: an invalid
   date is rejected with ValueError BEFORE any network call
7. append_irrigation_event_github: a GitHub API failure (non-2xx) returns
   a safe {"success": False, ...} dict that never contains the token
8. Dashboard import (app.sections.irrigation_events) still works
"""

from __future__ import annotations

import base64
import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.irrigation.github_persistence import (
    append_irrigation_event_github,
    build_irrigation_event_row,
)
from src.irrigation.persistence import get_github_persistence_settings

_FAKE_TOKEN = "ghp_super_secret_token_do_not_leak_1234567890"
_FAKE_REPO = "vanaprashanth/mango-digital-twin"
_FAKE_BRANCH = "master"
_FAKE_CSV_PATH = "data/manual/muthukur_irrigation_events.csv"


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def _mock_response(status_code: int, json_data: dict | None = None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


# ---------------------------------------------------------------------------
# get_github_persistence_settings
# ---------------------------------------------------------------------------

def test_settings_disabled_when_mode_is_local_csv(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", _FAKE_TOKEN)
    monkeypatch.setenv("GITHUB_REPO", _FAKE_REPO)
    settings = get_github_persistence_settings({"irrigation_persistence_mode": "local_csv"})
    assert settings["enabled"] is False


def test_settings_enabled_only_when_mode_and_credentials_present(monkeypatch):
    # Missing token -> disabled
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_REPO", _FAKE_REPO)
    settings = get_github_persistence_settings({"irrigation_persistence_mode": "github_csv"})
    assert settings["enabled"] is False
    assert settings["token_present"] is False

    # Missing repo -> disabled
    monkeypatch.setenv("GITHUB_TOKEN", _FAKE_TOKEN)
    monkeypatch.delenv("GITHUB_REPO", raising=False)
    settings = get_github_persistence_settings({"irrigation_persistence_mode": "github_csv"})
    assert settings["enabled"] is False
    assert settings["repo"] is None

    # Both present -> enabled
    monkeypatch.setenv("GITHUB_TOKEN", _FAKE_TOKEN)
    monkeypatch.setenv("GITHUB_REPO", _FAKE_REPO)
    settings = get_github_persistence_settings({"irrigation_persistence_mode": "github_csv"})
    assert settings["enabled"] is True
    assert settings["repo"] == _FAKE_REPO
    assert settings["token_present"] is True
    # Token value itself must never appear in the settings dict
    assert _FAKE_TOKEN not in str(settings.values())


def test_settings_branch_defaults_to_master(monkeypatch):
    monkeypatch.delenv("GITHUB_BRANCH", raising=False)
    settings = get_github_persistence_settings({"irrigation_persistence_mode": "github_csv"})
    assert settings["branch"] == "master"


# ---------------------------------------------------------------------------
# append_irrigation_event_github — success paths
# ---------------------------------------------------------------------------

def test_append_preserves_header_and_existing_rows():
    existing_csv = (
        "date,irrigation_mm,method,source,notes\n"
        "2025-03-10,25.0,drip,farmer,valid row\n"
    )
    get_resp = _mock_response(
        200,
        {"content": _b64(existing_csv), "sha": "abc123"},
    )
    put_resp = _mock_response(
        201,
        {"commit": {"html_url": "https://github.com/vanaprashanth/mango-digital-twin/commit/deadbeef"}},
    )

    with patch("src.irrigation.github_persistence.requests.get", return_value=get_resp) as mock_get, \
         patch("src.irrigation.github_persistence.requests.put", return_value=put_resp) as mock_put:
        result = append_irrigation_event_github(
            repo=_FAKE_REPO,
            branch=_FAKE_BRANCH,
            token=_FAKE_TOKEN,
            csv_path=_FAKE_CSV_PATH,
            event={
                "date": "2025-05-01",
                "irrigation_mm": 15.0,
                "method": "sprinkler",
                "source": "user_dashboard",
                "notes": "second event",
            },
        )

    assert result["success"] is True
    assert result["mode"] == "github_csv"
    assert result["commit_url"].endswith("deadbeef")

    mock_get.assert_called_once()
    mock_put.assert_called_once()

    # Inspect the committed content
    put_kwargs = mock_put.call_args.kwargs
    committed_b64 = put_kwargs["json"]["content"]
    committed_text = base64.b64decode(committed_b64).decode("utf-8")
    lines = committed_text.strip("\n").split("\n")

    assert lines[0] == "date,irrigation_mm,method,source,notes"
    assert lines[1] == "2025-03-10,25.0,drip,farmer,valid row"
    assert lines[2].startswith("2025-05-01,15.0,sprinkler,user_dashboard,second event")
    assert len(lines) == 3

    # sha from the fetched file must be used for the update
    assert put_kwargs["json"]["sha"] == "abc123"

    # Token must never leak into the PUT body or headers we can inspect as text
    assert _FAKE_TOKEN not in str(put_kwargs["json"])


def test_missing_file_creates_header_and_event():
    get_resp = _mock_response(404, {})
    put_resp = _mock_response(200, {"commit": {"html_url": "https://github.com/x/y/commit/abc"}})

    with patch("src.irrigation.github_persistence.requests.get", return_value=get_resp), \
         patch("src.irrigation.github_persistence.requests.put", return_value=put_resp) as mock_put:
        result = append_irrigation_event_github(
            repo=_FAKE_REPO,
            branch=_FAKE_BRANCH,
            token=_FAKE_TOKEN,
            csv_path=_FAKE_CSV_PATH,
            event={"date": "2025-05-01", "irrigation_mm": 20.0, "method": "drip"},
        )

    assert result["success"] is True

    put_kwargs = mock_put.call_args.kwargs
    committed_text = base64.b64decode(put_kwargs["json"]["content"]).decode("utf-8")
    lines = committed_text.strip("\n").split("\n")
    assert lines[0] == "date,irrigation_mm,method,source,notes"
    assert lines[1].startswith("2025-05-01,20.0,drip")
    assert len(lines) == 2
    # No sha for a brand-new file
    assert "sha" not in put_kwargs["json"]


# ---------------------------------------------------------------------------
# Validation happens before any network call
# ---------------------------------------------------------------------------

def test_negative_irrigation_rejected_before_api_call():
    with patch("src.irrigation.github_persistence.requests.get") as mock_get, \
         patch("src.irrigation.github_persistence.requests.put") as mock_put:
        with pytest.raises(ValueError):
            append_irrigation_event_github(
                repo=_FAKE_REPO,
                branch=_FAKE_BRANCH,
                token=_FAKE_TOKEN,
                csv_path=_FAKE_CSV_PATH,
                event={"date": "2025-05-01", "irrigation_mm": -5.0},
            )
    mock_get.assert_not_called()
    mock_put.assert_not_called()


def test_invalid_date_rejected_before_api_call():
    with patch("src.irrigation.github_persistence.requests.get") as mock_get, \
         patch("src.irrigation.github_persistence.requests.put") as mock_put:
        with pytest.raises(ValueError):
            append_irrigation_event_github(
                repo=_FAKE_REPO,
                branch=_FAKE_BRANCH,
                token=_FAKE_TOKEN,
                csv_path=_FAKE_CSV_PATH,
                event={"date": "not-a-date", "irrigation_mm": 10.0},
            )
    mock_get.assert_not_called()
    mock_put.assert_not_called()


def test_build_irrigation_event_row_rejects_bad_input():
    with pytest.raises(ValueError):
        build_irrigation_event_row(date="2025-05-01", irrigation_mm=-1.0)
    with pytest.raises(ValueError):
        build_irrigation_event_row(date="nope", irrigation_mm=10.0)


# ---------------------------------------------------------------------------
# GitHub API failure — safe error dict, no token leak
# ---------------------------------------------------------------------------

def test_api_failure_returns_safe_dict_without_token():
    get_resp = _mock_response(
        200,
        {"content": _b64("date,irrigation_mm,method,source,notes\n"), "sha": "abc123"},
    )
    put_resp = _mock_response(422, {"message": "Validation Failed"})

    with patch("src.irrigation.github_persistence.requests.get", return_value=get_resp), \
         patch("src.irrigation.github_persistence.requests.put", return_value=put_resp):
        result = append_irrigation_event_github(
            repo=_FAKE_REPO,
            branch=_FAKE_BRANCH,
            token=_FAKE_TOKEN,
            csv_path=_FAKE_CSV_PATH,
            event={"date": "2025-05-01", "irrigation_mm": 10.0},
        )

    assert result["success"] is False
    assert result["mode"] == "github_csv"
    assert result["commit_url"] is None
    assert _FAKE_TOKEN not in str(result)


def test_network_error_returns_safe_dict_without_token():
    import requests as _requests

    with patch(
        "src.irrigation.github_persistence.requests.get",
        side_effect=_requests.exceptions.ConnectionError("boom"),
    ):
        result = append_irrigation_event_github(
            repo=_FAKE_REPO,
            branch=_FAKE_BRANCH,
            token=_FAKE_TOKEN,
            csv_path=_FAKE_CSV_PATH,
            event={"date": "2025-05-01", "irrigation_mm": 10.0},
        )

    assert result["success"] is False
    assert _FAKE_TOKEN not in str(result)


# ---------------------------------------------------------------------------
# Dashboard import
# ---------------------------------------------------------------------------

def test_dashboard_import_still_works():
    mod = importlib.import_module("app.sections.irrigation_events")
    assert hasattr(mod, "render_irrigation_events_page")
    assert callable(mod.render_irrigation_events_page)
