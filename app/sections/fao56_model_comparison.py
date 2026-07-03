from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from app.sections.freshness import show_freshness_indicator


def render_fao56_model_comparison_page(
    fao56_comparison_df: pd.DataFrame | None,
    fao56_model_comparison_summary_text: str | None,
) -> None:
    """Render the FAO-56 Model Comparison dashboard page."""

    st.title("FAO-56 Model Comparison: Constant-Kc vs Phenology-Aware")
    show_freshness_indicator(fao56_comparison_df, label="FAO-56 model comparison", staleness_warning_days=7)

    st.caption(
        "A standalone model-to-model comparison of the two FAO-56 soil-water balance "
        "prototypes built so far, quantifying how much replacing a constant crop "
        "coefficient with a growth-stage-specific one changes estimated crop water "
        "demand and water-stress interpretation."
    )

    if fao56_comparison_df is None or fao56_comparison_df.empty:
        st.warning("FAO-56 model comparison data could not be loaded or is empty.")
        st.info("Run `python main.py --skip-fetch` to generate the FAO-56 model comparison output.")
    else:
        if fao56_model_comparison_summary_text is None:
            st.warning(
                "The markdown summary file "
                "(`data/processed/muthukur_fao56_model_comparison_summary.md`) was not found. "
                "Showing the CSV-based comparison below without the narrative summary."
            )

        comp_df = fao56_comparison_df

        st.subheader("Comparison Summary")

        matched_days = len(comp_df)
        date_min = comp_df["date"].min()
        date_max = comp_df["date"].max()
        mean_etc_diff = comp_df["etc_difference"].mean()
        mean_abs_etc_diff = comp_df["etc_difference"].abs().mean()
        max_abs_idx = comp_df["etc_difference"].abs().idxmax()
        max_etc_diff_row = comp_df.loc[max_abs_idx]
        percent_stress_changed = comp_df["stress_level_changed"].astype(bool).mean() * 100

        comp_metric_col1, comp_metric_col2, comp_metric_col3 = st.columns(3)

        with comp_metric_col1:
            st.metric(label="Matched days", value=f"{matched_days}")

        with comp_metric_col2:
            st.metric(
                label="Date range",
                value=f"{date_min.strftime('%Y-%m-%d')} to {date_max.strftime('%Y-%m-%d')}",
            )

        with comp_metric_col3:
            st.metric(
                label="% days water-stress level changed",
                value=f"{percent_stress_changed:.1f}%",
            )

        comp_metric_col4, comp_metric_col5, comp_metric_col6 = st.columns(3)

        with comp_metric_col4:
            st.metric(label="Mean ETc difference", value=f"{mean_etc_diff:+.3f} mm/day")

        with comp_metric_col5:
            st.metric(label="Mean absolute ETc difference", value=f"{mean_abs_etc_diff:.3f} mm/day")

        with comp_metric_col6:
            st.metric(
                label="Maximum ETc difference",
                value=f"{max_etc_diff_row['etc_difference']:+.3f} mm/day",
                help=f"On {max_etc_diff_row['date'].strftime('%Y-%m-%d')} ({max_etc_diff_row['mango_stage']})",
            )

        st.caption(
            "ETc difference is computed as phenology-aware minus constant-Kc "
            "(both in mm/day)."
        )

        st.divider()

        st.subheader("Comparison Charts")

        etc_diff_fig = px.line(
            comp_df, x="date", y="etc_difference",
            title="ETc Difference Over Time (Phenology-Aware minus Constant-Kc)",
            labels={"date": "Date", "etc_difference": "ETc difference (mm/day)"},
        )
        etc_diff_fig.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(etc_diff_fig, use_container_width=True)

        etc_both_fig = px.line(
            comp_df, x="date", y=["constant_etc", "phenology_etc"],
            title="ETc: Constant-Kc vs Phenology-Aware",
            labels={"date": "Date", "value": "ETc (mm/day)", "variable": "Model"},
        )
        st.plotly_chart(etc_both_fig, use_container_width=True)

        kc_both_fig = px.line(
            comp_df, x="date", y=["constant_kc", "phenology_kc"],
            title="Kc: Constant-Kc vs Phenology-Aware",
            labels={"date": "Date", "value": "Kc", "variable": "Model"},
        )
        st.plotly_chart(kc_both_fig, use_container_width=True)

        ks_diff_fig = px.line(
            comp_df, x="date", y="ks_difference",
            title="Ks Difference Over Time (Phenology-Aware minus Constant-Kc)",
            labels={"date": "Date", "ks_difference": "Ks difference"},
        )
        ks_diff_fig.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(ks_diff_fig, use_container_width=True)

        stress_changed_counts_df = (
            comp_df["stress_level_changed"].astype(bool)
            .value_counts()
            .reindex([False, True], fill_value=0)
            .rename(index={False: "Unchanged", True: "Changed"})
            .rename_axis("status")
            .reset_index(name="days")
        )
        stress_changed_fig = px.bar(
            stress_changed_counts_df, x="status", y="days",
            title="Water-Stress Level Changed: Day Counts",
            labels={"status": "Water-stress level status", "days": "Number of days"},
        )
        st.plotly_chart(stress_changed_fig, use_container_width=True)

        comp_stage_order = [
            "Flower induction / pre-flowering",
            "Flowering",
            "Fruit set",
            "Fruit development",
            "Maturity / harvest",
            "Rest / vegetative phase",
        ]
        comp_stages_present = [s for s in comp_stage_order if s in comp_df["mango_stage"].unique()]

        stage_etc_diff_df = (
            comp_df.groupby("mango_stage")["etc_difference"]
            .mean()
            .reindex(comp_stages_present)
            .rename_axis("mango_stage")
            .reset_index(name="avg_etc_difference")
        )
        stage_etc_diff_fig = px.bar(
            stage_etc_diff_df, x="mango_stage", y="avg_etc_difference",
            title="Stage-Wise Average ETc Difference",
            labels={"mango_stage": "Mango stage", "avg_etc_difference": "Average ETc difference (mm/day)"},
            category_orders={"mango_stage": comp_stages_present},
        )
        stage_etc_diff_fig.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(stage_etc_diff_fig, use_container_width=True)

        stage_stress_change_df = (
            comp_df.assign(stress_level_changed=comp_df["stress_level_changed"].astype(bool))
            .groupby("mango_stage")["stress_level_changed"]
            .sum()
            .reindex(comp_stages_present, fill_value=0)
            .rename_axis("mango_stage")
            .reset_index(name="days_stress_changed")
        )
        stage_stress_change_fig = px.bar(
            stage_stress_change_df, x="mango_stage", y="days_stress_changed",
            title="Stage-Wise Water-Stress-Level Change Counts",
            labels={"mango_stage": "Mango stage", "days_stress_changed": "Number of days changed"},
            category_orders={"mango_stage": comp_stages_present},
        )
        st.plotly_chart(stage_stress_change_fig, use_container_width=True)

        top10_df = (
            comp_df.assign(abs_etc_difference=comp_df["etc_difference"].abs())
            .sort_values("abs_etc_difference", ascending=False)
            .head(10)
            .copy()
        )
        top10_df["date_label"] = top10_df["date"].dt.strftime("%Y-%m-%d") + " (" + top10_df["mango_stage"] + ")"
        top10_fig = px.bar(
            top10_df.sort_values("etc_difference"), x="etc_difference", y="date_label", orientation="h",
            title="Top 10 Biggest ETc Difference Dates",
            labels={"etc_difference": "ETc difference (mm/day)", "date_label": "Date (mango stage)"},
        )
        top10_fig.add_vline(x=0, line_dash="dash", line_color="gray")
        st.plotly_chart(top10_fig, use_container_width=True)

        st.divider()

        st.subheader("Interpretation")

        st.write("- **Positive ETc difference** means phenology-aware Kc estimated higher crop water demand than constant Kc.")
        st.write("- **Negative ETc difference** means phenology-aware Kc estimated lower crop water demand than constant Kc.")
        st.write("- **Fruit development should usually show higher ETc** because the assumed Kc is higher for that stage (0.90).")
        st.write("- **Rest / vegetative phase should usually show lower ETc** because the assumed Kc is lower for that stage (0.60).")
        st.write("- **Stress-level changes show where phenology-aware modeling changes management interpretation** — i.e. days where the Low/Medium/High water-stress label itself flips between the two models, not just the underlying numbers.")

        st.divider()

        st.subheader("Limitations")

        st.info(
            "- This is a **model-to-model comparison**, not ground-truth validation.\n"
            "- Kc values are assumed, not locally calibrated for this orchard or cultivar.\n"
            "- No soil-moisture sensor validation yet.\n"
            "- No irrigation-event records yet (both models are rainfed-only depletion balances).\n"
            "- No yield validation yet."
        )

        st.divider()

        st.subheader("Raw Data")

        with st.expander("FAO-56 model comparison table (full)", expanded=False):
            comp_preview = comp_df.copy()
            comp_preview["date"] = comp_preview["date"].dt.strftime("%Y-%m-%d")
            numeric_columns = comp_preview.select_dtypes(include="number").columns
            comp_preview[numeric_columns] = comp_preview[numeric_columns].round(3)
            st.dataframe(comp_preview, use_container_width=True)

        if fao56_model_comparison_summary_text is not None:
            with st.expander("Markdown summary (full text)", expanded=False):
                st.markdown(fao56_model_comparison_summary_text)
        else:
            st.caption("Markdown summary file not available.")
