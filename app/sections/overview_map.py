from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def _risk_color(level: str) -> str:
    """Return emoji indicator based on risk level."""
    if level == "High":
        return "\U0001f534 High"
    elif level == "Medium":
        return "\U0001f7e0 Medium"
    else:
        return "\U0001f7e2 Low"


def render_overview_map_page(config, latest: "pd.Series", has_soil_adjusted_irrigation: bool) -> None:
    """Render the Overview & Map dashboard page."""

    st.title("\U0001f96d Sensor-Free Mango Digital Twin")
    st.caption(f"{config.study_area.name}, {config.study_area.district} district, {config.study_area.state}")

    st.subheader("Latest Digital Twin Status")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(label="Latest valid date", value=latest["date"].strftime("%Y-%m-%d"))

    with col2:
        st.metric(label="Irrigation risk (weather only)", value=_risk_color(latest["irrigation_risk_level"]))

    with col3:
        if has_soil_adjusted_irrigation:
            st.metric(label="Irrigation risk (soil-adjusted)", value=_risk_color(latest["soil_adjusted_irrigation_risk_level"]))
        else:
            st.metric(label="Irrigation risk (soil-adjusted)", value="N/A")

    with col4:
        st.metric(label="Heat stress risk", value=_risk_color(latest["heat_stress_risk_level"]))

    with col5:
        st.metric(label="Disease risk", value=_risk_color(latest["disease_risk_level"]))

    st.divider()

    # -----------------------------------------------------------------------
    # Study Area Map
    # -----------------------------------------------------------------------
    # Design decision: the map is intentionally zoomed in to the study area in
    # Chittoor / Andhra Pradesh (zoom 8).  At this zoom level the viewport covers
    # roughly southern Andhra Pradesh, Karnataka, and Tamil Nadu — the disputed
    # northern borders (~2 000 km north) are entirely off-screen.
    #
    # The basemap style is "carto-positron", a minimal neutral tile layer that
    # renders roads and terrain without prominently labelling or drawing
    # administrative/political boundaries.  This dashboard does not use the
    # basemap as an authoritative source of any political boundary.
    # -----------------------------------------------------------------------

    st.subheader("Study Area Map")

    map_df = pd.DataFrame(
        {"lat": [config.latitude], "lon": [config.longitude], "location": ["Study orchard"]}
    )

    map_fig = px.scatter_mapbox(
        map_df,
        lat="lat",
        lon="lon",
        hover_name="location",
        zoom=8,
        height=450,
        center={"lat": config.latitude, "lon": config.longitude},
    )
    map_fig.update_traces(marker=dict(size=14, color="red"))
    map_fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    st.plotly_chart(map_fig, use_container_width=True, config={"scrollZoom": True})

    st.caption(
        f"\U0001f4cd {config.study_area.name}, {config.study_area.district} district, "
        f"{config.study_area.state}, {config.study_area.country} "
        f"\u2014 {config.latitude}\u00b0 N, {config.longitude}\u00b0 E"
    )
    st.caption(
        "Map is focused on the study orchard location in Andhra Pradesh. "
        "Basemap boundary lines are provided by the tile provider and are not used "
        "as the authoritative boundary source."
    )

    with st.expander("India boundary layer \u2014 planned improvement", expanded=False):
        st.info(
            "**Status: not yet implemented.**\n\n"
            "A future update will overlay a reviewed India boundary on this map using "
            "an official or Survey of India-sourced GeoJSON file. This will replace "
            "dependence on the basemap tile provider for boundary rendering.\n\n"
            "Until that reviewed boundary file is added to the project, this dashboard "
            "deliberately avoids displaying a full India political map, because no "
            "third-party basemap tile provider is used as the authoritative source of "
            "India\u2019s boundaries, including Jammu & Kashmir and other sensitive regions."
        )

    st.divider()

    st.subheader("Latest Weather Conditions")

    weather_col1, weather_col2, weather_col3, weather_col4 = st.columns(4)

    with weather_col1:
        st.metric(label="Max temperature", value=f"{latest['temperature_max_c']:.2f} \u00b0C")

    with weather_col2:
        st.metric(label="Avg temperature", value=f"{latest['temperature_avg_c']:.2f} \u00b0C")

    with weather_col3:
        st.metric(label="Rainfall", value=f"{latest['rainfall_mm']:.2f} mm")

    with weather_col4:
        st.metric(label="7-day rainfall", value=f"{latest['rainfall_7day_mm']:.2f} mm")

    st.divider()

    st.subheader("Latest Recommendation")

    recommendations = []

    irrigation_level_for_advisory = (
        latest["soil_adjusted_irrigation_risk_level"]
        if has_soil_adjusted_irrigation
        else latest["irrigation_risk_level"]
    )

    if irrigation_level_for_advisory == "High":
        recommendations.append(
            "Irrigation attention is needed because recent rainfall is low and weather stress is elevated."
        )
    elif irrigation_level_for_advisory == "Medium":
        recommendations.append(
            "Monitor irrigation need. Rainfall or heat conditions may create moderate water stress."
        )
    else:
        recommendations.append(
            "Irrigation risk is currently low based on recent rainfall, temperature, and soil-adjusted water-retention behavior."
        )

    if latest["heat_stress_risk_level"] == "High":
        recommendations.append("Heat stress risk is high. Avoid crop operations during peak afternoon heat.")
    elif latest["heat_stress_risk_level"] == "Medium":
        recommendations.append("Moderate heat stress risk. Continue monitoring maximum temperature.")
    else:
        recommendations.append("Heat stress risk is currently low.")

    if latest["disease_risk_level"] == "High":
        recommendations.append("Disease-friendly weather conditions are high. Monitor orchard for fungal symptoms.")
    elif latest["disease_risk_level"] == "Medium":
        recommendations.append("Moderate disease-friendly conditions exist. Continue monitoring humidity and rainfall.")
    else:
        recommendations.append("Disease risk is currently low based on weather conditions.")

    for rec in recommendations:
        st.write(f"- {rec}")
