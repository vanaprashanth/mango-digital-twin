from __future__ import annotations

import pandas as pd
import streamlit as st
from app.sections.freshness import show_freshness_indicator

from src.utils.soil_factor import soil_factor_label


def _risk_color(level: str) -> str:
    """Return emoji indicator based on risk level."""
    if level == "High":
        return "\U0001f534 High"
    elif level == "Medium":
        return "\U0001f7e0 Medium"
    else:
        return "\U0001f7e2 Low"


def render_soil_intelligence_page(
    soil_df: pd.DataFrame | None,
    latest: "pd.Series | None",
    has_soil_adjusted_irrigation: bool,
) -> None:
    """Render the Soil Intelligence dashboard page."""

    st.title("Soil Intelligence")
    show_freshness_indicator(label="Soil intelligence", staleness_warning_days=0)

    if soil_df is None or soil_df.empty:
        st.warning("SoilGrids data file not found.")
        st.info("Please run: python src/soil/fetch_soilgrids.py")
    else:
        topsoil_summary = (
            soil_df.groupby("property").agg(
                average_0_30cm=("converted_value", "mean"),
                unit=("unit", "first"),
            ).reset_index()
        )

        soil_lookup = {row["property"]: row["average_0_30cm"] for _, row in topsoil_summary.iterrows()}

        soil_col1, soil_col2, soil_col3, soil_col4 = st.columns(4)

        with soil_col1:
            st.metric(label="Soil pH", value=f"{soil_lookup.get('phh2o', 0):.2f}")

        with soil_col2:
            st.metric(label="Sand", value=f"{soil_lookup.get('sand', 0):.2f} %")

        with soil_col3:
            st.metric(label="Silt", value=f"{soil_lookup.get('silt', 0):.2f} %")

        with soil_col4:
            st.metric(label="Clay", value=f"{soil_lookup.get('clay', 0):.2f} %")

        soil_col5, soil_col6, soil_col7, soil_col8 = st.columns(4)

        with soil_col5:
            st.metric(label="Organic carbon", value=f"{soil_lookup.get('soc', 0):.2f} g/kg")

        with soil_col6:
            st.metric(label="Bulk density", value=f"{soil_lookup.get('bdod', 0):.2f} g/cm\u00b3")

        with soil_col7:
            st.metric(label="CEC", value=f"{soil_lookup.get('cec', 0):.2f} cmol(c)/kg")

        with soil_col8:
            soil_factor = latest.get("soil_irrigation_factor", 1.0) if latest is not None else 1.0
            st.metric(label="Soil irrigation factor", value=f"{soil_factor:.2f}", delta=soil_factor_label(soil_factor))

        if has_soil_adjusted_irrigation and latest is not None:
            st.metric(
                label="Soil-adjusted irrigation risk",
                value=_risk_color(latest["soil_adjusted_irrigation_risk_level"]),
                delta=f"{latest['soil_adjusted_irrigation_risk_score']:.2f}"
            )

        sand = soil_lookup.get("sand", 0)
        clay = soil_lookup.get("clay", 0)
        ph = soil_lookup.get("phh2o", 0)
        soc = soil_lookup.get("soc", 0)
        soil_factor = latest.get("soil_irrigation_factor", 1.0) if latest is not None else 1.0

        st.write("### Soil Interpretation")

        soil_notes = []

        if clay >= 35:
            soil_notes.append("Clay content is high, so the soil may hold water better than sandy soil but may drain more slowly.")
        elif clay >= 20:
            soil_notes.append("Clay content is moderate, giving the soil reasonable water-holding capacity.")
        else:
            soil_notes.append("Clay content is low, so the soil may lose water faster and irrigation risk can increase quickly.")

        if sand >= 50:
            soil_notes.append("Sand content is high, which may improve drainage but reduce water retention.")
        elif sand >= 30:
            soil_notes.append("Sand content is moderate, supporting drainage while still allowing some water retention.")
        else:
            soil_notes.append("Sand content is low, so drainage may be slower.")

        if 6.0 <= ph <= 7.5:
            soil_notes.append("Soil pH is near the generally suitable range for mango cultivation.")
        elif ph < 6.0:
            soil_notes.append("Soil pH is acidic and may require soil management depending on crop response.")
        else:
            soil_notes.append("Soil pH is alkaline and may affect nutrient availability.")

        if soc >= 15:
            soil_notes.append("Organic carbon is relatively good and can support soil structure and water retention.")
        elif soc >= 8:
            soil_notes.append("Organic carbon is moderate; compost, mulch, or organic amendments may improve soil health.")
        else:
            soil_notes.append("Organic carbon is low, so improving organic matter may help water retention and soil health.")

        if soil_factor < 0.95:
            soil_notes.append(f"The soil irrigation adjustment factor is {soil_factor:.2f}, meaning this soil reduces estimated irrigation risk because of better water-retention behavior.")
        elif soil_factor > 1.05:
            soil_notes.append(f"The soil irrigation adjustment factor is {soil_factor:.2f}, meaning this soil increases estimated irrigation risk because water may drain or deplete faster.")
        else:
            soil_notes.append(f"The soil irrigation adjustment factor is {soil_factor:.2f}, meaning soil has a mostly neutral effect on irrigation risk.")

        for note in soil_notes:
            st.write(f"- {note}")

        soil_summary_display = topsoil_summary.copy()
        soil_summary_display["average_0_30cm"] = soil_summary_display["average_0_30cm"].round(2)

        with st.expander("SoilGrids 0\u201330 cm summary table", expanded=False):
            st.dataframe(soil_summary_display, use_container_width=True)
