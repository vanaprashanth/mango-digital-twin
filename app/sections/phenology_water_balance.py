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


def render_phenology_water_balance_page(
    fao56_phenology_water_balance_df: pd.DataFrame | None,
    fao56_water_balance_df: pd.DataFrame | None,
) -> None:
    """Render the Phenology Water Balance (phenology-aware FAO-56) dashboard page."""

    st.title("Phenology Water Balance (Phenology-Aware FAO-56)")

    st.warning(
        "This is a simplified phenology-aware prototype. Kc values are assumed, not "
        "cultivar-specific, not field-calibrated, and irrigation events are not yet included."
    )

    if fao56_phenology_water_balance_df is None or fao56_phenology_water_balance_df.empty:
        st.warning("Phenology-aware FAO-56 water balance file not found or could not be loaded.")
        st.info("Please run: python src/water_balance/fao56_phenology_water_balance.py")
        st.info(
            "(That script needs the combined feature table and the mango phenology calendar "
            "to already exist — see `python src/features/build_feature_table.py` and "
            "`python src/phenology/mango_phenology_calendar.py`.)"
        )
    else:
        st.caption(
            "Same daily ET0 / TAW / RAW / root-zone-depletion logic as the constant-Kc FAO-56 "
            "page, but the crop coefficient (Kc) now changes by mango growth stage instead of "
            "staying fixed at 0.75. This is a separate, standalone signal — it is not yet "
            "merged into the irrigation/heat/disease risk scores, the constant-Kc Water Balance "
            "page, or `main.py`."
        )

        phen_wb_latest = fao56_phenology_water_balance_df.iloc[-1]

        st.subheader("Latest Phenology-Aware Water Balance Status")

        pwb_col1, pwb_col2, pwb_col3, pwb_col4 = st.columns(4)

        with pwb_col1:
            st.metric(label="Latest date", value=phen_wb_latest["date"].strftime("%Y-%m-%d"))

        with pwb_col2:
            st.metric(label="Current mango stage", value=phen_wb_latest["mango_stage"])

        with pwb_col3:
            st.metric(label="Latest Kc", value=f"{phen_wb_latest['kc']:.2f}")

        with pwb_col4:
            st.metric(label="Latest ET0", value=f"{phen_wb_latest['et0_mm_day']:.2f} mm/day")

        pwb_col5, pwb_col6, pwb_col7, pwb_col8 = st.columns(4)

        with pwb_col5:
            st.metric(label="Latest ETc", value=f"{phen_wb_latest['etc_mm_day']:.2f} mm/day")

        with pwb_col6:
            st.metric(
                label="Latest root-zone depletion",
                value=f"{phen_wb_latest['root_zone_depletion_mm']:.1f} mm",
            )

        with pwb_col7:
            st.metric(label="Latest Ks", value=f"{phen_wb_latest['ks']:.2f}")

        with pwb_col8:
            st.metric(label="Latest water-stress level", value=_risk_color(phen_wb_latest["water_stress_level"]))

        st.divider()

        st.subheader("Phenology-Aware Water Balance Trends")

        kc_fig = px.line(
            fao56_phenology_water_balance_df, x="date", y="kc",
            title="Crop Coefficient (Kc) Over Time",
            labels={"date": "Date", "kc": "Kc"},
        )
        st.plotly_chart(kc_fig, use_container_width=True)

        phen_et_fig = px.line(
            fao56_phenology_water_balance_df, x="date", y=["et0_mm_day", "etc_mm_day"],
            title="ET0 and ETc Over Time (Phenology-Aware)",
            labels={"date": "Date", "value": "mm/day", "variable": "Metric"},
        )
        st.plotly_chart(phen_et_fig, use_container_width=True)

        phen_depletion_fig = px.line(
            fao56_phenology_water_balance_df, x="date", y="root_zone_depletion_mm",
            title="Root-Zone Depletion Over Time (Phenology-Aware)",
            labels={"date": "Date", "root_zone_depletion_mm": "Depletion (mm)"},
        )
        phen_depletion_fig.add_hline(
            y=phen_wb_latest["raw_mm"], line_dash="dash", line_color="orange",
            annotation_text="RAW (stress begins)",
        )
        phen_depletion_fig.add_hline(
            y=phen_wb_latest["taw_mm"], line_dash="dash", line_color="red",
            annotation_text="TAW (all available water gone)",
        )
        st.plotly_chart(phen_depletion_fig, use_container_width=True)

        phen_ks_fig = px.line(
            fao56_phenology_water_balance_df, x="date", y="ks",
            title="Ks Water-Stress Coefficient Over Time (Phenology-Aware)",
            labels={"date": "Date", "ks": "Ks"},
        )
        st.plotly_chart(phen_ks_fig, use_container_width=True)

        phen_stress_level_counts_df = (
            fao56_phenology_water_balance_df["water_stress_level"]
            .value_counts()
            .reindex(["Low", "Medium", "High"], fill_value=0)
            .rename_axis("water_stress_level")
            .reset_index(name="days")
        )
        phen_stress_level_fig = px.bar(
            phen_stress_level_counts_df, x="water_stress_level", y="days",
            title="Water-Stress Level Counts (full date range, phenology-aware)",
            labels={"water_stress_level": "Water-stress level", "days": "Number of days"},
        )
        st.plotly_chart(phen_stress_level_fig, use_container_width=True)

        phen_wb_stage_order = [
            "Flowering",
            "Fruit set",
            "Fruit development",
            "Maturity / harvest",
            "Rest / vegetative phase",
            "Flower induction / pre-flowering",
        ]
        stages_present = [
            s for s in phen_wb_stage_order
            if s in fao56_phenology_water_balance_df["mango_stage"].unique()
        ]

        stress_by_stage_df = (
            fao56_phenology_water_balance_df
            .groupby(["mango_stage", "water_stress_level"])
            .size()
            .reset_index(name="days")
        )
        stress_by_stage_fig = px.bar(
            stress_by_stage_df, x="mango_stage", y="days", color="water_stress_level",
            title="Water-Stress Level by Mango Stage",
            labels={"mango_stage": "Mango stage", "days": "Number of days", "water_stress_level": "Water-stress level"},
            category_orders={"mango_stage": stages_present, "water_stress_level": ["Low", "Medium", "High"]},
        )
        st.plotly_chart(stress_by_stage_fig, use_container_width=True)

        etc_by_stage_df = (
            fao56_phenology_water_balance_df
            .groupby("mango_stage")["etc_mm_day"]
            .mean()
            .reindex(stages_present)
            .rename_axis("mango_stage")
            .reset_index(name="avg_etc_mm_day")
        )
        etc_by_stage_fig = px.bar(
            etc_by_stage_df, x="mango_stage", y="avg_etc_mm_day",
            title="Average ETc by Mango Stage",
            labels={"mango_stage": "Mango stage", "avg_etc_mm_day": "Average ETc (mm/day)"},
            category_orders={"mango_stage": stages_present},
        )
        st.plotly_chart(etc_by_stage_fig, use_container_width=True)

        st.divider()

        if fao56_water_balance_df is not None and not fao56_water_balance_df.empty:
            st.subheader("Comparison with Constant-Kc FAO-56 (Prototype Comparison)")
            st.caption(
                "**Prototype comparison only** — both models share the same ET0/TAW/RAW/depletion "
                "logic and only differ in how Kc is assigned (constant 0.75 vs. stage-aware). This "
                "is not a validated benchmark against field data."
            )

            comparison_df = pd.merge(
                fao56_water_balance_df[["date", "etc_mm", "water_stress_level"]].rename(
                    columns={"etc_mm": "etc_mm_constant_kc", "water_stress_level": "water_stress_level_constant_kc"}
                ),
                fao56_phenology_water_balance_df[["date", "etc_mm_day", "water_stress_level"]].rename(
                    columns={"etc_mm_day": "etc_mm_phenology_kc", "water_stress_level": "water_stress_level_phenology_kc"}
                ),
                on="date", how="inner",
            )

            if comparison_df.empty:
                st.info(
                    "No overlapping dates found between the constant-Kc and phenology-aware "
                    "FAO-56 outputs, so a direct comparison can't be shown yet."
                )
            else:
                etc_compare_fig = px.line(
                    comparison_df, x="date", y=["etc_mm_constant_kc", "etc_mm_phenology_kc"],
                    title="ETc: Constant-Kc vs. Phenology-Aware Kc",
                    labels={"date": "Date", "value": "ETc (mm/day)", "variable": "Model"},
                )
                st.plotly_chart(etc_compare_fig, use_container_width=True)

                constant_kc_counts = (
                    comparison_df["water_stress_level_constant_kc"]
                    .value_counts()
                    .reindex(["Low", "Medium", "High"], fill_value=0)
                )
                phenology_kc_counts = (
                    comparison_df["water_stress_level_phenology_kc"]
                    .value_counts()
                    .reindex(["Low", "Medium", "High"], fill_value=0)
                )
                stress_compare_df = pd.DataFrame({
                    "water_stress_level": ["Low", "Medium", "High"],
                    "Constant Kc": constant_kc_counts.values,
                    "Phenology-Aware Kc": phenology_kc_counts.values,
                }).melt(id_vars="water_stress_level", var_name="Model", value_name="days")

                stress_compare_fig = px.bar(
                    stress_compare_df, x="water_stress_level", y="days", color="Model", barmode="group",
                    title="Water-Stress Level Counts: Constant Kc vs. Phenology-Aware Kc",
                    labels={"water_stress_level": "Water-stress level", "days": "Number of days"},
                    category_orders={"water_stress_level": ["Low", "Medium", "High"]},
                )
                st.plotly_chart(stress_compare_fig, use_container_width=True)
        else:
            st.info(
                "Constant-Kc FAO-56 output not found — run "
                "`python src/water_balance/fao56_water_balance.py` to enable the comparison view."
            )

        st.divider()

        st.subheader("Interpretation")

        st.write("- **Kc changes by mango stage** instead of staying fixed — flowering, fruit set, fruit development, maturity/harvest, and rest each get their own assumed value.")
        st.write("- **Higher Kc means higher crop water demand** for the same atmospheric ET0.")
        st.write("- **Fruit development and fruit set usually have higher water sensitivity**, which is reflected in their higher assumed Kc values (0.90 and 0.85).")
        st.write("- **This model is still assumption-based and not field-calibrated** — the Kc-by-stage values are first-pass estimates from general mango/FAO-56 guidance, not measurements from this orchard.")

        st.divider()

        st.subheader("Disclaimer")
        st.info(
            "This is a simplified phenology-aware prototype. Kc values are assumed, not "
            "cultivar-specific, not field-calibrated, and irrigation events are not yet included."
        )

        st.divider()

        st.subheader("Raw Phenology-Aware FAO-56 Water Balance Table")

        with st.expander("Phenology-aware FAO-56 water balance table (full)", expanded=False):
            phen_wb_preview = fao56_phenology_water_balance_df.copy()
            phen_wb_preview["date"] = phen_wb_preview["date"].dt.strftime("%Y-%m-%d")
            numeric_columns = phen_wb_preview.select_dtypes(include="number").columns
            phen_wb_preview[numeric_columns] = phen_wb_preview[numeric_columns].round(3)
            st.dataframe(phen_wb_preview, use_container_width=True)

        if fao56_water_balance_df is not None and not fao56_water_balance_df.empty:
            with st.expander("Constant-Kc FAO-56 water balance table (full, for comparison)", expanded=False):
                const_wb_preview = fao56_water_balance_df.copy()
                const_wb_preview["date"] = const_wb_preview["date"].dt.strftime("%Y-%m-%d")
                numeric_columns = const_wb_preview.select_dtypes(include="number").columns
                const_wb_preview[numeric_columns] = const_wb_preview[numeric_columns].round(3)
                st.dataframe(const_wb_preview, use_container_width=True)
