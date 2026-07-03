from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from app.sections.freshness import show_freshness_indicator


def _risk_color(level: str) -> str:
    """Return emoji indicator based on risk level."""
    if level == "High":
        return "\U0001f534 High"
    elif level == "Medium":
        return "\U0001f7e0 Medium"
    else:
        return "\U0001f7e2 Low"


def render_combined_intelligence_page(combined_feature_df: pd.DataFrame | None) -> None:
    """Render the Combined Intelligence dashboard page."""

    st.title("Combined Intelligence")
    show_freshness_indicator(combined_feature_df, label="Combined intelligence", staleness_warning_days=7)

    if combined_feature_df is None or combined_feature_df.empty:
        st.warning("Combined feature table file not found or could not be loaded.")
        st.info("Please run: python src/features/build_feature_table.py")
        st.info(
            "(That script needs the historical risk CSV, the daily Sentinel-2 vegetation CSV, "
            "and the SoilGrids CSV to already exist.)"
        )
    else:
        st.caption(
            "This page combines historical weather risk, static soil intelligence, and "
            "nearest-previous Sentinel-2 vegetation observations. It does not use future "
            "satellite observations — every row only uses vegetation data that was actually "
            "available on or before that date."
        )

        combined_latest = combined_feature_df.iloc[-1]

        st.subheader("Latest Combined Status")

        combined_metric_col1, combined_metric_col2, combined_metric_col3, combined_metric_col4 = st.columns(4)

        with combined_metric_col1:
            st.metric(label="Latest date", value=combined_latest["date"].strftime("%Y-%m-%d"))

        with combined_metric_col2:
            st.metric(label="Irrigation risk", value=_risk_color(combined_latest["irrigation_risk_level"]))

        with combined_metric_col3:
            st.metric(label="Heat stress risk", value=_risk_color(combined_latest["heat_stress_risk_level"]))

        with combined_metric_col4:
            st.metric(label="Disease risk", value=_risk_color(combined_latest["disease_risk_level"]))

        combined_metric_col5, combined_metric_col6, combined_metric_col7, combined_metric_col8 = st.columns(4)

        with combined_metric_col5:
            ndvi_value = combined_latest["ndvi_mean"]
            st.metric(label="Latest NDVI", value=f"{ndvi_value:.3f}" if pd.notna(ndvi_value) else "N/A")

        with combined_metric_col6:
            ndmi_value = combined_latest["ndmi_mean"]
            st.metric(label="Latest NDMI", value=f"{ndmi_value:.3f}" if pd.notna(ndmi_value) else "N/A")

        with combined_metric_col7:
            st.metric(label="Vegetation freshness", value=combined_latest["vegetation_data_freshness"])

        with combined_metric_col8:
            st.metric(label="Soil irrigation factor", value=f"{combined_latest['soil_irrigation_factor']:.2f}")

        st.divider()

        st.subheader("Filters")

        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            combined_min_date = combined_feature_df["date"].min().date()
            combined_max_date = combined_feature_df["date"].max().date()

            combined_selected_range = st.date_input(
                "Date range",
                value=(combined_min_date, combined_max_date),
                min_value=combined_min_date,
                max_value=combined_max_date,
                key="combined_intelligence_date_range",
            )

        with filter_col2:
            freshness_options = ["Fresh", "Moderate", "Stale", "Missing"]
            selected_freshness = st.multiselect(
                "Vegetation freshness",
                options=freshness_options,
                default=freshness_options,
                key="combined_intelligence_freshness_filter",
            )

        if isinstance(combined_selected_range, tuple) and len(combined_selected_range) == 2:
            combined_start_date, combined_end_date = combined_selected_range
            filtered_combined_df = combined_feature_df[
                (combined_feature_df["date"].dt.date >= combined_start_date)
                & (combined_feature_df["date"].dt.date <= combined_end_date)
            ]
        else:
            filtered_combined_df = combined_feature_df.copy()

        if selected_freshness:
            filtered_combined_df = filtered_combined_df[
                filtered_combined_df["vegetation_data_freshness"].isin(selected_freshness)
            ]

        if filtered_combined_df.empty:
            st.warning("No rows match the selected date range and freshness filters.")
        else:
            st.divider()

            st.subheader("Risk Trends")

            irrigation_fig = px.line(
                filtered_combined_df, x="date", y="irrigation_risk_score",
                title="Irrigation Risk Score Over Time",
                labels={"date": "Date", "irrigation_risk_score": "Irrigation risk score"},
            )
            st.plotly_chart(irrigation_fig, use_container_width=True)

            disease_fig = px.line(
                filtered_combined_df, x="date", y="disease_risk_score",
                title="Disease Risk Score Over Time",
                labels={"date": "Date", "disease_risk_score": "Disease risk score"},
            )
            st.plotly_chart(disease_fig, use_container_width=True)

            st.subheader("Vegetation Trends")

            ndvi_combined_fig = px.line(
                filtered_combined_df, x="date", y="ndvi_mean",
                title="NDVI Over Time (matched Sentinel-2 observation)",
                labels={"date": "Date", "ndvi_mean": "NDVI"},
            )
            st.plotly_chart(ndvi_combined_fig, use_container_width=True)

            ndmi_combined_fig = px.line(
                filtered_combined_df, x="date", y="ndmi_mean",
                title="NDMI Over Time (matched Sentinel-2 observation)",
                labels={"date": "Date", "ndmi_mean": "NDMI"},
            )
            st.plotly_chart(ndmi_combined_fig, use_container_width=True)

            st.subheader("Irrigation Risk vs. NDVI")
            st.caption(
                "Irrigation risk score (left axis) and NDVI (right axis) plotted together, "
                "since they use different scales."
            )

            dual_axis_fig = make_subplots(specs=[[{"secondary_y": True}]])
            dual_axis_fig.add_trace(
                go.Scatter(
                    x=filtered_combined_df["date"], y=filtered_combined_df["irrigation_risk_score"],
                    name="Irrigation risk score", mode="lines",
                ),
                secondary_y=False,
            )
            dual_axis_fig.add_trace(
                go.Scatter(
                    x=filtered_combined_df["date"], y=filtered_combined_df["ndvi_mean"],
                    name="NDVI", mode="lines",
                ),
                secondary_y=True,
            )
            dual_axis_fig.update_layout(title="Irrigation Risk Score and NDVI Over Time")
            dual_axis_fig.update_xaxes(title_text="Date")
            dual_axis_fig.update_yaxes(title_text="Irrigation risk score", secondary_y=False)
            dual_axis_fig.update_yaxes(title_text="NDVI", secondary_y=True)
            st.plotly_chart(dual_axis_fig, use_container_width=True)

            st.subheader("Vegetation Data Freshness")

            freshness_counts_df = (
                filtered_combined_df["vegetation_data_freshness"]
                .value_counts()
                .reindex(freshness_options, fill_value=0)
                .rename_axis("freshness")
                .reset_index(name="days")
            )
            freshness_fig = px.bar(
                freshness_counts_df, x="freshness", y="days",
                title="Vegetation Data Freshness (days in selected range)",
                labels={"freshness": "Freshness", "days": "Number of days"},
            )
            st.plotly_chart(freshness_fig, use_container_width=True)

        st.divider()

        st.subheader("Interpretation")
        st.caption("Based on the latest combined row, not the filtered selection above.")

        interpretation_notes = []

        if (
            combined_latest["irrigation_risk_level"] == "High"
            and combined_latest["moisture_level"] == "Dry vegetation / moisture stress"
        ):
            interpretation_notes.append(
                ("warning", "Possible water stress: irrigation risk is high and the matched "
                            "Sentinel-2 observation shows dry vegetation / moisture stress (low NDMI).")
            )

        if combined_latest["disease_risk_level"] == "High" and (
            combined_latest["relative_humidity_percent"] >= 75
            or combined_latest["rainfall_3day_mm"] >= 20
        ):
            interpretation_notes.append(
                ("warning", "Disease-friendly conditions: disease risk is high alongside high "
                            "humidity and/or recent rainfall.")
            )

        if combined_latest["ndvi_level"] == "Low vegetation greenness" and (
            combined_latest["irrigation_risk_level"] == "High"
            or combined_latest["heat_stress_risk_level"] == "High"
            or combined_latest["disease_risk_level"] == "High"
        ):
            interpretation_notes.append(
                ("warning", "Possible combined stress: NDVI shows low vegetation greenness while "
                            "at least one weather risk score is high.")
            )

        if combined_latest["vegetation_data_freshness"] in ("Stale", "Missing"):
            interpretation_notes.append(
                ("info", f"Vegetation data freshness is '{combined_latest['vegetation_data_freshness']}' "
                         "for the latest date — the matched Sentinel-2 observation may be outdated or "
                         "may not exist yet, so vegetation-based interpretation should be treated with caution.")
            )

        if not interpretation_notes:
            st.info("No combined-stress conditions flagged for the latest date based on the rules above.")
        else:
            for level, note in interpretation_notes:
                if level == "warning":
                    st.warning(note)
                else:
                    st.info(note)

        st.divider()

        st.subheader("Raw Combined Feature Table")

        with st.expander("Combined feature table (filtered by the selections above)", expanded=False):
            combined_preview = filtered_combined_df.copy()
            combined_preview["date"] = combined_preview["date"].dt.strftime("%Y-%m-%d")
            if "sentinel2_date" in combined_preview.columns:
                combined_preview["sentinel2_date"] = combined_preview["sentinel2_date"].dt.strftime("%Y-%m-%d")
            numeric_columns = combined_preview.select_dtypes(include="number").columns
            combined_preview[numeric_columns] = combined_preview[numeric_columns].round(3)
            st.dataframe(combined_preview, use_container_width=True)
