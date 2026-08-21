"""
src/irrigation/persistence.py

Persistence-mode helpers for irrigation event recording.

CONTEXT
-------
The Irrigation Events dashboard form (app/sections/irrigation_events.py)
currently appends new events to a local CSV file:

    data/manual/muthukur_irrigation_events.csv

That works for local development, but on ephemeral hosting such as
Streamlit Community Cloud, the filesystem is not guaranteed to persist
across app restarts or redeploys — a write today may silently disappear
tomorrow. This module reports which persistence mode is configured and
whether GitHub-backed persistence is actually usable (credentials present).
The GitHub write path itself lives in src/irrigation/github_persistence.py
and is only invoked by the dashboard when this module reports it enabled.

SCOPE — WHAT THIS MODULE DOES NOT DO
-------------------------------------
  - It does NOT call the GitHub API or push commits anywhere itself (see
    src/irrigation/github_persistence.py for the actual write path).
  - It does NOT require GitHub tokens or any credentials to import or use.
  - It does NOT change how the local CSV form writes data — that remains
    exactly as-is (see src/irrigation/load_irrigation_events.append_irrigation_event).
  - It does NOT implement database storage.
  - It NEVER returns the raw token value from get_github_persistence_settings
    — only a `token_present` boolean, so status displays can't leak it.

This is primarily a planning/status layer: it reports which persistence
mode is configured, whether GitHub persistence is enabled (mode selected
AND credentials present), and human-readable explanations of each mode —
so the dashboard and README can accurately describe current behavior and
the upgrade path.

CONFIGURATION
--------------
configs/config.yaml:
    irrigation_persistence_mode: "local_csv"   # local_csv | github_csv | database

GitHub credentials (only relevant if irrigation_persistence_mode is set to
"github_csv"), preferred as environment variables / Streamlit secrets:
    GITHUB_TOKEN   — personal access token with repo contents write scope
    GITHUB_REPO    — "<owner>/<repo>", e.g. "vanaprashanth/mango-digital-twin"
    GITHUB_BRANCH  — target branch (optional, defaults to "master")
Or equivalently a `github: {token: ..., repo: ..., branch: ...}` section in
config — env vars always take priority.

PUBLIC FUNCTIONS
-----------------
  get_irrigation_persistence_mode(config) -> str
  is_github_persistence_enabled(config_or_env) -> bool
  get_github_persistence_settings(config) -> dict
  explain_persistence_mode(mode) -> str
"""

from __future__ import annotations

import os
from typing import Any, Mapping, Optional

# ---------------------------------------------------------------------------
# Supported modes
# ---------------------------------------------------------------------------

VALID_PERSISTENCE_MODES = ("local_csv", "github_csv", "database")
DEFAULT_PERSISTENCE_MODE = "local_csv"

# Human-readable labels for dashboard display.
_MODE_LABELS = {
    "local_csv": "Local CSV",
    "github_csv": "GitHub-backed CSV",
    "database": "Database",
}

_EXPLANATIONS = {
    "local_csv": (
        "Local CSV mode (current default, implemented). Irrigation events are "
        "appended directly to data/manual/muthukur_irrigation_events.csv on the "
        "local filesystem. This is simple and fully auditable via git history, "
        "but on ephemeral hosting (e.g. Streamlit Community Cloud) writes may "
        "not persist across an app restart or redeploy."
    ),
    "github_csv": (
        "GitHub-backed CSV mode (planned, NOT yet implemented). New irrigation "
        "events would be committed directly to this repository's CSV file via "
        "the GitHub API, giving durable, versioned, redeploy-safe storage while "
        "keeping the data in a plain, auditable CSV. Requires GITHUB_TOKEN and "
        "GITHUB_REPO to be configured; remains disabled until both are present. "
        "No GitHub API calls are made by this prototype yet."
    ),
    "database": (
        "Database mode (planned, NOT yet implemented). Irrigation events would "
        "be written to an external database (e.g. Postgres/SQLite) for durable, "
        "queryable, multi-user, redeploy-safe storage. This is the recommended "
        "long-term production approach once the project outgrows a single CSV "
        "file."
    ),
}

_UNKNOWN_MODE_TEMPLATE = (
    "Unknown persistence mode '{mode}'. Supported modes are: {supported}. "
    f"Falling back to '{DEFAULT_PERSISTENCE_MODE}' behavior."
)

# GitHub credential lookup keys (env vars take priority over config).
_GITHUB_TOKEN_ENV_VAR = "GITHUB_TOKEN"
_GITHUB_REPO_ENV_VAR = "GITHUB_REPO"
_GITHUB_BRANCH_ENV_VAR = "GITHUB_BRANCH"
_DEFAULT_GITHUB_BRANCH = "master"
_DEFAULT_IRRIGATION_CSV_PATH = "data/manual/muthukur_irrigation_events.csv"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _raw_dict(config: Any) -> Mapping[str, Any]:
    """
    Best-effort extraction of a plain dict view of `config`.

    Accepts, in order of preference:
      - None                       -> {}
      - a plain dict               -> itself
      - a src.utils.config.Config instance (via its private `_raw` attr)
      - any object exposing a `.get()` method (duck-typed mapping)

    Never raises — always returns something dict-like (possibly empty).
    """
    if config is None:
        return {}
    if isinstance(config, Mapping):
        return config
    raw = getattr(config, "_raw", None)
    if isinstance(raw, Mapping):
        return raw
    if hasattr(config, "get"):
        return config  # duck-typed mapping
    return {}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def get_irrigation_persistence_mode(config: Any) -> str:
    """
    Return the configured irrigation persistence mode.

    Reads `irrigation_persistence_mode` from `config` (a Config instance,
    a plain dict, or any mapping-like object). Falls back to
    DEFAULT_PERSISTENCE_MODE ("local_csv") if the config is missing, the
    key is absent, or the value is not one of VALID_PERSISTENCE_MODES.

    This function never raises.
    """
    raw = _raw_dict(config)
    try:
        mode = raw.get("irrigation_persistence_mode")
    except Exception:
        mode = None

    if not isinstance(mode, str) or mode not in VALID_PERSISTENCE_MODES:
        return DEFAULT_PERSISTENCE_MODE

    return mode


def is_github_persistence_enabled(config_or_env: Optional[Any] = None) -> bool:
    """
    Report whether GitHub-backed persistence is both selected AND usable.

    Returns True only if ALL of the following hold:
      1. get_irrigation_persistence_mode(config_or_env) == "github_csv"
      2. A GitHub token is available (env var GITHUB_TOKEN, or a
         config["github"]["token"] value)
      3. A target repo is configured (env var GITHUB_REPO, or a
         config["github"]["repo"] value)

    IMPORTANT: this function only checks whether the *prerequisites* look
    present. It does NOT validate the token, does NOT contact GitHub, and
    does NOT push anything. The GitHub commit path itself is not
    implemented yet — this flag exists so future code can gate on it, and
    so the dashboard can show an accurate "would this work" status.

    Safe to call with no arguments, None, or a bare dict — never raises.
    """
    mode = get_irrigation_persistence_mode(config_or_env)
    if mode != "github_csv":
        return False

    raw = _raw_dict(config_or_env)
    github_cfg = raw.get("github") if isinstance(raw, Mapping) else None
    if not isinstance(github_cfg, Mapping):
        github_cfg = {}

    token = os.environ.get(_GITHUB_TOKEN_ENV_VAR) or github_cfg.get("token")
    repo = os.environ.get(_GITHUB_REPO_ENV_VAR) or github_cfg.get("repo")

    return bool(token) and bool(repo)


def get_github_persistence_settings(config: Any = None) -> dict:
    """
    Collect GitHub-backed persistence settings for display and for wiring
    into src.irrigation.github_persistence.append_irrigation_event_github.

    Reads (env vars take priority over config, so Streamlit Cloud secrets
    always win over any local config file value):
      - GITHUB_TOKEN   / config["github"]["token"]
      - GITHUB_REPO    / config["github"]["repo"]     e.g. "owner/repo"
      - GITHUB_BRANCH  / config["github"]["branch"]   default "master"
      - irrigation_events_csv path from config["paths"], defaulting to
        "data/manual/muthukur_irrigation_events.csv" if unavailable

    IMPORTANT: the returned dict's "token" value is intentionally omitted —
    only `token_present` (a bool) is reported, so callers displaying this
    dict (e.g. in the dashboard) can never accidentally leak the token.
    The actual token value must be re-read from the environment/config by
    the caller only at the point it is passed to
    append_irrigation_event_github, and must never be logged or displayed.

    Returns
    -------
    dict with keys:
        repo          : str | None   ("<owner>/<repo>", or None if unset)
        branch        : str          (defaults to "master")
        token_present : bool
        csv_path      : str          (repo-relative path to the irrigation CSV)
        enabled       : bool         (True only if mode is "github_csv" AND
                                       both a token and repo are present)

    Never raises.
    """
    raw = _raw_dict(config)
    github_cfg = raw.get("github") if isinstance(raw, Mapping) else None
    if not isinstance(github_cfg, Mapping):
        github_cfg = {}

    token = os.environ.get(_GITHUB_TOKEN_ENV_VAR) or github_cfg.get("token")
    repo = os.environ.get(_GITHUB_REPO_ENV_VAR) or github_cfg.get("repo")
    branch = (
        os.environ.get(_GITHUB_BRANCH_ENV_VAR)
        or github_cfg.get("branch")
        or _DEFAULT_GITHUB_BRANCH
    )

    csv_path = _DEFAULT_IRRIGATION_CSV_PATH
    try:
        paths_cfg = raw.get("paths") if isinstance(raw, Mapping) else None
        if isinstance(paths_cfg, Mapping) and paths_cfg.get("irrigation_events_csv"):
            csv_path = paths_cfg["irrigation_events_csv"]
    except Exception:
        pass

    mode = get_irrigation_persistence_mode(config)
    token_present = bool(token)
    repo_present = bool(repo)

    return {
        "repo": repo if repo_present else None,
        "branch": branch,
        "token_present": token_present,
        "csv_path": csv_path,
        "enabled": mode == "github_csv" and token_present and repo_present,
    }


def get_github_token(config: Any = None) -> Optional[str]:
    """
    Return the raw GitHub token to use for an authenticated API call, or
    None if not configured.

    Deliberately kept SEPARATE from get_github_persistence_settings() so
    that dict is always safe to display or log (it only reports
    `token_present`, a bool). This function returns the real secret and
    must only be called immediately before passing it to
    append_irrigation_event_github — callers must never print, log, cache
    for display, or otherwise surface the returned value.
    """
    raw = _raw_dict(config)
    github_cfg = raw.get("github") if isinstance(raw, Mapping) else None
    if not isinstance(github_cfg, Mapping):
        github_cfg = {}
    return os.environ.get(_GITHUB_TOKEN_ENV_VAR) or github_cfg.get("token")


def explain_persistence_mode(mode: str) -> str:
    """
    Return a human-readable explanation of a persistence mode, suitable for
    display in the dashboard or README.

    For an unrecognized mode string, returns an explanatory message noting
    the mode is unsupported and that behavior falls back to
    DEFAULT_PERSISTENCE_MODE — it does not raise.
    """
    if mode in _EXPLANATIONS:
        return _EXPLANATIONS[mode]

    return _UNKNOWN_MODE_TEMPLATE.format(
        mode=mode,
        supported=", ".join(VALID_PERSISTENCE_MODES),
    )


def persistence_mode_label(mode: str) -> str:
    """Return a short display label for a mode (e.g. for a status badge)."""
    return _MODE_LABELS.get(mode, mode.replace("_", " ").title() if isinstance(mode, str) else str(mode))
