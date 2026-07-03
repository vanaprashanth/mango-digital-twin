from __future__ import annotations

import pandas as pd
import streamlit as st


def render_raw_data_page(
    df: pd.DataFrame,
    forecast_df: pd.DataFrame | None,
    soil_df: pd.DataFrame | None,
    vegetation_df: pd.DataFrame | None,
    phenology_df: pd.DataFrame | None,
    fao56_phenology_water_balance_df: pd.DataFrame | None,
) -> None:
    """Render the Raw Processed Data dashboard page."""

    st.title("Raw Processed Data")

    st.write("### Historical Risk Data")
    with st.expander("Historical risk table (last 20 rows)", expanded=False):
        preview_df = df.tail(20).copy()
        numeric_columns = preview_df.select_dtypes(include="number").columns
        preview_df[numeric_columns] = preview_df[numeric_columns].round(2)
        st.dataframe(preview_df, use_container_width=True)

    if forecast_df is not None and not forecast_df.empty:
        st.write("### Forecast Risk Data")
        with st.expander("Forecast risk table (full)", expanded=False):
            forecast_preview = forecast_df.copy()
            numeric_columns = forecast_preview.select_dtypes(include="number").columns
            forecast_preview[numeric_columns] = forecast_preview[numeric_columns].round(2)
            st.dataframe(forecast_preview, use_container_width=True)

    if soil_df is not None and not soil_df.empty:
        st.write("### SoilGrids Raw Data")
        with st.expander("SoilGrids raw points", expanded=False):
            st.dataframe(soil_df, use_container_width=True)

    if vegetation_df is not None and not vegetation_df.empty:
        st.write("### Sentinel-2 Daily Vegetation Data")
        with st.expander("Sentinel-2 daily vegetation table (full)", expanded=False):
            veg_preview = vegetation_df.copy()
            veg_preview["date"] = veg_preview["date"].dt.strftime("%Y-%m-%d")
            numeric_columns = veg_preview.select_dtypes(include="number").columns
            veg_preview[numeric_columns] = veg_preview[numeric_columns].round(3)
            st.dataframe(veg_preview, use_container_width=True)

    if phenology_df is not None and not phenology_df.empty:
        st.write("### Mango Phenology Calendar Data")
        with st.expander("Mango phenology calendar table (full)", expanded=False):
            phenology_raw_preview = phenology_df.copy()
            phenology_raw_preview["date"] = phenology_raw_preview["date"].dt.strftime("%Y-%m-%d")
            st.dataframe(phenology_raw_preview, use_container_width=True)

    if fao56_phenology_water_balance_df is not None and not fao56_phenology_water_balance_df.empty:
        st.write("### Phenology-Aware FAO-56 Water Balance Data")
        with st.expander("Phenology-aware FAO-56 water balance table (full)", expanded=False):
            phen_wb_raw_preview = fao56_phenology_water_balance_df.copy()
            phen_wb_raw_preview["date"] = phen_wb_raw_preview["date"].dt.strftime("%Y-%m-%d")
            numeric_columns = phen_wb_raw_preview.select_dtypes(include="number").columns
            phen_wb_raw_preview[numeric_columns] = phen_wb_raw_preview[numeric_columns].round(3)
            st.dataframe(phen_wb_raw_preview, use_container_width=True)
