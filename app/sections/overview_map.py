from __future__ import annotations

import pandas as pd
import plotly.express as px
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


def render_overview_map_page(
    config,
    latest: "pd.Series",
    has_soil_adjusted_irrigation: bool,
    combined_feature_df: "pd.DataFrame | None" = None,
) -> None:
    """Render the Overview & Map dashboard page."""

    st.title("\U0001f96d Sensor-Free Mango Digital Twin")
    show_freshness_indicator(label="Overview", staleness_warning_days=0)
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

    # Detect Streamlit theme and pick the appropriate tile style.
    # carto-darkmatter is dark, carto-positron is light — both are token-free.
    try:
        _theme_base = st.get_option("theme.base")
    except Exception:
        _theme_base = None
    _map_style = "carto-darkmatter" if _theme_base == "dark" else "carto-positron"
    # Marker colour stays red on the dark basemap (visible against dark tiles);
    # use a brighter orange-red on light tiles for consistency.
    _marker_color = "#ff4444" if _theme_base == "dark" else "red"

    map_fig = px.scatter_mapbox(
        map_df,
        lat="lat",
        lon="lon",
        hover_name="location",
        zoom=8,
        height=450,
        center={"lat": config.latitude, "lon": config.longitude},
    )
    map_fig.update_traces(marker=dict(size=14, color=_marker_color))
    map_fig.update_layout(
        mapbox_style=_map_style,
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

    # -----------------------------------------------------------------------
    # Remote Sensing Freshness
    # -----------------------------------------------------------------------
    st.subheader("Remote Sensing Freshness")

    if combined_feature_df is None or combined_feature_df.empty:
        st.info(
            "Combined feature table not available. "
            "Run `python main.py` to generate remote sensing freshness data."
        )
    else:
        _cf = combined_feature_df.sort_values("date").iloc[-1]

        def _rs_str(val, fallback: str = "N/A") -> str:
            """Safely format a potentially NaN/None/empty combined-table value."""
            if val is None:
                return fallback
            try:
                if pd.isna(val):
                    return fallback
            except (TypeError, ValueError):
                pass
            s = str(val).strip()
            return s if s else fallback

        def _days_str(raw) -> str:
            """Format a days-since float/int into a readable string."""
            if raw is None:
                return "N/A"
            try:
                if pd.isna(raw):
                    return "N/A"
                return f"{int(float(raw))} days ago"
            except (TypeError, ValueError):
                return "N/A"

        # Sentinel-2 fields
        s2_date_str = _rs_str(_cf.get("sentinel2_date"))
        s2_days_str = _days_str(_cf.get("days_since_sentinel2_observation"))
        s2_freshness = _rs_str(_cf.get("vegetation_data_freshness"), "Missing")

        # Sentinel-1 fields — column may be absent in CSVs generated before S1 support
        _has_s1_cols = "sentinel1_freshness_level" in combined_feature_df.columns
        if _has_s1_cols:
            s1_date_str = _rs_str(_cf.get("sentinel1_date"))
            s1_days_str = _days_str(_cf.get("days_since_sentinel1_observation"))
            s1_freshness = _rs_str(_cf.get("sentinel1_freshness_level"), "Missing")
        else:
            s1_date_str = s1_days_str = "N/A"
            s1_freshness = "Missing"

        # Two-column layout: S2 left, S1 right
        rs_col1, rs_col2 = st.columns(2)

        with rs_col1:
            st.markdown("**Sentinel-2 Optical**")
            st.metric("Last observation", s2_date_str)
            st.metric("Days since", s2_days_str)
            st.metric("Freshness", s2_freshness)

        with rs_col2:
            st.markdown("**Sentinel-1 SAR (Cloudy-Season Fallback)**")
            if not _has_s1_cols:
                st.info(
                    "SAR fallback not available yet. "
                    "Run `python main.py --refresh-sentinel2` with GEE credentials."
                )
            else:
                st.metric("Last SAR observation", s1_date_str)
                st.metric("Days since", s1_days_str)
                st.metric("SAR freshness", s1_freshness)

        # Fallback status banner
        _s2_recent = s2_freshness in ("Fresh", "Moderate")
        _s1_recent = _has_s1_cols and s1_freshness in ("Fresh", "Moderate")
        _s2_missing = s2_freshness == "Missing"
        _s1_missing = not _has_s1_cols or s1_freshness == "Missing"

        if _s2_missing and _s1_missing:
            st.warning(
                "⚠️ **Remote sensing unavailable** — no Sentinel-2 or Sentinel-1 data "
                "found. Run `python main.py --refresh-sentinel2` with GEE credentials configured."
            )
        elif not _s2_recent and _s1_recent:
            st.info(
                "📡 **SAR fallback active** — Sentinel-2 optical data is stale, likely "
                "due to cloud cover. Sentinel-1 SAR provides radar-based proxy signals "
                "for cloudy-season continuity."
            )
        elif _s2_recent and _s1_recent:
            st.success(
                "✅ **Optical and SAR both recent** — Sentinel-2 optical and Sentinel-1 "
                "SAR data are both current."
            )
        elif _s2_recent:
            st.success(
                "✅ **Optical observation current.** "
                "Sentinel-1 SAR data is stale or unavailable."
            )
        else:
            st.warning(
                "⚠️ **Remote sensing stale** — both Sentinel-2 optical and Sentinel-1 "
                "SAR data are stale or missing. Run `python main.py --refresh-sentinel2` "
                "with GEE credentials configured."
            )

        st.caption(
            "Sentinel-2 is optical and may be stale during cloudy periods. "
            "Sentinel-1 SAR provides radar-based proxy continuity — not NDVI or "
            "field-calibrated soil moisture."
        )

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
