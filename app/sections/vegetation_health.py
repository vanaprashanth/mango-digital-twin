from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
from app.sections.freshness import show_freshness_indicator


def render_vegetation_health_page(
    vegetation_df: pd.DataFrame | None,
    vegetation_timeseries_df: pd.DataFrame | None,
    sentinel1_df: pd.DataFrame | None = None,
) -> None:
    """Render the Vegetation Health (Sentinel-2) dashboard page."""

    st.title("Vegetation Health (Sentinel-2)")
    show_freshness_indicator(vegetation_df, label="Vegetation health", staleness_warning_days=14)

    st.caption(
        "Satellite-derived vegetation/water indices from Sentinel-2 imagery, aggregated to one "
        "row per day. This is a separate signal from the weather/soil risk pages above — it is "
        "not yet merged into the irrigation/heat/disease risk scores."
    )

    if vegetation_df is None or vegetation_df.empty:
        st.warning("Sentinel-2 daily vegetation file not found or could not be loaded.")
        st.info("Please run: python src/remote_sensing/aggregate_sentinel2_timeseries.py")
        st.info(
            "(That script itself needs the time series file from "
            "`python src/remote_sensing/build_sentinel2_index_timeseries.py`, which in turn needs "
            "Earth Engine set up via `python src/remote_sensing/gee_setup.py`.)"
        )
    else:
        veg_latest = vegetation_df.iloc[-1]

        st.write("### What these indices mean")
        index_explain_col1, index_explain_col2, index_explain_col3, index_explain_col4 = st.columns(4)
        with index_explain_col1:
            st.caption("**NDVI** — vegetation greenness")
        with index_explain_col2:
            st.caption("**NDWI** — water / surface water signal")
        with index_explain_col3:
            st.caption("**NDMI** — vegetation moisture")
        with index_explain_col4:
            st.caption("**NDRE** — chlorophyll / canopy stress signal")

        st.divider()

        st.subheader("Latest Sentinel-2 Reading")

        veg_metric_col1, veg_metric_col2, veg_metric_col3, veg_metric_col4, veg_metric_col5, veg_metric_col6 = st.columns(6)

        with veg_metric_col1:
            st.metric(label="Latest date", value=veg_latest["date"].strftime("%Y-%m-%d"))

        with veg_metric_col2:
            st.metric(label="NDVI", value=f"{veg_latest['ndvi_mean']:.3f}")

        with veg_metric_col3:
            st.metric(label="NDMI", value=f"{veg_latest['ndmi_mean']:.3f}")

        with veg_metric_col4:
            st.metric(label="NDRE", value=f"{veg_latest['ndre_mean']:.3f}")

        with veg_metric_col5:
            st.metric(label="Cloud cover", value=f"{veg_latest['cloud_percentage']:.1f}%")

        with veg_metric_col6:
            st.metric(label="Scenes that day", value=int(veg_latest["scene_count"]))

        st.write("### Interpretation")

        interp_col1, interp_col2, interp_col3 = st.columns(3)

        with interp_col1:
            st.info(f"**NDVI level:** {veg_latest['ndvi_level']}")

        with interp_col2:
            st.info(f"**Moisture level:** {veg_latest['moisture_level']}")

        with interp_col3:
            st.info(f"**Canopy stress level:** {veg_latest['canopy_stress_level']}")

        st.divider()

        st.subheader("Vegetation Index Trends")

        ndvi_fig = px.line(
            vegetation_df, x="date", y="ndvi_mean",
            title="NDVI Over Time (vegetation greenness)",
            labels={"date": "Date", "ndvi_mean": "NDVI"},
        )
        st.plotly_chart(ndvi_fig, use_container_width=True)

        ndmi_fig = px.line(
            vegetation_df, x="date", y="ndmi_mean",
            title="NDMI Over Time (vegetation moisture)",
            labels={"date": "Date", "ndmi_mean": "NDMI"},
        )
        st.plotly_chart(ndmi_fig, use_container_width=True)

        ndre_fig = px.line(
            vegetation_df, x="date", y="ndre_mean",
            title="NDRE Over Time (chlorophyll / canopy stress signal)",
            labels={"date": "Date", "ndre_mean": "NDRE"},
        )
        st.plotly_chart(ndre_fig, use_container_width=True)

        ndwi_fig = px.line(
            vegetation_df, x="date", y="ndwi_mean",
            title="NDWI Over Time (surface water signal)",
            labels={"date": "Date", "ndwi_mean": "NDWI"},
        )
        st.plotly_chart(ndwi_fig, use_container_width=True)

        st.write("### Combined Index View")
        combined_fig = px.line(
            vegetation_df, x="date",
            y=["ndvi_mean", "ndwi_mean", "ndmi_mean", "ndre_mean"],
            title="NDVI, NDWI, NDMI, and NDRE Over Time",
            labels={"date": "Date", "value": "Index value", "variable": "Index"},
        )
        st.plotly_chart(combined_fig, use_container_width=True)

        st.divider()

        st.subheader("Raw Tables")

        with st.expander("Daily Sentinel-2 vegetation index table", expanded=False):
            daily_preview = vegetation_df.copy()
            daily_preview["date"] = daily_preview["date"].dt.strftime("%Y-%m-%d")
            numeric_columns = daily_preview.select_dtypes(include="number").columns
            daily_preview[numeric_columns] = daily_preview[numeric_columns].round(3)
            st.dataframe(daily_preview, use_container_width=True)

        if vegetation_timeseries_df is not None and not vegetation_timeseries_df.empty:
            with st.expander("Image-level Sentinel-2 table (one row per scene)", expanded=False):
                image_preview = vegetation_timeseries_df.copy()
                image_preview["date"] = image_preview["date"].dt.strftime("%Y-%m-%d")
                numeric_columns = image_preview.select_dtypes(include="number").columns
                image_preview[numeric_columns] = image_preview[numeric_columns].round(3)
                st.dataframe(image_preview, use_container_width=True)


    # ------------------------------------------------------------------
    # Sentinel-1 SAR fallback section (cloudy-season proxy signals)
    # ------------------------------------------------------------------
    st.divider()
    st.subheader("Sentinel-1 SAR Backscatter (Cloudy-Season Fallback)")

    st.warning(
        "⚠️ **These are radar backscatter proxy signals, not direct NDVI or "
        "field-calibrated soil-moisture measurements.** VV and VH backscatter "
        "values (dB) correlate loosely with surface roughness, soil moisture, "
        "and canopy structure under specific conditions, but they have NOT been "
        "calibrated against field observations at Muthukur or for mango orchards. "
        "Use them as directional signals during periods when Sentinel-2 optical "
        "imagery is unavailable due to cloud cover — not as substitutes for "
        "ground-truth measurements."
    )

    if sentinel1_df is None or sentinel1_df.empty:
        st.info(
            "Sentinel-1 SAR daily file not found or could not be loaded. "
            "To enable this section, run:\n"
            "1. `python src/remote_sensing/build_sentinel1_sar_timeseries.py`\n"
            "2. `python src/remote_sensing/aggregate_sentinel1_timeseries.py`\n"
            "Or use `python main.py --refresh-sentinel2` (refreshes both S2 and S1 if "
            "GEE credentials are configured)."
        )
    else:
        s1_latest = sentinel1_df.iloc[-1]
        latest_date = s1_latest["date"]
        latest_date_str = latest_date.strftime("%Y-%m-%d") if hasattr(latest_date, "strftime") else str(latest_date)

        st.caption(
            f"Latest Sentinel-1 scene: {latest_date_str} · "
            f"Orbit: {s1_latest.get('orbit_pass', 'N/A')} · "
            f"{int(s1_latest.get('scene_count', 1))} scene(s) averaged"
        )

        s1_col1, s1_col2, s1_col3 = st.columns(3)
        with s1_col1:
            st.metric(
                label="VV (surface/roughness proxy, dB)",
                value=f"{s1_latest['vv_mean']:.2f}" if s1_latest.get("vv_mean") is not None else "N/A",
            )
        with s1_col2:
            st.metric(
                label="VH (vegetation volume proxy, dB)",
                value=f"{s1_latest['vh_mean']:.2f}" if s1_latest.get("vh_mean") is not None else "N/A",
            )
        with s1_col3:
            st.metric(
                label="VV − VH ratio (dB)",
                value=f"{s1_latest['vv_vh_ratio_mean']:.2f}" if s1_latest.get("vv_vh_ratio_mean") is not None else "N/A",
            )

        if "vv_level" in sentinel1_df.columns and "vh_level" in sentinel1_df.columns:
            s1_interp_col1, s1_interp_col2 = st.columns(2)
            with s1_interp_col1:
                st.info(f"**VV signal:** {s1_latest.get('vv_level', 'Unknown')}")
            with s1_interp_col2:
                st.info(f"**VH signal:** {s1_latest.get('vh_level', 'Unknown')}")

        vv_fig = px.line(
            sentinel1_df, x="date", y="vv_mean",
            title="VV Backscatter Over Time (surface / soil roughness proxy)",
            labels={"date": "Date", "vv_mean": "VV (dB)"},
        )
        st.plotly_chart(vv_fig, use_container_width=True)

        vh_fig = px.line(
            sentinel1_df, x="date", y="vh_mean",
            title="VH Backscatter Over Time (vegetation volume proxy)",
            labels={"date": "Date", "vh_mean": "VH (dB)"},
        )
        st.plotly_chart(vh_fig, use_container_width=True)

        with st.expander("Daily Sentinel-1 SAR table", expanded=False):
            s1_preview = sentinel1_df.copy()
            if "date" in s1_preview.columns and hasattr(s1_preview["date"].iloc[0], "strftime"):
                s1_preview["date"] = s1_preview["date"].dt.strftime("%Y-%m-%d")
            numeric_cols = s1_preview.select_dtypes(include="number").columns
            s1_preview[numeric_cols] = s1_preview[numeric_cols].round(3)
            st.dataframe(s1_preview, use_container_width=True)
