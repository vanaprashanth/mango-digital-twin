from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def render_fao56_sensitivity_analysis_page(
    fao56_sensitivity_df: pd.DataFrame | None,
    fao56_sensitivity_summary_text: str | None,
) -> None:
    """Render the FAO-56 Sensitivity Analysis dashboard page."""

    st.title("FAO-56 Sensitivity Analysis")

    st.caption(
        "This analysis tests how FAO-56 soil-water-balance results change under different "
        "modelling assumptions. Three parameters are varied independently across a full factorial "
        "grid of scenarios: root depth (m), depletion fraction p, and a Kc multiplier. "
        "This is assumption/sensitivity analysis — it is not field validation and should not be "
        "treated as ground truth. No soil-moisture sensor or yield data are used."
    )

    if fao56_sensitivity_df is None or fao56_sensitivity_df.empty:
        st.warning("FAO-56 sensitivity analysis data could not be loaded or is empty.")
        st.info("Run `python main.py` to generate the FAO-56 sensitivity analysis output.")
        return

    df = fao56_sensitivity_df.copy()

    # ------------------------------------------------------------------ #
    # Key metrics
    # ------------------------------------------------------------------ #
    st.subheader("Key Metrics")

    baseline_rows = df[df["is_baseline"].astype(bool)]
    baseline = baseline_rows.iloc[0] if not baseline_rows.empty else None

    total_scenarios = len(df)
    hs_min = int(df["n_days_high_stress"].min())
    hs_max = int(df["n_days_high_stress"].max())
    etc_min = df["mean_etc_mm_day"].min()
    etc_max = df["mean_etc_mm_day"].max()
    dep_min = df["mean_depletion_mm"].min()
    dep_max = df["mean_depletion_mm"].max()

    worst_row = df.loc[df["n_days_high_stress"].idxmax()]
    best_row  = df.loc[df["n_days_high_stress"].idxmin()]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total scenarios", total_scenarios)
    with col2:
        st.metric("High-stress days range", f"{hs_min} – {hs_max} days")
    with col3:
        st.metric("Mean ETc range", f"{etc_min:.2f} – {etc_max:.2f} mm/day")

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("Mean depletion range", f"{dep_min:.1f} – {dep_max:.1f} mm")
    with col5:
        if baseline is not None:
            st.metric(
                "Baseline scenario",
                f"root={baseline['root_depth_m']:.1f}m, "
                f"p={baseline['depletion_fraction_p']:.2f}, "
                f"kc×{baseline['kc_multiplier']:.2f}",
            )
        else:
            st.metric("Baseline scenario", "n/a")
    with col6:
        if baseline is not None:
            st.metric("Baseline high-stress days", int(baseline["n_days_high_stress"]))

    col7, col8 = st.columns(2)
    with col7:
        st.metric(
            "Most conservative (most stress)",
            f"root={worst_row['root_depth_m']:.1f}m, "
            f"p={worst_row['depletion_fraction_p']:.2f}, "
            f"kc×{worst_row['kc_multiplier']:.2f}",
            help=f"{int(worst_row['n_days_high_stress'])} high-stress days "
                 f"({worst_row['pct_days_high_stress']:.1f}%)",
        )
    with col8:
        st.metric(
            "Least conservative (least stress)",
            f"root={best_row['root_depth_m']:.1f}m, "
            f"p={best_row['depletion_fraction_p']:.2f}, "
            f"kc×{best_row['kc_multiplier']:.2f}",
            help=f"{int(best_row['n_days_high_stress'])} high-stress days "
                 f"({best_row['pct_days_high_stress']:.1f}%)",
        )

    st.divider()

    # ------------------------------------------------------------------ #
    # Charts
    # ------------------------------------------------------------------ #
    st.subheader("Sensitivity Charts")

    # Label each scenario for hover
    df["scenario_label"] = (
        "root=" + df["root_depth_m"].astype(str) + "m, "
        "p=" + df["depletion_fraction_p"].astype(str) + ", "
        "kc×" + df["kc_multiplier"].astype(str)
    )
    df["kc_multiplier_str"] = df["kc_multiplier"].astype(str)
    df["root_depth_str"] = df["root_depth_m"].astype(str) + " m"
    df["dep_p_str"] = "p=" + df["depletion_fraction_p"].astype(str)

    # 1. High-stress days by scenario (all 36), colour = kc_multiplier
    hs_fig = px.scatter(
        df.sort_values("n_days_high_stress"),
        x="scenario_id",
        y="n_days_high_stress",
        color="kc_multiplier_str",
        hover_name="scenario_label",
        hover_data={"n_days_high_stress": True, "pct_days_high_stress": True,
                    "scenario_id": False, "kc_multiplier_str": False},
        title="High-Stress Days by Scenario (all 36)",
        labels={
            "scenario_id": "Scenario ID",
            "n_days_high_stress": "High-stress days",
            "kc_multiplier_str": "Kc multiplier",
        },
    )
    st.plotly_chart(hs_fig, use_container_width=True)

    # 2. Mean ETc by Kc multiplier (box)
    etc_fig = px.box(
        df, x="kc_multiplier_str", y="mean_etc_mm_day",
        title="Mean ETc by Kc Multiplier",
        labels={"kc_multiplier_str": "Kc multiplier", "mean_etc_mm_day": "Mean ETc (mm/day)"},
        category_orders={"kc_multiplier_str": sorted(df["kc_multiplier_str"].unique())},
    )
    st.plotly_chart(etc_fig, use_container_width=True)

    # 3. Mean depletion by root depth (box)
    dep_fig = px.box(
        df, x="root_depth_str", y="mean_depletion_mm",
        title="Mean Depletion by Root Depth",
        labels={"root_depth_str": "Root depth", "mean_depletion_mm": "Mean depletion (mm)"},
        category_orders={"root_depth_str": sorted(df["root_depth_str"].unique())},
    )
    st.plotly_chart(dep_fig, use_container_width=True)

    # 4. High-stress percent by depletion fraction p (box)
    p_fig = px.box(
        df, x="dep_p_str", y="pct_days_high_stress",
        title="High-Stress Days (%) by Depletion Fraction p",
        labels={"dep_p_str": "Depletion fraction p", "pct_days_high_stress": "High-stress days (%)"},
        category_orders={"dep_p_str": sorted(df["dep_p_str"].unique())},
    )
    st.plotly_chart(p_fig, use_container_width=True)

    st.divider()

    # ------------------------------------------------------------------ #
    # Limitations
    # ------------------------------------------------------------------ #
    st.subheader("Limitations")

    st.info(
        "- This is **assumption/sensitivity analysis**, not field validation.\n"
        "- Kc values and root depths are assumed, not locally calibrated for this orchard.\n"
        "- No soil-moisture sensor validation.\n"
        "- No yield or irrigation-event records.\n"
        "- Results should not be treated as ground truth — they show the range of possible "
        "outcomes under different modelling choices."
    )

    st.divider()

    # ------------------------------------------------------------------ #
    # Raw data / markdown summary
    # ------------------------------------------------------------------ #
    st.subheader("Raw Data & Summary")

    with st.expander("Full sensitivity analysis table (all scenarios)", expanded=False):
        display_df = df.drop(columns=["scenario_label", "kc_multiplier_str",
                                       "root_depth_str", "dep_p_str"], errors="ignore").copy()
        numeric_cols = display_df.select_dtypes(include="number").columns
        display_df[numeric_cols] = display_df[numeric_cols].round(3)
        st.dataframe(display_df, use_container_width=True)

    if fao56_sensitivity_summary_text is not None:
        with st.expander("Markdown summary (full text)", expanded=False):
            st.markdown(fao56_sensitivity_summary_text)
    else:
        st.caption("Markdown summary file not available.")
