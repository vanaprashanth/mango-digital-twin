"""
ET0 Validation page: Open-Meteo ET0 vs FAO-56 Penman-Monteith ET0.

This page renders the comparison analysis produced by
src/validation/compare_et0_openmeteo_vs_fao56.py.  It is intentionally
lightweight: a summary markdown block, a data table, and (when enough rows
exist) a line chart.  It does NOT redesign existing pages.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app.sections.freshness import show_freshness_indicator


def render_et0_validation_page(
    et0_comparison_df: pd.DataFrame | None,
    summary_text: str | None,
) -> None:
    """Render the ET0 source comparison validation page."""

    st.title("ET0 Validation: Open-Meteo vs FAO-56")
    show_freshness_indicator(
        et0_comparison_df,
        label="ET0 comparison",
        staleness_warning_days=7,
    )

    st.caption(
        "Source-to-source comparison between Open-Meteo's direct ET0 estimate "
        "and this project's FAO-56 Penman-Monteith ET0 computed from NASA POWER "
        "weather data. Neither is ground-truth — both are model-derived."
    )

    st.divider()

    # --- Summary markdown ---
    if summary_text:
        st.markdown(summary_text)
    else:
        st.info(
            "ET0 comparison summary not found. "
            "Run `python main.py --skip-fetch` to generate it."
        )

    st.divider()

    # --- Data table + chart ---
    if et0_comparison_df is None:
        st.info(
            "ET0 comparison data not found. "
            "Run `python main.py --skip-fetch` to generate it."
        )
        return

    if et0_comparison_df.empty:
        st.info(
            "No overlapping dates found between Open-Meteo and FAO-56 data. "
            "Run `python main.py` to fetch fresh weather data. "
            "Once Open-Meteo recent dates overlap with the FAO-56 historical range, "
            "the comparison will populate here automatically."
        )
        return

    # Have data — show chart + table
    df = et0_comparison_df.copy()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])

    n = len(df)
    st.subheader(f"Day-by-day ET0 comparison ({n} matched days)")

    chart_cols = [c for c in ["open_meteo_et0_mm_day", "fao56_et0_mm_day"] if c in df.columns]
    if chart_cols and "date" in df.columns:
        fig = px.line(
            df,
            x="date",
            y=chart_cols,
            title="Open-Meteo ET0 vs FAO-56 ET0 (mm/day)",
            labels={
                "date": "Date",
                "value": "ET0 (mm/day)",
                "variable": "Source",
            },
        )
        fig.for_each_trace(lambda t: t.update(
            name=t.name
            .replace("open_meteo_et0_mm_day", "Open-Meteo ET0")
            .replace("fao56_et0_mm_day", "FAO-56 ET0")
        ))
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("View comparison data table"):
        display_df = df.copy()
        if "date" in display_df.columns:
            display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
        st.dataframe(display_df, use_container_width=True)
