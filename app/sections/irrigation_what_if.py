"""
app/sections/irrigation_what_if.py

Irrigation What-If Planner — a read-only, dashboard-only scenario simulator.

PURPOSE
-------
Lets the user test possible irrigation amounts and see how the FAO-56 root-zone
depletion balance would respond, without writing any data to disk.

The calculation is intentionally conservative: only the immediate depletion
reduction is estimated (Dr,new = max(0, Dr,current - irrigation_mm)). This
matches FAO-56 eq 85 logic — irrigation is a water input that directly
reduces the current depletion — but does NOT propagate the benefit forward
through future ETc and rainfall (that would require a full re-run of the
pipeline). Users who want a full forward projection should add the event to
data/manual/muthukur_irrigation_events.csv and re-run python main.py.

PURE HELPER FUNCTIONS (importable and testable without Streamlit)
-----------------------------------------------------------------
  apply_scenario_irrigation(current_depletion_mm, irrigation_mm)  → float
  classify_stress_from_depletion(depletion_mm, taw_mm, raw_mm)     → str
  scenario_stress_rank(level)                                       → int
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from app.sections.freshness import show_freshness_indicator


# ---------------------------------------------------------------------------
# Pure helper functions
# ---------------------------------------------------------------------------

def apply_scenario_irrigation(
    current_depletion_mm: float,
    irrigation_mm: float,
) -> float:
    """
    Estimate root-zone depletion immediately after applying irrigation.

    Irrigation is an additive water input that reduces depletion (FAO-56 eq 85).
    Depletion is clamped at 0 — it cannot go below field capacity.

    Parameters
    ----------
    current_depletion_mm : float
        Current root-zone depletion before irrigation.
    irrigation_mm : float
        Irrigation water applied in the scenario (mm).

    Returns
    -------
    float
        Estimated depletion after irrigation, clamped to [0, ∞).
    """
    return max(0.0, float(current_depletion_mm) - float(irrigation_mm))


def _compute_ks(depletion_mm: float, taw_mm: float, raw_mm: float) -> float:
    """FAO-56 eq 84: compute the water-stress coefficient Ks from depletion."""
    if depletion_mm <= raw_mm:
        return 1.0
    denom = taw_mm - raw_mm
    if denom <= 1e-9:
        return 1.0
    ks = (taw_mm - depletion_mm) / denom
    return max(0.0, min(1.0, ks))


def classify_stress_from_depletion(
    depletion_mm: float,
    taw_mm: float,
    raw_mm: float,
) -> str:
    """
    Classify water stress level from root-zone depletion, TAW, and RAW.

    Uses the same Ks thresholds as the FAO-56 pipeline scripts:
      Ks ≥ 0.90  →  "Low"
      Ks ≥ 0.60  →  "Medium"
      Ks < 0.60  →  "High"

    Parameters
    ----------
    depletion_mm : float
        Root-zone depletion (mm).
    taw_mm : float
        Total available water (mm).
    raw_mm : float
        Readily available water / stress onset threshold (mm).

    Returns
    -------
    str : "Low", "Medium", or "High"
    """
    ks = _compute_ks(depletion_mm, taw_mm, raw_mm)
    if ks >= 0.90:
        return "Low"
    if ks >= 0.60:
        return "Medium"
    return "High"


def scenario_stress_rank(level: str) -> int:
    """
    Integer rank for stress level comparison: lower = less stress.
    Unknown levels default to Medium (1).
    """
    return {"Low": 0, "Medium": 1, "High": 2}.get(level, 1)


def _stress_label(level: str) -> str:
    """Return emoji + text label for a stress level string."""
    if level == "High":
        return "🔴 High"
    if level == "Medium":
        return "🟠 Medium"
    return "🟢 Low"


# ---------------------------------------------------------------------------
# Dashboard page
# ---------------------------------------------------------------------------

_REQUIRED_COLS = {"root_zone_depletion_mm", "water_stress_level", "taw_mm", "raw_mm"}


def render_irrigation_what_if_page(
    fao56_df: pd.DataFrame | None,
) -> None:
    """Render the Irrigation What-If Planner dashboard page."""

    st.title("Irrigation What-If Planner")
    show_freshness_indicator(fao56_df, label="FAO-56 water balance", staleness_warning_days=0)

    st.info(
        "📐 **Decision-support estimate only.** "
        "This planner simulates how an irrigation application would affect the FAO-56 "
        "root-zone depletion balance. It does **not** write any data to disk — "
        "no CSV, no pipeline state, no committed file is changed. "
        "To make an event official, add it to "
        "`data/manual/muthukur_irrigation_events.csv` and re-run "
        "`python main.py --skip-fetch`."
    )

    if fao56_df is None or fao56_df.empty:
        st.warning(
            "FAO-56 water balance data not available. "
            "Run `python main.py --skip-fetch` to generate it."
        )
        return

    missing_cols = _REQUIRED_COLS - set(fao56_df.columns)
    if missing_cols:
        st.error(
            f"FAO-56 output is missing required columns: {sorted(missing_cols)}. "
            "Re-run `python main.py --skip-fetch` to regenerate the water balance CSV."
        )
        return

    latest = fao56_df.iloc[-1]
    latest_date = pd.to_datetime(latest["date"]).date()
    taw_mm = float(latest["taw_mm"])
    raw_mm = float(latest["raw_mm"])
    baseline_depletion = float(latest["root_zone_depletion_mm"])
    baseline_stress = str(latest["water_stress_level"])

    # Optional context columns
    mango_stage = str(latest.get("mango_stage", "")) if "mango_stage" in fao56_df.columns else None
    ks_current = float(latest["ks"]) if "ks" in fao56_df.columns else None

    # ── Inputs ────────────────────────────────────────────────────────────
    st.subheader("Scenario Inputs")

    input_col1, input_col2, input_col3 = st.columns(3)

    with input_col1:
        scenario_date = st.date_input(
            "Scenario date",
            value=latest_date,
            min_value=latest_date,
            max_value=latest_date + dt.timedelta(days=30),
            help=(
                "Date you plan to irrigate. "
                "Defaults to the latest FAO-56 date. "
                "Future dates within 30 days are allowed for planning purposes."
            ),
        )

    with input_col2:
        irrigation_mm = st.number_input(
            "Irrigation amount (mm)",
            min_value=0,
            max_value=100,
            value=20,
            step=5,
            help=(
                "Amount of water to apply in this scenario (mm). "
                "Typical drip/sprinkler sessions for mango orchards: 15–40 mm."
            ),
        )

    with input_col3:
        scenario_label = st.text_input(
            "Scenario label",
            value="Scenario irrigation",
            max_chars=40,
            help="Optional label for this scenario (shown on the chart).",
        )

    # Show current context
    ctx_parts = [f"Latest FAO-56 date: **{latest_date.strftime('%Y-%m-%d')}**"]
    if mango_stage:
        ctx_parts.append(f"Crop stage: **{mango_stage}**")
    if ks_current is not None:
        ctx_parts.append(f"Current Ks: **{ks_current:.3f}**")
    ctx_parts.append(f"TAW: **{taw_mm:.1f} mm**  ·  RAW: **{raw_mm:.1f} mm**")
    st.caption("  ·  ".join(ctx_parts))

    st.divider()

    # ── Scenario calculation ──────────────────────────────────────────────
    scenario_depletion = apply_scenario_irrigation(baseline_depletion, irrigation_mm)
    depletion_reduction = baseline_depletion - scenario_depletion
    scenario_stress = classify_stress_from_depletion(scenario_depletion, taw_mm, raw_mm)

    # ── Result cards ─────────────────────────────────────────────────────
    st.subheader("Scenario Results")
    st.caption(
        "Left column: current baseline. "
        "Middle: scenario inputs. "
        "Right: estimated outcome after irrigation."
    )

    card_col1, card_col2, card_col3 = st.columns(3)

    with card_col1:
        st.markdown("**Current baseline**")
        st.metric(
            label="Root-zone depletion",
            value=f"{baseline_depletion:.1f} mm",
            help=f"As of {latest_date.strftime('%Y-%m-%d')}.",
        )
        st.metric(
            label="Water stress level",
            value=_stress_label(baseline_stress),
        )

    with card_col2:
        st.markdown("**Scenario input**")
        st.metric(
            label=scenario_label if scenario_label else "Irrigation applied",
            value=f"{irrigation_mm:.0f} mm",
        )
        st.metric(
            label="Depletion reduction",
            value=f"−{depletion_reduction:.1f} mm",
            delta=f"−{depletion_reduction:.1f} mm",
            delta_color="inverse",
        )

    with card_col3:
        st.markdown("**Estimated outcome**")
        st.metric(
            label="Depletion after irrigation",
            value=f"{scenario_depletion:.1f} mm",
            delta=f"−{depletion_reduction:.1f} mm" if depletion_reduction > 0 else "0 mm",
            delta_color="inverse",
        )
        st.metric(
            label="Stress level after irrigation",
            value=_stress_label(scenario_stress),
        )

    # Stress change commentary
    baseline_rank = scenario_stress_rank(baseline_stress)
    scenario_rank = scenario_stress_rank(scenario_stress)

    if irrigation_mm == 0:
        st.info("ℹ️ Zero irrigation applied — depletion and stress level are unchanged.")
    elif scenario_rank < baseline_rank:
        st.success(
            f"✅ Applying {irrigation_mm} mm would move water stress from "
            f"**{baseline_stress}** → **{scenario_stress}**."
        )
    elif baseline_rank == scenario_rank:
        st.info(
            f"ℹ️ Applying {irrigation_mm} mm reduces depletion by "
            f"{depletion_reduction:.1f} mm but the stress classification remains "
            f"**{baseline_stress}**. A larger application may be needed to shift stress level."
        )
    else:
        # Should not happen but handle defensively
        st.warning("⚠️ Scenario stress classification is higher than baseline — check inputs.")

    pct_of_taw = (scenario_depletion / taw_mm * 100) if taw_mm > 0 else 0.0
    st.caption(
        f"Scenario depletion {scenario_depletion:.1f} mm = {pct_of_taw:.0f}% of TAW "
        f"({taw_mm:.1f} mm).  "
        f"{'Below RAW — no water stress.' if scenario_depletion <= raw_mm else 'Above RAW — some water stress remains.'}"
    )

    st.divider()

    # ── Comparison chart ─────────────────────────────────────────────────
    st.subheader("Depletion Chart")

    # Use last 30 rows of actual depletion as context
    chart_df = fao56_df.tail(30).copy()
    chart_df["date"] = pd.to_datetime(chart_df["date"])

    fig = go.Figure()

    # Actual depletion history
    fig.add_trace(
        go.Scatter(
            x=chart_df["date"],
            y=chart_df["root_zone_depletion_mm"],
            mode="lines+markers",
            name="Actual depletion",
            line=dict(color="#636EFA", width=2),
            marker=dict(size=5),
        )
    )

    # Baseline point (latest actual)
    fig.add_trace(
        go.Scatter(
            x=[pd.Timestamp(latest_date)],
            y=[baseline_depletion],
            mode="markers",
            name=f"Current ({baseline_depletion:.1f} mm)",
            marker=dict(size=12, color="#636EFA", symbol="diamond"),
            showlegend=True,
        )
    )

    # Scenario point
    fig.add_trace(
        go.Scatter(
            x=[pd.Timestamp(scenario_date)],
            y=[scenario_depletion],
            mode="markers",
            name=f"{scenario_label} ({scenario_depletion:.1f} mm)",
            marker=dict(size=16, color="green", symbol="star"),
        )
    )

    # If scenario date is in the future, draw a connector line from baseline
    if scenario_date > latest_date:
        fig.add_trace(
            go.Scatter(
                x=[pd.Timestamp(latest_date), pd.Timestamp(scenario_date)],
                y=[baseline_depletion, scenario_depletion],
                mode="lines",
                name="Scenario path",
                line=dict(color="green", dash="dot", width=1.5),
                showlegend=False,
            )
        )

    # RAW threshold
    fig.add_hline(
        y=raw_mm, line_dash="dash", line_color="orange",
        annotation_text="RAW (stress begins)",
        annotation_position="bottom right",
    )

    # TAW threshold
    fig.add_hline(
        y=taw_mm, line_dash="dash", line_color="red",
        annotation_text="TAW (all water gone)",
        annotation_position="top right",
    )

    fig.update_layout(
        title="Root-Zone Depletion: Actual History vs Irrigation Scenario",
        xaxis_title="Date",
        yaxis_title="Root-zone depletion (mm)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420,
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Explanation ───────────────────────────────────────────────────────
    st.subheader("How This Estimate Works")

    st.write(
        "Adding irrigation reduces root-zone depletion in the FAO-56 balance. "
        "The estimated depletion after irrigation is:"
    )
    st.code(
        f"new_depletion = max(0, current_depletion − irrigation_mm)\n"
        f"             = max(0, {baseline_depletion:.1f} − {irrigation_mm:.0f})\n"
        f"             = {scenario_depletion:.1f} mm",
        language="text",
    )
    st.write(
        "This is a conservative, single-step estimate — it does not simulate ETc and rainfall "
        "propagating forward after the irrigation event. The actual benefit depends on crop "
        "stage, upcoming rainfall, and ongoing evapotranspiration."
    )

    st.warning(
        "⚠️ **This what-if estimate does not write an irrigation event to the project CSV.** "
        "Adding irrigation reduces root-zone depletion in the FAO-56 balance. "
        "To make this event official and include it in the FAO-56 balance and advisory, "
        "add it to `data/manual/muthukur_irrigation_events.csv` and re-run "
        "`python main.py --skip-fetch`."
    )
