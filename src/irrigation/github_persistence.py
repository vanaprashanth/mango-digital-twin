"""
src/irrigation/github_persistence.py

Optional GitHub-backed writeback for the irrigation events CSV.

CONTEXT
-------
data/manual/muthukur_irrigation_events.csv is normally appended to on the
local filesystem (see src/irrigation/load_irrigation_events.append_irrigation_event).
On ephemeral hosting such as Streamlit Community Cloud, that local write may
not survive an app restart or redeploy. This module offers an alternative:
commit the updated CSV directly to the project's GitHub repository via the
GitHub Contents API, so the new row is durably stored in git history
regardless of what happens to the running container's filesystem.

This module is disabled by default and only takes effect when
`irrigation_persistence_mode: "github_csv"` is configured AND a token/repo
are present (see src.irrigation.persistence.get_github_persistence_settings).
Importing this module never requires a token and never makes a network call
on its own — it only acts when append_irrigation_event_github() is called
explicitly with credentials.

SAFETY
------
  - Only ever touches the single CSV file at `csv_path` in the target repo.
    Never reads or writes any other path.
  - Uses the same date/irrigation_mm validation rules as the local CSV path
    (src.irrigation.load_irrigation_events.validate_new_event) — invalid
    input is rejected BEFORE any network call is made.
  - Builds the new CSV row through the stdlib `csv` module (proper quoting
    and escaping), never manual string concatenation, so notes containing
    commas, quotes, or newlines cannot corrupt the file.
  - Never logs, prints, or includes the token in any return value or error
    message.
  - Network/API errors are caught and returned as a safe result dict —
    this function is designed to never raise for network-related failures
    (it CAN still raise ValueError for invalid event data, same as the
    local append path, since that is a caller-input bug, not a network
    condition).
  - If the target file does not yet exist in the repo, it is created with
    the correct header row followed by the new event — never overwrites or
    touches any other file in the repository.

PUBLIC FUNCTIONS
-----------------
  build_irrigation_event_row(date, irrigation_mm, method, source, notes) -> list[str]
  append_irrigation_event_github(repo, branch, token, csv_path, event, commit_message=None) -> dict
"""

from __future__ import annotations

import base64
import csv
import io
from typing import Any, Optional

import requests

from src.irrigation.load_irrigation_events import _SCHEMA_COLS, validate_new_event

_GITHUB_API_BASE = "https://api.github.com"
_REQUEST_TIMEOUT_S = 15


def build_irrigation_event_row(
    date: "Any",
    irrigation_mm: float,
    method: str = "",
    source: str = "",
    notes: str = "",
) -> list:
    """
    Validate and format a single irrigation event as a CSV row (list of
    string-safe values), matching the `_SCHEMA_COLS` column order:
    date, irrigation_mm, method, source, notes.

    Raises ValueError if the date or irrigation_mm are invalid (same rules
    as the local CSV append path).
    """
    parsed_date, mm_value = validate_new_event(date, irrigation_mm)
    return [
        parsed_date.strftime("%Y-%m-%d"),
        mm_value,
        str(method).strip(),
        str(source).strip(),
        str(notes).strip(),
    ]


def _csv_text_to_rows(text: str) -> list:
    """Parse CSV text into a list of rows (list of lists), using the csv module."""
    reader = csv.reader(io.StringIO(text))
    return [row for row in reader]


def _rows_to_csv_text(rows: list) -> str:
    """Serialize a list of rows back to CSV text using the csv module (proper quoting)."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def _safe_error(message: str) -> dict:
    """Build a failure result dict. Never include the token or raw exception repr."""
    return {
        "success": False,
        "mode": "github_csv",
        "message": message,
        "commit_url": None,
    }


def append_irrigation_event_github(
    repo: str,
    branch: str,
    token: str,
    csv_path: str,
    event: dict,
    commit_message: Optional[str] = None,
) -> dict:
    """
    Append one irrigation event to the CSV file at `csv_path` in `repo` on
    `branch`, via the GitHub Contents API, and commit the change.

    Parameters
    ----------
    repo : str
        "<owner>/<repo>", e.g. "vanaprashanth/mango-digital-twin".
    branch : str
        Target branch, e.g. "master".
    token : str
        GitHub personal access token with repo-contents write permission.
        NEVER logged, printed, or included in the returned dict.
    csv_path : str
        Path to the CSV file within the repo, e.g.
        "data/manual/muthukur_irrigation_events.csv". Only this exact path
        is ever read or written.
    event : dict
        Must contain "date" and "irrigation_mm"; may optionally contain
        "method", "source", "notes".
    commit_message : str, optional
        Custom commit message. Defaults to a message naming the event date.

    Returns
    -------
    dict with keys:
        success      : bool
        mode         : "github_csv"
        message      : human-readable outcome (never contains the token)
        commit_url   : GitHub commit URL on success, else None

    Raises
    ------
    ValueError
        If `event["date"]` or `event["irrigation_mm"]` are invalid. This is
        raised (not returned as a failure dict) BEFORE any network call, so
        callers can distinguish "bad input" from "GitHub/network problem".
    """
    # ── Validate input before any network call ──────────────────────────
    new_row = build_irrigation_event_row(
        date=event.get("date"),
        irrigation_mm=event.get("irrigation_mm"),
        method=event.get("method", ""),
        source=event.get("source", ""),
        notes=event.get("notes", ""),
    )

    if not repo or "/" not in repo:
        return _safe_error(
            f"Invalid repo '{repo}'. Expected the format '<owner>/<repo>' "
            "(e.g. 'vanaprashanth/mango-digital-twin')."
        )
    if not branch:
        return _safe_error("No branch specified.")
    if not token:
        return _safe_error("No GitHub token provided.")
    if not csv_path:
        return _safe_error("No csv_path specified.")

    contents_url = f"{_GITHUB_API_BASE}/repos/{repo}/contents/{csv_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # ── Fetch current file (if it exists) ───────────────────────────────
    try:
        get_resp = requests.get(
            contents_url,
            headers=headers,
            params={"ref": branch},
            timeout=_REQUEST_TIMEOUT_S,
        )
    except requests.exceptions.RequestException as exc:
        return _safe_error(f"Network error while fetching current CSV from GitHub: {type(exc).__name__}")

    existing_sha: Optional[str] = None
    if get_resp.status_code == 200:
        try:
            payload = get_resp.json()
            encoded_content = payload.get("content", "")
            existing_sha = payload.get("sha")
            decoded = base64.b64decode(encoded_content.encode("ascii")).decode("utf-8")
            rows = _csv_text_to_rows(decoded)
        except Exception as exc:
            return _safe_error(f"Could not decode existing CSV content from GitHub: {type(exc).__name__}")

        # Ensure a header exists; if the file is empty or malformed, start fresh with the schema header.
        if not rows or rows[0] != _SCHEMA_COLS:
            if not rows:
                rows = [_SCHEMA_COLS]
            else:
                rows = [_SCHEMA_COLS] + rows
    elif get_resp.status_code == 404:
        # File does not exist yet in the repo — create it with header + event.
        rows = [_SCHEMA_COLS]
        existing_sha = None
    else:
        return _safe_error(
            f"GitHub API error fetching CSV (HTTP {get_resp.status_code}). "
            "Check that the repo, branch, and token permissions are correct."
        )

    # ── Append exactly one new row, preserving all existing rows ────────
    rows.append(new_row)
    updated_csv_text = _rows_to_csv_text(rows)
    updated_content_b64 = base64.b64encode(updated_csv_text.encode("utf-8")).decode("ascii")

    if commit_message is None:
        commit_message = f"Add irrigation event {new_row[0]} ({new_row[1]} mm) via dashboard"

    put_payload: dict = {
        "message": commit_message,
        "content": updated_content_b64,
        "branch": branch,
    }
    if existing_sha:
        put_payload["sha"] = existing_sha

    try:
        put_resp = requests.put(
            contents_url,
            headers=headers,
            json=put_payload,
            timeout=_REQUEST_TIMEOUT_S,
        )
    except requests.exceptions.RequestException as exc:
        return _safe_error(f"Network error while committing updated CSV to GitHub: {type(exc).__name__}")

    if put_resp.status_code not in (200, 201):
        return _safe_error(
            f"GitHub API error committing CSV (HTTP {put_resp.status_code}). "
            "Check that the repo, branch, and token permissions are correct."
        )

    try:
        commit_url = put_resp.json().get("commit", {}).get("html_url")
    except Exception:
        commit_url = None

    return {
        "success": True,
        "mode": "github_csv",
        "message": f"Committed irrigation event {new_row[0]} ({new_row[1]} mm) to {repo}@{branch}.",
        "commit_url": commit_url,
    }
