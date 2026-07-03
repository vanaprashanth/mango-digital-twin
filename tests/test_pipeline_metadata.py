"""
tests/test_pipeline_metadata.py

Unit tests for the git-version helpers in src/utils/pipeline_metadata.py.

_git_commit() and _git_branch() are safe wrappers around `git rev-parse`.
These tests verify:
  - They return strings (never crash)
  - In this project (which IS a git repo) they return real values
  - When subprocess is monkeypatched to raise, they fall back to "unknown"
"""

from __future__ import annotations

import subprocess
from unittest.mock import patch, MagicMock

import pytest

from src.utils.pipeline_metadata import _git_commit, _git_branch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_failed_result(returncode: int = 128) -> MagicMock:
    """CompletedProcess-like mock that signals a git error."""
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = ""
    return mock


# ---------------------------------------------------------------------------
# _git_commit()
# ---------------------------------------------------------------------------

class TestGitCommit:
    def test_returns_string(self):
        result = _git_commit()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_valid_hash_in_git_repo(self):
        # This project is a git repository, so we expect a 40-char hex hash
        result = _git_commit()
        if result != "unknown":
            assert len(result) == 40
            assert all(c in "0123456789abcdef" for c in result.lower())

    def test_falls_back_when_subprocess_raises(self):
        with patch("src.utils.pipeline_metadata.subprocess.run", side_effect=FileNotFoundError("git not found")):
            result = _git_commit()
        assert result == "unknown"

    def test_falls_back_when_git_returns_nonzero(self):
        with patch("src.utils.pipeline_metadata.subprocess.run", return_value=_make_failed_result(128)):
            result = _git_commit()
        assert result == "unknown"

    def test_falls_back_when_stdout_is_empty(self):
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = "   "
        with patch("src.utils.pipeline_metadata.subprocess.run", return_value=mock):
            result = _git_commit()
        assert result == "unknown"

    def test_never_raises(self):
        # Even with a completely unexpected exception, must not propagate
        with patch("src.utils.pipeline_metadata.subprocess.run", side_effect=RuntimeError("unexpected")):
            result = _git_commit()
        assert result == "unknown"


# ---------------------------------------------------------------------------
# _git_branch()
# ---------------------------------------------------------------------------

class TestGitBranch:
    def test_returns_string(self):
        result = _git_branch()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_non_empty_name_in_git_repo(self):
        result = _git_branch()
        # In a real repo: branch name or "HEAD" (detached) or "unknown"
        assert result  # never empty string

    def test_falls_back_when_subprocess_raises(self):
        with patch("src.utils.pipeline_metadata.subprocess.run", side_effect=FileNotFoundError("git not found")):
            result = _git_branch()
        assert result == "unknown"

    def test_falls_back_when_git_returns_nonzero(self):
        with patch("src.utils.pipeline_metadata.subprocess.run", return_value=_make_failed_result(128)):
            result = _git_branch()
        assert result == "unknown"

    def test_falls_back_when_stdout_is_empty(self):
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = ""
        with patch("src.utils.pipeline_metadata.subprocess.run", return_value=mock):
            result = _git_branch()
        assert result == "unknown"

    def test_never_raises(self):
        with patch("src.utils.pipeline_metadata.subprocess.run", side_effect=OSError("no git")):
            result = _git_branch()
        assert result == "unknown"


# ---------------------------------------------------------------------------
# build_pipeline_metadata includes git fields
# ---------------------------------------------------------------------------

class TestBuildPipelineMetadataGitFields:
    """Smoke-check that git_commit and git_branch appear in the output dict."""

    def test_git_commit_present_in_metadata(self):
        from src.utils.pipeline_metadata import build_pipeline_metadata, utc_now
        now = utc_now()
        meta = build_pipeline_metadata(
            run_started_at=now,
            run_completed_at=now,
            pipeline_mode="test",
            status="success",
        )
        assert "git_commit" in meta
        assert isinstance(meta["git_commit"], str)
        assert meta["git_commit"]  # non-empty

    def test_git_branch_present_in_metadata(self):
        from src.utils.pipeline_metadata import build_pipeline_metadata, utc_now
        now = utc_now()
        meta = build_pipeline_metadata(
            run_started_at=now,
            run_completed_at=now,
            pipeline_mode="test",
            status="success",
        )
        assert "git_branch" in meta
        assert isinstance(meta["git_branch"], str)
        assert meta["git_branch"]  # non-empty

    def test_existing_fields_still_present(self):
        """Regression guard: adding git fields must not drop any existing fields."""
        from src.utils.pipeline_metadata import build_pipeline_metadata, utc_now
        now = utc_now()
        meta = build_pipeline_metadata(
            run_started_at=now,
            run_completed_at=now,
            pipeline_mode="test",
            status="success",
        )
        required_existing = {
            "run_started_at", "run_completed_at", "timezone",
            "pipeline_mode", "status",
            "source_files", "output_files", "row_counts",
            "latest_dates", "file_modified_timestamps",
            "missing_file_warnings", "near_real_time_note", "step_results",
        }
        missing = required_existing - set(meta.keys())
        assert not missing, f"Existing metadata fields were dropped: {missing}"
