"""
Lightweight per-page data freshness indicator for the Mango Digital Twin dashboard.

WHAT THIS MODULE DOES
  Provides a single helper function, show_freshness_indicator(), that each
  dashboard page calls at the top of its render function. It shows:

    - Latest data date (from the page's own DataFrame, if it has a date column)
    - Row count (from the DataFrame)
    - Pipeline run time and status (from pipeline_run_metadata.json)
    - Git commit hash (from pipeline_run_metadata.json)
    - A stale-data warning if the latest date is more than
      staleness_warning_days old

  It intentionally uses lightweight Streamlit primitives (st.caption,
  st.info, st.warning) and renders as a compact single line or small block
  at the top of the page -- it does NOT redesign page layouts.

WHAT THIS MODULE DOES NOT DO
  - Does not fetch or recompute any data.
  - Does not change any chart or table on any page.
  - Does not introduce new config entries.
  - Does not crash if metadata is missing or the DataFrame has no date column.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st

from src.utils.config import get_config
from src.utils.pipeline_metadata import load_metadata_json

_config = get_config()
_METADATA_PATH: Path = _config.path("pipeline_run_metadata_json")

_DEFAULT_STALENESS_DAYS = 7


def _parse_iso(ts: str | None) -> dt.datetime | None:
    """Parse an ISO-8601 UTC string from the metadata JSON, or return None."""
    if not ts:
        return None
    try:
        return dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def _latest_date_in_df(df: pd.DataFrame | None) -> dt.date | None:
    """
    Return the maximum date found in the DataFrame's 'date' column,
    or None if the DataFrame is None/empty/has no date column.
    """
    if df is None or df.empty:
        return None
    if "date" not in df.columns:
        return None
    try:
        parsed = pd.to_datetime(df["date"], errors="coerce").dropna()
        if parsed.empty:
            return None
        return parsed.max().date()
    except Exception:
        return None


def show_freshness_indicator(
    df: pd.DataFrame | None = None,
    label: str = "",
    staleness_warning_days: int = _DEFAULT_STALENESS_DAYS,
) -> None:
    """
    Render a compact data freshness indicator at the top of a dashboard page.

    Parameters
    ----------
    df : pd.DataFrame | None
        The primary DataFrame for this page. If it has a 'date' column, the
        latest date and row count are shown. Pass None for pages with no
        time-series DataFrame (e.g. Soil Intelligence, Irrigation Advisory).
    label : str
        Optional human-readable name for the dataset shown in the indicator
        (e.g. "Historical risk", "FAO-56 water balance"). If empty, the
        indicator just says "Data".
    staleness_warning_days : int
        Show a st.warning if the latest date is more than this many days old.
        Default is 7. Set to 0 to disable.
    """
    metadata = load_metadata_json(_METADATA_PATH)
    latest_date = _latest_date_in_df(df)
    today = dt.date.today()

    parts: list[str] = []

    # --- Data date / row count (from the page's own DataFrame) ---
    if latest_date is not None:
        data_label = label if label else "Data"
        row_count = len(df) if df is not None else 0
        parts.append(
            f"**{data_label}:** latest date {latest_date.strftime('%Y-%m-%d')} "
            f"({row_count:,} rows)"
        )

    # --- Pipeline run info (from metadata JSON) ---
    if metadata is not None:
        run_ts = _parse_iso(metadata.get("run_completed_at"))
        if run_ts:
            parts.append(f"Pipeline ran {run_ts.strftime('%Y-%m-%d %H:%M')} UTC")
        commit = metadata.get("git_commit", "unknown")
        if commit and commit != "unknown":
            parts.append(f"commit `{commit[:8]}`")

    if parts:
        st.caption("  ·  ".join(parts))

    # --- Staleness warning ---
    if staleness_warning_days > 0 and latest_date is not None:
        age_days = (today - latest_date).days
        if age_days > staleness_warning_days:
            dataset_name = label if label else "This page's data"
            st.warning(
                f"⚠️ {dataset_name} is {age_days} day(s) old "
                f"(latest: {latest_date.strftime('%Y-%m-%d')}). "
                "Run `python main.py` to refresh."
            )
