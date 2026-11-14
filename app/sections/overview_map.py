from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from app.sections.freshness import show_freshness_indicator
from app.theme import PALETTE, esc, kpi_card, page_header, section_header, status_pill


def _risk_color(level: str) -> str:
    """Return emoji indicator based on risk level."""
    if level == "High":
        return "\U0001f534 High"
    elif level == "Medium":
        return "\U0001f7e0 Medium"
    else:
        return "\U0001f7e2 Low"


def build_study_area_map(latitude: float, longitude: float, theme_base: str | None = None):
    """Build the Study Area map figure (Plotly >= 5.24 ``scatter_map`` API).

    carto-darkmatter is dark, carto-positron is light; both are token-free.
    Marker colour: "#ff4444" on dark tiles, "red" on light tiles.
    """
    map_df = pd.DataFrame({"lat": [latitude], "lon": [longitude], "location": ["Study orchard"]})
    dark = theme_base == "dark"
    map_style = "carto-darkmatter" if dark else "carto-positron"
    marker_color = "#ff4444" if dark else "red"

    fig = px.scatter_map(
        map_df,
        lat="lat",
        lon="lon",
        hover_name="location",
        zoom=8,
        height=450,
        center={"lat": latitude, "lon": longitude},
    )
    fig.update_traces(marker=dict(size=14, color=marker_color))
    fig.update_layout(
        map_style=map_style,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    return fig


_STATE_RANK = {"Fresh": 0, "Aging": 1, "Stale": 2, "Unknown": 3, "Missing": 4}


def satellite_freshness_summary(records: list[dict]) -> tuple[str, str]:
    """(state, note) for the Satellite freshness KPI from the Data Sources records.

    Sentinel-2 and Sentinel-1 keep their own source-specific states; the KPI shows the
    better of the two (either sensor being recent means usable satellite context).
    """
    by_key = {r["key"]: r for r in records}
    parts, states = [], []
    for key, label in (("sentinel2", "S2"), ("sentinel1", "S1")):
        r = by_key.get(key)
        if r is None:
            continue
        age = f"{r['age_days']}d" if r.get("age_days") is not None else r["state"].lower()
        parts.append(f"{label} {age}")
        states.append(r["state"])
    if not states:
        return "Unknown", "No satellite sources configured"
    return min(states, key=lambda x: _STATE_RANK.get(x, 9)), " \u00b7 ".join(parts)


def _level_state(level) -> "str | None":
    return level if level in ("Low", "Medium", "High") else None


def water_balance_trend_figure(fao56_df: "pd.DataFrame | None", days: int = 120):
    """Root-zone depletion trend with RAW / TAW reference lines; None if data unusable."""
    if fao56_df is None or fao56_df.empty or not {"date", "root_zone_depletion_mm"} <= set(fao56_df.columns):
        return None
    d = fao56_df.sort_values("date").tail(days)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d["date"], y=d["root_zone_depletion_mm"], mode="lines", name="Root-zone depletion",
        line=dict(color=PALETTE["blue"], width=2),
        hovertemplate="%{x|%Y-%m-%d}<br>Depletion: %{y:.1f} mm<extra></extra>",
    ))
    for col, label, colour in (("raw_mm", "RAW (stress onset)", PALETTE["gold"]),
                               ("taw_mm", "TAW (total available water)", PALETTE["red"])):
        if col in d.columns and d[col].notna().any():
            fig.add_hline(y=float(d[col].dropna().iloc[-1]), line_dash="dash", line_color=colour,
                          annotation_text=label, annotation_position="top left")
    fig.update_layout(height=320, yaxis_title="Depletion (mm)", xaxis_title=None,
                      title="FAO-56 root-zone depletion (last %d days)" % len(d), showlegend=False)
    return fig


def render_overview_map_page(
    config,
    latest: "pd.Series",
    has_soil_adjusted_irrigation: bool,
    combined_feature_df: "pd.DataFrame | None" = None,
    fao56_df: "pd.DataFrame | None" = None,
    advisory_df: "pd.DataFrame | None" = None,
    sentinel1_df: "pd.DataFrame | None" = None,
    vegetation_df: "pd.DataFrame | None" = None,
) -> None:
    """Render the Overview & Map dashboard landing page."""
    from app.sections.data_sources_health import evaluate_all

    page_header("MangoTwin Intelligence", "Sensor-Free Mango Orchard Digital Twin",
                "Muthukur / Peddapanjani, Andhra Pradesh")
    show_freshness_indicator(label="Overview", staleness_warning_days=0)
    st.caption(f"{config.study_area.name}, {config.study_area.district} district, {config.study_area.state}")

    try:
        records = evaluate_all(config)
    except Exception:
        records = []

    # ---- KPI cards ------------------------------------------------------
    irr_level = (latest["soil_adjusted_irrigation_risk_level"] if has_soil_adjusted_irrigation
                 else latest["irrigation_risk_level"])
    irr_note = "Weather-based, soil-adjusted" if has_soil_adjusted_irrigation else "Weather-based"

    ws_level, ws_note = "N/A", "FAO-56 water balance unavailable"
    if fao56_df is not None and not fao56_df.empty and "water_stress_level" in fao56_df.columns:
        row = fao56_df.sort_values("date").iloc[-1]
        ws_level = str(row["water_stress_level"])
        ks = row.get("ks")
        ws_note = "FAO-56 Ks " + (f"{float(ks):.2f}" if pd.notna(ks) else "n/a") + f" \u00b7 {row['date']:%Y-%m-%d}"

    sat_state, sat_note = satellite_freshness_summary(records)

    cards = [
        ("Latest valid data date", latest["date"].strftime("%Y-%m-%d"), "Historical weather", None),
        ("Irrigation risk", str(irr_level), irr_note, _level_state(irr_level)),
        ("Water stress", ws_level, ws_note, _level_state(ws_level)),
        ("Disease risk", str(latest["disease_risk_level"]), "Weather-based", _level_state(latest["disease_risk_level"])),
        ("Satellite freshness", sat_state, sat_note, sat_state if sat_state in ("Fresh", "Aging", "Stale") else None),
    ]
    for col, (label, value, note, state) in zip(st.columns(5), cards):
        col.markdown(kpi_card(label, value, note, state), unsafe_allow_html=True)
    st.caption(
        "Irrigation risk is a weather-rule score; water stress is the separate FAO-56 soil-water "
        "assessment (Ks from root-zone depletion). They can differ and are not interchangeable."
    )

    st.write("")

    # ---- Map + remote sensing summary ----------------------------------
    # The map is intentionally zoomed to the study area (zoom 8); disputed northern borders are
    # off-screen and the carto basemap is not an authoritative boundary source.
    map_col, rs_col = st.columns([3, 2])
    with map_col:
        section_header("Study Area Map")
        try:
            _theme_base = st.get_option("theme.base")
        except Exception:
            _theme_base = None
        map_fig = build_study_area_map(config.latitude, config.longitude, _theme_base)
        st.plotly_chart(map_fig, use_container_width=True, config={"scrollZoom": True})
        st.caption(
            f"\U0001f4cd {config.study_area.name}, {config.study_area.district} district, "
            f"{config.study_area.state}, {config.study_area.country} "
            f"\u2014 {config.latitude}\u00b0 N, {config.longitude}\u00b0 E"
        )
    with rs_col:
        section_header("Remote Sensing Freshness Summary")
        for r in records:
            if r["key"] in ("sentinel2", "sentinel1"):
                latest_obs = r["latest_observation"].isoformat() if r["latest_observation"] else "n/a"
                st.markdown(
                    f'<div class="mt-card"><div style="display:flex;justify-content:space-between">'
                    f'<h4>{esc(r["name"])}</h4>{status_pill(r["state"])}</div>'
                    f'<div class="mt-meta">Latest observation: {esc(latest_obs)}<br>{esc(r["detail"])}</div></div>',
                    unsafe_allow_html=True,
                )
        st.caption("Sentinel-2 is optical and can be stale in cloudy periods; Sentinel-1 SAR is a "
                   "radar proxy, not NDVI or calibrated soil moisture.")

    st.caption(
        "Map is focused on the study orchard location in Andhra Pradesh. Basemap boundary lines "
        "are provided by the tile provider and are not used as the authoritative boundary source."
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

    # ---- Water balance trend + latest advisory --------------------------
    trend_col, adv_col = st.columns([3, 2])
    with trend_col:
        section_header("Water Balance Trend")
        fig = water_balance_trend_figure(fao56_df)
        if fig is None:
            st.info("FAO-56 water-balance data not available. Run `python main.py` to generate it.")
        else:
            st.plotly_chart(fig, use_container_width=True)
    with adv_col:
        section_header("Latest Irrigation Advisory")
        if advisory_df is None or advisory_df.empty:
            st.info("Irrigation advisory not available. Run `python main.py --skip-fetch` to generate it.")
        else:
            adv = advisory_df.iloc[0]
            pr = str(adv.get("advisory_priority", "Unknown"))
            pill = status_pill(pr if pr in ("Low", "Medium", "High") else "Unknown", "Priority: " + pr)
            st.markdown(
                f'<div class="mt-card"><div style="display:flex;justify-content:space-between;gap:.5rem">'
                f'<h4>{esc(adv.get("advisory_action", "n/a"))}</h4>{pill}</div>'
                f'<div class="mt-meta">{esc(adv.get("advisory_reason", ""))}<br>'
                f'FAO-56 status date: {esc(adv.get("current_date", "n/a"))}</div></div>',
                unsafe_allow_html=True,
            )
            st.caption("FAO-56 + forecast advisory. Open the Irrigation Advisory page for full limitations.")

    st.divider()

    # ---- Recent data refresh summary -----------------------------------
    section_header("Recent Data Refresh Summary",
                   "Source-specific freshness; see Data Sources & Health for detail.")
    if records:
        summary = pd.DataFrame([{
            "Source": r["name"], "State": r["state"],
            "Latest observation": r["latest_observation"].isoformat() if r["latest_observation"] else "n/a",
            "Age (days)": r["age_days"],
        } for r in records])
        st.dataframe(summary, use_container_width=True, hide_index=True)
    else:
        st.info("Source status unavailable.")

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

    st.metric(label="Heat stress risk", value=_risk_color(latest["heat_stress_risk_level"]))

    st.divider()

    _render_remote_sensing_freshness(combined_feature_df)

    st.divider()

    _render_weather_recommendations(latest, has_soil_adjusted_irrigation)


def _render_remote_sensing_freshness(combined_feature_df: "pd.DataFrame | None") -> None:
    """Detailed Sentinel-2 / Sentinel-1 freshness from the combined feature table (unchanged logic)."""
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


def _render_weather_recommendations(latest: "pd.Series", has_soil_adjusted_irrigation: bool) -> None:
    """Weather-rule recommendations (distinct from the FAO-56 advisory above; unchanged logic)."""
    st.subheader("Weather-Based Recommendation")

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
