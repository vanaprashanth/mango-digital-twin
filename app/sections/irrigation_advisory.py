"""
app/sections/irrigation_advisory.py
------------------------------------
Renders the Irrigation Advisory dashboard page.

Called from app/streamlit_app.py:
    from app.sections.irrigation_advisory import render_irrigation_advisory_page
    render_irrigation_advisory_page(irrigation_advisory_df)
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_irrigation_advisory_page(irrigation_advisory_df: pd.DataFrame | None) -> None:
    """Render the Irrigation Advisory sidebar page."""

    st.title("Irrigation Advisory")

    st.caption(
        "Farmer-facing irrigation recommendation based on the phenology-aware "
        "FAO-56 water stress status combined with the Open-Meteo short-term "
        "rainfall forecast. Updated every pipeline run."
    )

    if irrigation_advisory_df is None or irrigation_advisory_df.empty:
        st.warning("Irrigation advisory data could not be loaded or is empty.")
        st.info("Run `python main.py --skip-fetch` to generate the forecast-aware irrigation advisory.")
        return

    adv = irrigation_advisory_df.iloc[0]

    priority = str(adv.get("advisory_priority", "Low"))
    action = str(adv.get("advisory_action", "—"))
    reason = str(adv.get("advisory_reason", "—"))
    limitations_raw = str(adv.get("advisory_limitations", ""))
    water_stress_level = str(adv.get("water_stress_level", "—"))
    mango_stage = str(adv.get("mango_stage", "—"))
    current_date = str(adv.get("current_date", "—"))
    generated_at = str(adv.get("advisory_generated_at", "—"))
    forecast_resolution = str(adv.get("forecast_resolution", "daily"))
    rain_24h = adv.get("rain_next_24h_mm", None)
    rain_6h = adv.get("rain_next_6h_mm", None)
    rain_12h = adv.get("rain_next_12h_mm", None)
    rain_prob = adv.get("rain_probability_next_24h", None)
    kc = adv.get("kc", None)
    et0 = adv.get("et0_mm_day", None)
    etc = adv.get("etc_mm_day", None)
    depletion = adv.get("root_zone_depletion_mm", None)
    ks = adv.get("ks", None)

    def _fmt_mm(v) -> str:
        try:
            return f"{float(v):.1f} mm"
        except (TypeError, ValueError):
            return "—"

    def _fmt_f(v, decimals=3) -> str:
        try:
            return f"{float(v):.{decimals}f}"
        except (TypeError, ValueError):
            return "—"

    # ── Top metrics ─────────────────────────────────────────────────
    st.subheader("Current Status")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("FAO-56 status date", current_date)
    with m2:
        st.metric("Mango stage", mango_stage)
    with m3:
        st.metric("Water stress", water_stress_level)
    with m4:
        st.metric("Rain next 24h", _fmt_mm(rain_24h) if rain_24h is not None else "—")

    m5, m6, m7, m8 = st.columns(4)
    with m5:
        st.metric("Advisory priority", priority)
    with m6:
        st.metric("Forecast resolution", forecast_resolution)
    with m7:
        st.metric("Advisory generated at", generated_at[:19] if len(generated_at) > 19 else generated_at)
    with m8:
        st.metric("Advisory action", "See below ↓")

    st.divider()

    # ── Advisory action callout ──────────────────────────────────────
    st.subheader("Recommendation")

    if priority == "High":
        st.error(f"⚠️ **{action}**")
    elif priority == "Medium":
        st.warning(f"🟡 **{action}**")
    else:
        st.success(f"✅ **{action}**")

    st.divider()

    # ── Explanation ─────────────────────────────────────────────────
    st.subheader("Why this recommendation?")

    st.write(reason)

    exp_col1, exp_col2, exp_col3 = st.columns(3)
    with exp_col1:
        st.markdown("**FAO-56 water balance**")
        st.write(f"Water stress level: **{water_stress_level}**")
        st.write(f"Ks (stress coefficient): **{_fmt_f(ks)}**")
        st.write(f"Root-zone depletion: **{_fmt_mm(depletion)}**")
    with exp_col2:
        st.markdown("**Forecast rainfall**")
        st.write(f"Rain next 24h: **{_fmt_mm(rain_24h) if rain_24h is not None else '—'}**")
        st.write(f"Rain next 12h: **{_fmt_mm(rain_12h) if rain_12h is not None else 'Not available (hourly data required)'}**")
        st.write(f"Rain next 6h: **{_fmt_mm(rain_6h) if rain_6h is not None else 'Not available (hourly data required)'}**")
        st.write(f"Rain probability 24h: **{_fmt_f(rain_prob, 0) + '%' if rain_prob is not None else 'Not available'}**")
    with exp_col3:
        st.markdown("**Crop stage context**")
        st.write(f"Current stage: **{mango_stage}**")
        st.caption(
            "Fruit set and Fruit development are the most sensitive stages for "
            "water deficit. During these stages the model may recommend partial "
            "irrigation even when rain is expected but uncertain."
        )

    st.divider()

    # ── Decision rule summary ────────────────────────────────────────
    st.subheader("Decision Rules (Summary)")

    rules = [
        ("High", "Rain ≥ 5 mm expected in 24h", "Delay irrigation and recheck after rainfall"),
        ("High", "Rain < 2 mm expected in 24h", "Irrigate now or apply partial irrigation"),
        ("High", "Rain 2–5 mm (uncertain) — critical stage (Fruit set / Fruit development)", "Apply partial irrigation and recheck after forecast update"),
        ("High", "Rain 2–5 mm (uncertain) — other stage", "Delay irrigation and recheck after rainfall"),
        ("Medium", "Rain ≥ 2 mm expected in 24h", "Wait and monitor"),
        ("Medium", "Rain < 2 mm expected in 24h", "Monitor closely; consider irrigation soon"),
        ("Low", "Any forecast", "No irrigation needed now"),
        ("—", "Forecast unavailable", "Use FAO-56 advisory only; forecast unavailable"),
    ]

    rules_df = pd.DataFrame(rules, columns=["Water stress", "Forecast condition", "Advisory action"])
    st.dataframe(rules_df, use_container_width=True, hide_index=True)

    st.caption(
        "Note: 6-hour and 12-hour rainfall amounts are only computable from hourly forecast data. "
        "This project currently uses daily Open-Meteo forecast output; all thresholds above are "
        "applied to the next-24-hour rainfall total."
    )

    st.divider()

    # ── Technical details ────────────────────────────────────────────
    st.subheader("Technical Details")

    td_col1, td_col2 = st.columns(2)
    with td_col1:
        st.markdown("**FAO-56 parameters**")
        st.write(f"Kc (crop coefficient): **{_fmt_f(kc)}**")
        st.write(f"ET₀ (reference evapotranspiration): **{_fmt_mm(et0)}/day**")
        st.write(f"ETc (crop evapotranspiration): **{_fmt_mm(etc)}/day**")
        st.write(f"Root-zone depletion: **{_fmt_mm(depletion)}**")
        st.write(f"Ks (water stress coefficient): **{_fmt_f(ks)}**")
    with td_col2:
        st.markdown("**Forecast inputs**")
        st.write(f"Forecast resolution: **{forecast_resolution}**")
        st.write(f"Rain next 6h: **{_fmt_mm(rain_6h) if rain_6h is not None else 'N/A — hourly data required'}**")
        st.write(f"Rain next 12h: **{_fmt_mm(rain_12h) if rain_12h is not None else 'N/A — hourly data required'}**")
        st.write(f"Rain next 24h: **{_fmt_mm(rain_24h) if rain_24h is not None else '—'}**")
        st.write(f"Rain probability 24h: **{_fmt_f(rain_prob, 0) + '%' if rain_prob is not None else 'N/A — not in Open-Meteo daily output'}**")

    st.divider()

    # ── Limitations ─────────────────────────────────────────────────
    st.subheader("Limitations")

    st.info(
        "- **Daily forecast only.** This advisory uses daily Open-Meteo forecast data. "
        "6-hour and 12-hour rain amounts are not available.\n"
        "- **Not a replacement for farmer judgment.** Actual field conditions, soil "
        "observations, and local knowledge should always take precedence.\n"
        "- **No soil-moisture sensor validation yet.** Root-zone depletion is a "
        "model estimate, not a measured value.\n"
        "- **No irrigation-event records yet.** The FAO-56 water balance treats all "
        "water input as rainfall; actual irrigation history is not tracked.\n"
        "- **Rain forecasts can change.** Re-run the pipeline to refresh the advisory "
        "before making irrigation decisions.\n"
        "- **Kc values are assumed**, not locally calibrated for this orchard or cultivar."
    )

    # Parsed limitations from the CSV if available
    if limitations_raw and " | " in limitations_raw:
        with st.expander("Detailed limitations (from advisory output)", expanded=False):
            for part in limitations_raw.split(" | "):
                st.write(f"- {part}")

    st.divider()

    # ── Raw data ────────────────────────────────────────────────────
    st.subheader("Raw Data")

    with st.expander("Full advisory record", expanded=False):
        adv_display = irrigation_advisory_df.copy()
        st.dataframe(adv_display, use_container_width=True)
