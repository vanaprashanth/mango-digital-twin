from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from app.sections.freshness import show_freshness_indicator


def render_mango_phenology_page(phenology_df: pd.DataFrame | None) -> None:
    """Render the Mango Phenology Calendar dashboard page."""

    st.title("Mango Phenology Calendar")
    show_freshness_indicator(phenology_df, label="Mango phenology", staleness_warning_days=7)

    st.warning(
        "This is a simplified, regional (Andhra Pradesh / South India) mango phenology "
        "calendar. It is not cultivar-specific yet, it is not field-calibrated yet (no actual "
        "bloom/fruit-set/harvest dates from this orchard have been used), and every date is "
        "assigned a stage purely from the calendar day-of-year, regardless of that year's "
        "actual weather. It will later be used to make the FAO-56 water balance's crop "
        "coefficient (Kc) and the irrigation/heat/disease risk thresholds stage-aware — that "
        "wiring has not happened yet."
    )

    if phenology_df is None or phenology_df.empty:
        st.warning("Mango phenology calendar file not found or could not be loaded.")
        st.info("Please run: python src/phenology/mango_phenology_calendar.py")
        st.info(
            "(That script needs the combined feature table to already exist — "
            "see `python src/features/build_feature_table.py` — only its date range is used.)"
        )
    else:
        st.caption(
            "One growth stage is assigned to every calendar date using fixed, documented "
            "month/day boundaries (see the script's module docstring for the exact cutover "
            "rules). This is a separate, standalone signal — it is not yet merged into the "
            "FAO-56 water balance or the irrigation/heat/disease risk scores."
        )

        phenology_latest = phenology_df.iloc[-1]

        st.subheader("Current Mango Stage")

        phen_col1, phen_col2, phen_col3, phen_col4, phen_col5 = st.columns(5)

        with phen_col1:
            st.metric(label="Latest date", value=phenology_latest["date"].strftime("%Y-%m-%d"))

        with phen_col2:
            st.metric(label="Current mango stage", value=phenology_latest["mango_stage"])

        with phen_col3:
            st.metric(label="Water sensitivity", value=phenology_latest["water_sensitivity"])

        with phen_col4:
            st.metric(label="Heat sensitivity", value=phenology_latest["heat_sensitivity"])

        with phen_col5:
            st.metric(label="Disease sensitivity", value=phenology_latest["disease_sensitivity"])

        st.info(f"**Stage description:** {phenology_latest['stage_description']}")
        st.info(f"**Recommended monitoring focus:** {phenology_latest['recommended_monitoring_focus']}")

        st.divider()

        st.subheader("Stage Counts (full date range)")

        stage_order = [
            "Flowering",
            "Fruit set",
            "Fruit development",
            "Maturity / harvest",
            "Rest / vegetative phase",
            "Flower induction / pre-flowering",
        ]

        stage_counts_df = (
            phenology_df["mango_stage"]
            .value_counts()
            .reindex(stage_order, fill_value=0)
            .rename_axis("mango_stage")
            .reset_index(name="days")
        )
        stage_count_fig = px.bar(
            stage_counts_df, x="mango_stage", y="days",
            title="Number of Days per Mango Stage (full historical date range)",
            labels={"mango_stage": "Mango stage", "days": "Number of days"},
        )
        st.plotly_chart(stage_count_fig, use_container_width=True)

        st.subheader("Mango Stage Timeline")
        st.caption(
            "Each stage is shown as a numbered band over time so growth-stage transitions are "
            "visible at a glance."
        )

        stage_code_map = {name: i for i, name in enumerate(stage_order)}
        timeline_df = phenology_df.copy()
        timeline_df["stage_code"] = timeline_df["mango_stage"].map(stage_code_map)

        timeline_fig = px.scatter(
            timeline_df, x="date", y="mango_stage",
            title="Mango Growth Stage Over Time",
            labels={"date": "Date", "mango_stage": "Mango stage"},
            category_orders={"mango_stage": stage_order},
        )
        timeline_fig.update_traces(marker=dict(size=4))
        st.plotly_chart(timeline_fig, use_container_width=True)

        st.subheader("Monthly Stage Distribution")

        monthly_stage_df = phenology_df.copy()
        monthly_stage_df["month_name"] = monthly_stage_df["date"].dt.strftime("%b")
        monthly_stage_df["month_num"] = monthly_stage_df["date"].dt.month

        monthly_stage_table = (
            monthly_stage_df.groupby(["month_num", "month_name", "mango_stage"])
            .size()
            .reset_index(name="days")
            .sort_values(["month_num"])
        )

        monthly_stage_pivot = monthly_stage_table.pivot_table(
            index=["month_num", "month_name"], columns="mango_stage", values="days", fill_value=0
        ).reset_index().sort_values("month_num").drop(columns="month_num").rename(columns={"month_name": "Month"})

        with st.expander("Monthly stage distribution table", expanded=False):
            st.dataframe(monthly_stage_pivot, use_container_width=True)

        monthly_stage_fig = px.bar(
            monthly_stage_table, x="month_name", y="days", color="mango_stage",
            title="Mango Stage Distribution by Month (stacked, full historical range)",
            labels={"month_name": "Month", "days": "Number of days", "mango_stage": "Mango stage"},
            category_orders={
                "month_name": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                "mango_stage": stage_order,
            },
        )
        st.plotly_chart(monthly_stage_fig, use_container_width=True)

        st.divider()

        st.subheader("About This Calendar")
        st.write("- This is a **simplified regional phenology calendar** for mango in Andhra Pradesh / South India, not a field-measured calendar for this specific orchard.")
        st.write("- It is **not yet calibrated to a specific cultivar** (e.g. Banganapalli, Totapuri, Alphonso/Benishan bloom and harvest timing can differ).")
        st.write("- It **does not yet use field observations** — no actual bloom, fruit-set, or harvest dates from this orchard have been recorded or used.")
        st.write("- It will **later** be used to make the FAO-56 water balance's crop coefficient (Kc) and the irrigation/heat/disease risk thresholds stage-aware — that wiring has not happened yet.")

        st.divider()

        st.subheader("Raw Mango Phenology Calendar Table")

        with st.expander("Mango phenology calendar table (full)", expanded=False):
            phenology_preview = phenology_df.copy()
            phenology_preview["date"] = phenology_preview["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(phenology_preview, use_container_width=True)
