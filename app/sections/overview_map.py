from __future__ import annotations

import pandas as pd
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

    st.subheader("Study Area Map")

    map_df = pd.DataFrame(
        {"lat": [config.latitude], "lon": [config.longitude]}
    )
    st.map(map_df, zoom=10)
    st.caption(
        f"Latitude {config.latitude}, Longitude {config.longitude} — "
        f"{config.study_area.name}, {config.study_area.district}, {config.study_area.state}, {config.study_area.country}"
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
