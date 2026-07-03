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


def render_forecast_risk_page(forecast_df: pd.DataFrame | None) -> None:
    """Render the Forecast Risk Intelligence dashboard page."""

    st.title("Forecast Risk Intelligence")

    if forecast_df is None or forecast_df.empty:
        st.warning("Forecast risk file not found.")
        st.info("Please run: python src/weather/fetch_open_meteo.py and then python src/risk/open_meteo_risk_engine.py")
    else:
        forecast_latest = forecast_df.iloc[-1]
        has_soil_adjusted_forecast_irrigation = "soil_adjusted_irrigation_risk_level" in forecast_df.columns

        st.caption(
            "Open-Meteo recent and forecast weather risk layer — future risk is computed by applying "
            "our risk rules to Open-Meteo's API forecast values, not by a trained prediction model."
        )

        forecast_period_start = forecast_df["date"].min().strftime("%Y-%m-%d")
        forecast_period_end = forecast_df["date"].max().strftime("%Y-%m-%d")

        st.metric(
            label="Forecast date range",
            value=f"{forecast_period_start} \u2192 {forecast_period_end}",
            delta=f"{len(forecast_df)} days"
        )

        forecast_col1, forecast_col2, forecast_col3, forecast_col4 = st.columns(4)

        with forecast_col1:
            st.metric(label="Forecast irrigation risk (weather only)", value=_risk_color(forecast_latest["irrigation_risk_level"]))

        with forecast_col2:
            if has_soil_adjusted_forecast_irrigation:
                st.metric(label="Forecast irrigation risk (soil-adjusted)", value=_risk_color(forecast_latest["soil_adjusted_irrigation_risk_level"]))
            else:
                st.metric(label="Forecast irrigation risk (soil-adjusted)", value="N/A")

        with forecast_col3:
            st.metric(label="Forecast heat stress risk", value=_risk_color(forecast_latest["heat_stress_risk_level"]))

        with forecast_col4:
            st.metric(label="Forecast disease risk", value=_risk_color(forecast_latest["disease_risk_level"]))

        st.write("### Forecast Weather Conditions")

        forecast_weather_col1, forecast_weather_col2, forecast_weather_col3, forecast_weather_col4 = st.columns(4)

        with forecast_weather_col1:
            st.metric(label="Forecast max temperature", value=f"{forecast_latest['temperature_max_c']:.2f} \u00b0C")

        with forecast_weather_col2:
            st.metric(label="Forecast avg temperature", value=f"{forecast_latest['temperature_avg_c']:.2f} \u00b0C")

        with forecast_weather_col3:
            st.metric(label="Forecast rainfall", value=f"{forecast_latest['rainfall_mm']:.2f} mm")

        with forecast_weather_col4:
            st.metric(label="Forecast 7-day rainfall", value=f"{forecast_latest['rainfall_7day_mm']:.2f} mm")

        st.write("### Forecast Rainfall Trend")
        forecast_rain_fig = px.line(
            forecast_df, x="date", y=["rainfall_mm", "rainfall_7day_mm"],
            title="Open-Meteo Forecast Rainfall and 7-Day Rolling Rainfall",
            labels={"date": "Date", "value": "Rainfall (mm)", "variable": "Metric"}
        )
        st.plotly_chart(forecast_rain_fig, use_container_width=True)

        st.write("### Forecast Temperature Trend")
        forecast_temp_fig = px.line(
            forecast_df, x="date", y=["temperature_avg_c", "temperature_max_c", "temperature_min_c"],
            title="Open-Meteo Forecast Temperature",
            labels={"date": "Date", "value": "Temperature (\u00b0C)", "variable": "Metric"}
        )
        st.plotly_chart(forecast_temp_fig, use_container_width=True)

        st.write("### Forecast Risk Score Trend")
        forecast_risk_fig = px.line(
            forecast_df, x="date",
            y=["irrigation_risk_score", "heat_stress_risk_score", "disease_risk_score"],
            title="Open-Meteo Forecast Mango Risk Scores",
            labels={"date": "Date", "value": "Risk score", "variable": "Risk type"}
        )
        st.plotly_chart(forecast_risk_fig, use_container_width=True)

        st.write("### Forecast Risk Table")

        forecast_table_columns = [
            "date", "rainfall_mm", "rainfall_7day_mm", "temperature_max_c",
            "relative_humidity_percent", "irrigation_risk_level",
        ]

        if has_soil_adjusted_forecast_irrigation:
            forecast_table_columns.append("soil_adjusted_irrigation_risk_level")

        forecast_table_columns += ["heat_stress_risk_level", "disease_risk_level"]

        forecast_table_df = forecast_df[forecast_table_columns].copy()
        forecast_table_df["date"] = forecast_table_df["date"].dt.strftime("%Y-%m-%d")

        numeric_forecast_columns = forecast_table_df.select_dtypes(include="number").columns
        forecast_table_df[numeric_forecast_columns] = forecast_table_df[numeric_forecast_columns].round(2)

        forecast_table_df = forecast_table_df.rename(columns={
            "date": "Date",
            "rainfall_mm": "Rainfall (mm)",
            "rainfall_7day_mm": "7-day rainfall (mm)",
            "temperature_max_c": "Max temp (\u00b0C)",
            "relative_humidity_percent": "Humidity (%)",
            "irrigation_risk_level": "Irrigation risk",
            "soil_adjusted_irrigation_risk_level": "Irrigation risk (soil-adjusted)",
            "heat_stress_risk_level": "Heat stress risk",
            "disease_risk_level": "Disease risk",
        })

        with st.expander("Forecast risk table (all future dates)", expanded=True):
            st.dataframe(forecast_table_df, use_container_width=True)

        st.write("### Forecast Advisory")

        forecast_recommendations = []

        if forecast_latest["irrigation_risk_level"] == "High":
            forecast_recommendations.append("Forecast irrigation risk is high. Plan irrigation because upcoming rainfall may be insufficient.")
        elif forecast_latest["irrigation_risk_level"] == "Medium":
            forecast_recommendations.append("Forecast irrigation risk is medium. Monitor rainfall and soil moisture conditions closely.")
        else:
            forecast_recommendations.append("Forecast irrigation risk is low based on upcoming rainfall and temperature.")

        if forecast_latest["heat_stress_risk_level"] == "High":
            forecast_recommendations.append("Forecast heat stress is high. Avoid stressful orchard operations during peak heat periods.")
        elif forecast_latest["heat_stress_risk_level"] == "Medium":
            forecast_recommendations.append("Forecast heat stress is medium. Continue monitoring maximum temperature.")
        else:
            forecast_recommendations.append("Forecast heat stress is low.")

        if forecast_latest["disease_risk_level"] == "High":
            forecast_recommendations.append("Forecast disease-friendly conditions are high. Monitor orchard for fungal symptoms.")
        elif forecast_latest["disease_risk_level"] == "Medium":
            forecast_recommendations.append("Forecast disease-friendly conditions are medium. Watch humidity and rainfall conditions.")
        else:
            forecast_recommendations.append("Forecast disease risk is low.")

        for rec in forecast_recommendations:
            st.write(f"- {rec}")
