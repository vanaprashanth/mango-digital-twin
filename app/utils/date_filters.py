"""
Reusable date-range filter utilities for the Mango Digital Twin dashboard.

Every time-series page imports from here so the list of options, the
filtering logic, and the UI widget stay consistent across pages.

Usage pattern
-------------
    from app.utils.date_filters import filter_by_date_range, render_date_range_selector

    # In a render function:
    selected = render_date_range_selector(key="my_page_date_range", default="1 year")
    df_plot  = filter_by_date_range(df, selected_range=selected)
    if df_plot.empty:
        st.warning("No data in the selected time window.")
        # return or st.stop()
    # ... pass df_plot to charts ...
"""
from __future__ import annotations

from datetime import timedelta

import pandas as pd
import streamlit as st

# Ordered list of options shown in the selectbox.
DATE_RANGE_OPTIONS: list[str] = [
    "Past 24 hours",
    "1 week",
    "1 month",
    "3 months",
    "6 months",
    "1 year",
    "5 years",
    "Max",
]

# Mapping from option label to number of calendar days to look back.
# None means "no cutoff" (all rows).
_RANGE_DAYS: dict[str, int | None] = {
    "Past 24 hours": 1,
    "1 week": 7,
    "1 month": 30,
    "3 months": 90,
    "6 months": 180,
    "1 year": 365,
    "5 years": 1825,
    "Max": None,
}


def get_date_range_options() -> list[str]:
    """Return the ordered list of time-window options."""
    return DATE_RANGE_OPTIONS


def filter_by_date_range(
    df: pd.DataFrame,
    date_col: str = "date",
    selected_range: str = "1 year",
    reference_date=None,
) -> pd.DataFrame:
    """
    Return a copy of *df* filtered to the rows inside *selected_range*.

    Parameters
    ----------
    df
        Input DataFrame.  May be empty; function returns it unchanged in
        that case.
    date_col
        Name of the column that holds the dates.  Coerced to
        ``pd.Timestamp`` if it isn't already.
    selected_range
        One of DATE_RANGE_OPTIONS.  Unrecognised values are treated as
        "Max" (all rows returned).
    reference_date
        If given, the cut-off is computed relative to this date instead
        of the maximum date present in *df[date_col]*.  Passed as
        anything that ``pd.Timestamp`` can parse.

    Returns
    -------
    pd.DataFrame
        Subset of *df* in original row order.  May be empty.
    """
    if df is None:
        return pd.DataFrame()
    if df.empty:
        return df.copy()

    if date_col not in df.columns:
        return df.copy()  # can't filter — return as-is

    # Coerce to datetime if needed; errors -> NaT (rows with NaT are excluded
    # by the >= comparison below, which is the safe behaviour).
    col = pd.to_datetime(df[date_col], errors="coerce")

    days = _RANGE_DAYS.get(selected_range)  # None if unrecognised or "Max"

    if days is None:
        return df.copy()

    if reference_date is not None:
        ref = pd.Timestamp(reference_date)
    else:
        ref = col.dropna().max()
        if pd.isna(ref):
            return df.copy()  # all NaT — cannot filter sensibly

    cutoff = ref - timedelta(days=days)
    mask = col >= cutoff
    return df[mask].copy()


def render_date_range_selector(key: str, default: str = "1 year") -> str:
    """
    Render a compact, labelled selectbox for choosing a time window.

    The label ("Time window") is visible and the widget is rendered inline
    so it fits naturally at the top of any dashboard page without taking
    too much vertical space.

    Parameters
    ----------
    key
        Streamlit widget key — must be unique per page so multiple
        selectors on the same page don't share state.
    default
        The option pre-selected on first load.  Must be one of
        DATE_RANGE_OPTIONS; falls back to "1 year" if not found.

    Returns
    -------
    str
        The currently selected label, e.g. ``"1 year"``.
    """
    options = DATE_RANGE_OPTIONS
    default_index = options.index(default) if default in options else options.index("1 year")

    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("**Time window**")
    with col2:
        selected = st.selectbox(
            "Time window",
            options=options,
            index=default_index,
            key=key,
            label_visibility="collapsed",
        )
    return selected
