from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from app.sections.freshness import show_freshness_indicator
from app.utils.date_filters import filter_by_date_range, render_date_range_selector


def render_historical_risk_page(df: pd.DataFrame) -> None:
    """Render the Historical Risk dashboard page."""

    st.title("Historical Risk")

    show_freshness_indicator(df, label="Historical risk", staleness_warning_days=7)

    selected_range = render_date_range_selector(
        key="historical_risk_date_range", default="1 year"
    )
    filtered_df = filter_by_date_range(df, selected_range=selected_range)

    if filtered_df.empty:
        st.warning(
            f"No historical risk data in the selected window ({selected_range}). "
            "Try a wider time range."
        )
        return

    st.caption(f"Selected period: **{selected_range}** — "
               f"{len(filtered_df)} days shown out of {len(df)} total.")

    st.divider()

    st.subheader("Rainfall Trend")
    rain_fig = px.line(
        filtered_df, x="date", y=["rainfall_mm", "rainfall_7day_mm"],
        title="Daily Rainfall and 7-Day Rolling Rainfall",
        labels={"date": "Date", "value": "Rainfall (mm)", "variable": "Metric"}
    )
    st.plotly_chart(rain_fig, use_container_width=True)

    st.subheader("Temperature Trend")
    temp_fig = px.line(
        filtered_df, x="date", y=["temperature_avg_c", "temperature_max_c", "temperature_min_c"],
        title="Average, Maximum, and Minimum Temperature",
        labels={"date": "Date", "value": "Temperature (\u00b0C)", "variable": "Metric"}
    )
    st.plotly_chart(temp_fig, use_container_width=True)

    st.subheader("Risk Score Trend")
    risk_fig = px.line(
        filtered_df, x="date",
        y=["irrigation_risk_score", "heat_stress_risk_score", "disease_risk_score"],
        title="Mango Risk Scores Over Time",
        labels={"date": "Date", "value": "Risk score", "variable": "Risk type"}
    )
    st.plotly_chart(risk_fig, use_container_width=True)

    st.divider()

    st.subheader("Risk Summary")

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.write("**Irrigation Risk Days**")
        irrigation_counts = filtered_df["irrigation_risk_level"].value_counts().reindex(["Low", "Medium", "High"], fill_value=0)
        st.dataframe(irrigation_counts.rename("Days"), use_container_width=True)

    with summary_col2:
        st.write("**Heat Stress Risk Days**")
        heat_counts = filtered_df["heat_stress_risk_level"].value_counts().reindex(["Low", "Medium", "High"], fill_value=0)
        st.dataframe(heat_counts.rename("Days"), use_container_width=True)

    with summary_col3:
        st.write("**Disease Risk Days**")
        disease_counts = filtered_df["disease_risk_level"].value_counts().reindex(["Low", "Medium", "High"], fill_value=0)
        st.dataframe(disease_counts.rename("Days"), use_container_width=True)

    st.divider()

    st.subheader("Monthly Risk Summary")

    monthly_df = filtered_df.copy()
    monthly_df["month"] = monthly_df["date"].dt.to_period("M").astype(str)

    monthly_summary = (
        monthly_df.groupby("month").agg(
            avg_irrigation_risk=("irrigation_risk_score", "mean"),
            avg_heat_stress_risk=("heat_stress_risk_score", "mean"),
            avg_disease_risk=("disease_risk_score", "mean"),
            total_rainfall_mm=("rainfall_mm", "sum"),
            avg_max_temperature_c=("temperature_max_c", "mean"),
        ).reset_index()
    )

    monthly_summary = monthly_summary.round({
        "avg_irrigation_risk": 2, "avg_heat_stress_risk": 2, "avg_disease_risk": 2,
        "total_rainfall_mm": 2, "avg_max_temperature_c": 2,
    })

    with st.expander("Monthly risk summary table", expanded=False):
        st.dataframe(monthly_summary, use_container_width=True)

    if not monthly_summary.empty:
        highest_irrigation_month = monthly_summary.loc[monthly_summary["avg_irrigation_risk"].idxmax()]
        highest_heat_month = monthly_summary.loc[monthly_summary["avg_heat_stress_risk"].idxmax()]
        highest_disease_month = monthly_summary.loc[monthly_summary["avg_disease_risk"].idxmax()]

        risk_month_col1, risk_month_col2, risk_month_col3 = st.columns(3)

        with risk_month_col1:
            st.metric(label="Highest irrigation-risk month", value=highest_irrigation_month["month"], delta=f"{highest_irrigation_month['avg_irrigation_risk']:.2f}")

        with risk_month_col2:
            st.metric(label="Highest heat-risk month", value=highest_heat_month["month"], delta=f"{highest_heat_month['avg_heat_stress_risk']:.2f}")

        with risk_month_col3:
            st.metric(label="Highest disease-risk month", value=highest_disease_month["month"], delta=f"{highest_disease_month['avg_disease_risk']:.2f}")
