from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


def _risk_color(level: str) -> str:
    """Return emoji indicator based on risk level."""
    if level == "High":
        return "\U0001f534 High"
    elif level == "Medium":
        return "\U0001f7e0 Medium"
    else:
        return "\U0001f7e2 Low"


def render_water_balance_page(fao56_water_balance_df: pd.DataFrame | None) -> None:
    """Render the Water Balance (FAO-56) dashboard page."""

    st.title("Water Balance (FAO-56)")

    st.warning(
        "This FAO-56 page is a simplified rainfed prototype. It does not yet include actual "
        "irrigation events, runoff, deep percolation, phenology-aware crop coefficients, or "
        "field validation."
    )

    if fao56_water_balance_df is None or fao56_water_balance_df.empty:
        st.warning("FAO-56 water balance file not found or could not be loaded.")
        st.info("Please run: python src/water_balance/fao56_water_balance.py")
        st.info(
            "(That script needs the combined feature table to already exist — "
            "see `python src/features/build_feature_table.py`.)"
        )
    else:
        st.caption(
            "Daily reference evapotranspiration (ET0), estimated crop water use (ETc), and a "
            "root-zone soil-water depletion balance computed with the FAO-56 Penman-Monteith "
            "method (Allen et al., 1998). This is a separate, standalone signal — it is not yet "
            "merged into the irrigation/heat/disease risk scores or the dashboard's other pages."
        )

        fao56_latest = fao56_water_balance_df.iloc[-1]

        st.subheader("Latest Water Balance Status")

        fao56_col1, fao56_col2, fao56_col3, fao56_col4 = st.columns(4)

        with fao56_col1:
            st.metric(label="Latest date", value=fao56_latest["date"].strftime("%Y-%m-%d"))

        with fao56_col2:
            st.metric(label="Latest ET0", value=f"{fao56_latest['et0_mm']:.2f} mm/day")

        with fao56_col3:
            st.metric(label="Latest ETc", value=f"{fao56_latest['etc_mm']:.2f} mm/day")

        with fao56_col4:
            st.metric(label="Latest root-zone depletion", value=f"{fao56_latest['root_zone_depletion_mm']:.1f} mm")

        fao56_col5, fao56_col6, fao56_col7, fao56_col8 = st.columns(4)

        with fao56_col5:
            st.metric(
                label="Latest Ks (water-stress coefficient)",
                value=f"{fao56_latest['water_stress_coefficient_ks']:.2f}",
            )

        with fao56_col6:
            st.metric(label="Latest water-stress level", value=_risk_color(fao56_latest["water_stress_level"]))

        with fao56_col7:
            st.metric(label="TAW (total available water)", value=f"{fao56_latest['taw_mm']:.1f} mm")

        with fao56_col8:
            st.metric(label="RAW (readily available water)", value=f"{fao56_latest['raw_mm']:.1f} mm")

        st.divider()

        st.subheader("Water Balance Trends")

        et_fig = px.line(
            fao56_water_balance_df, x="date", y=["et0_mm", "etc_mm"],
            title="ET0 and ETc Over Time",
            labels={"date": "Date", "value": "mm/day", "variable": "Metric"},
        )
        st.plotly_chart(et_fig, use_container_width=True)

        st.caption(
            "Rainfall and ETc plotted together (different scales), since rainfall events and "
            "crop water use both drive the daily depletion balance."
        )
        rain_etc_fig = make_subplots(specs=[[{"secondary_y": True}]])
        rain_etc_fig.add_trace(
            go.Bar(
                x=fao56_water_balance_df["date"], y=fao56_water_balance_df["rainfall_mm"],
                name="Rainfall (mm)",
            ),
            secondary_y=False,
        )
        rain_etc_fig.add_trace(
            go.Scatter(
                x=fao56_water_balance_df["date"], y=fao56_water_balance_df["etc_mm"],
                name="ETc (mm/day)", mode="lines",
            ),
            secondary_y=True,
        )
        rain_etc_fig.update_layout(title="Rainfall and ETc Over Time")
        rain_etc_fig.update_xaxes(title_text="Date")
        rain_etc_fig.update_yaxes(title_text="Rainfall (mm)", secondary_y=False)
        rain_etc_fig.update_yaxes(title_text="ETc (mm/day)", secondary_y=True)
        st.plotly_chart(rain_etc_fig, use_container_width=True)

        depletion_fig = px.line(
            fao56_water_balance_df, x="date", y="root_zone_depletion_mm",
            title="Root-Zone Depletion Over Time",
            labels={"date": "Date", "root_zone_depletion_mm": "Depletion (mm)"},
        )
        depletion_fig.add_hline(
            y=fao56_latest["raw_mm"], line_dash="dash", line_color="orange",
            annotation_text="RAW (stress begins)",
        )
        depletion_fig.add_hline(
            y=fao56_latest["taw_mm"], line_dash="dash", line_color="red",
            annotation_text="TAW (all available water gone)",
        )
        st.plotly_chart(depletion_fig, use_container_width=True)

        ks_fig = px.line(
            fao56_water_balance_df, x="date", y="water_stress_coefficient_ks",
            title="Ks Water-Stress Coefficient Over Time",
            labels={"date": "Date", "water_stress_coefficient_ks": "Ks"},
        )
        st.plotly_chart(ks_fig, use_container_width=True)

        stress_level_counts_df = (
            fao56_water_balance_df["water_stress_level"]
            .value_counts()
            .reindex(["Low", "Medium", "High"], fill_value=0)
            .rename_axis("water_stress_level")
            .reset_index(name="days")
        )
        stress_level_fig = px.bar(
            stress_level_counts_df, x="water_stress_level", y="days",
            title="Water-Stress Level Counts (full date range)",
            labels={"water_stress_level": "Water-stress level", "days": "Number of days"},
        )
        st.plotly_chart(stress_level_fig, use_container_width=True)

        st.divider()

        st.subheader("Interpretation")

        st.write("- **ET0** is atmospheric evaporative demand — how much water the air/sun/wind could pull from a reference surface that day.")
        st.write("- **ETc** is estimated crop water use, derived from ET0 and a crop coefficient (Kc).")
        st.write("- **Depletion** is how much water has been removed from the root zone since it was last at field capacity.")
        st.write("- **Ks** is the water-stress coefficient — 1.0 means no stress, and lower values mean stronger water stress.")
        st.write("- **TAW** is total available water — the maximum water the root zone can hold and still release to the crop.")
        st.write("- **RAW** is readily available water — the portion of TAW that can be used before water stress (Ks < 1) begins.")

        st.divider()

        st.subheader("Raw FAO-56 Water Balance Table")

        with st.expander("FAO-56 water balance table (full)", expanded=False):
            fao56_preview = fao56_water_balance_df.copy()
            fao56_preview["date"] = fao56_preview["date"].dt.strftime("%Y-%m-%d")
            numeric_columns = fao56_preview.select_dtypes(include="number").columns
            fao56_preview[numeric_columns] = fao56_preview[numeric_columns].round(3)
            st.dataframe(fao56_preview, use_container_width=True)
