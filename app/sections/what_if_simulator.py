from __future__ import annotations

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


def _classify_risk(score: float) -> str:
    """Convert numeric risk score into category."""
    if score >= 0.70:
        return "High"
    elif score >= 0.40:
        return "Medium"
    else:
        return "Low"


def simulate_weather_risk(
    rainfall_7day_mm: float,
    temperature_max_c: float,
    temperature_avg_c: float,
    relative_humidity_percent: float,
    solar_radiation_mj_m2: float,
    rainfall_change_percent: float,
    temperature_change_c: float,
    humidity_change_percent: float,
) -> dict:
    """Simulate mango risk under changed weather conditions."""

    simulated_rainfall_7day = rainfall_7day_mm * (1 + rainfall_change_percent / 100)
    simulated_temp_max = temperature_max_c + temperature_change_c
    simulated_temp_avg = temperature_avg_c + temperature_change_c
    simulated_humidity = relative_humidity_percent + humidity_change_percent

    simulated_humidity = max(0, min(simulated_humidity, 100))
    simulated_rainfall_7day = max(0, simulated_rainfall_7day)

    irrigation_score = 0.0

    if simulated_rainfall_7day < 10:
        irrigation_score += 0.45
    elif simulated_rainfall_7day < 25:
        irrigation_score += 0.25

    if simulated_temp_max >= 35:
        irrigation_score += 0.35
    elif simulated_temp_max >= 32:
        irrigation_score += 0.20

    if solar_radiation_mj_m2 >= 22:
        irrigation_score += 0.20
    elif solar_radiation_mj_m2 >= 18:
        irrigation_score += 0.10

    irrigation_score = min(irrigation_score, 1.0)

    heat_score = 0.0

    if simulated_temp_max >= 40:
        heat_score += 0.80
    elif simulated_temp_max >= 37:
        heat_score += 0.60
    elif simulated_temp_max >= 35:
        heat_score += 0.40
    elif simulated_temp_max >= 32:
        heat_score += 0.20

    if simulated_temp_avg >= 30:
        heat_score += 0.20

    heat_score = min(heat_score, 1.0)

    disease_score = 0.0

    if simulated_humidity >= 85:
        disease_score += 0.45
    elif simulated_humidity >= 75:
        disease_score += 0.30
    elif simulated_humidity >= 65:
        disease_score += 0.15

    if 24 <= simulated_temp_avg <= 30:
        disease_score += 0.30
    elif 20 <= simulated_temp_avg < 24:
        disease_score += 0.15

    if simulated_rainfall_7day >= 40:
        disease_score += 0.25
    elif simulated_rainfall_7day >= 15:
        disease_score += 0.10

    disease_score = min(disease_score, 1.0)

    return {
        "simulated_rainfall_7day_mm": simulated_rainfall_7day,
        "simulated_temperature_max_c": simulated_temp_max,
        "simulated_temperature_avg_c": simulated_temp_avg,
        "simulated_humidity_percent": simulated_humidity,
        "irrigation_risk_score": irrigation_score,
        "heat_stress_risk_score": heat_score,
        "disease_risk_score": disease_score,
        "irrigation_risk_level": _classify_risk(irrigation_score),
        "heat_stress_risk_level": _classify_risk(heat_score),
        "disease_risk_level": _classify_risk(disease_score),
    }


def generate_simulation_explanation(simulation: dict) -> list[str]:
    """Generate human-readable explanations for simulated risk results."""

    explanations = []

    rainfall_7day = simulation["simulated_rainfall_7day_mm"]
    temp_max = simulation["simulated_temperature_max_c"]
    temp_avg = simulation["simulated_temperature_avg_c"]
    humidity = simulation["simulated_humidity_percent"]

    irrigation_level = simulation["irrigation_risk_level"]
    heat_level = simulation["heat_stress_risk_level"]
    disease_level = simulation["disease_risk_level"]

    if irrigation_level == "High":
        explanations.append(
            "Irrigation risk is high because simulated 7-day rainfall is low and/or temperature stress is elevated."
        )
    elif irrigation_level == "Medium":
        explanations.append(
            "Irrigation risk is medium because rainfall or temperature conditions may create moderate water stress."
        )
    else:
        explanations.append(
            "Irrigation risk is low because simulated recent rainfall is sufficient or temperature stress is limited."
        )

    if heat_level == "High":
        explanations.append(
            f"Heat stress is high because simulated maximum temperature reaches {temp_max:.2f} \u00b0C."
        )
    elif heat_level == "Medium":
        explanations.append(
            f"Heat stress is medium because simulated maximum temperature is {temp_max:.2f} \u00b0C."
        )
    else:
        explanations.append(
            f"Heat stress is low because simulated maximum temperature is {temp_max:.2f} \u00b0C."
        )

    if disease_level == "High":
        explanations.append(
            f"Disease-friendly weather is high because humidity is {humidity:.2f}% and recent rainfall is {rainfall_7day:.2f} mm."
        )
    elif disease_level == "Medium":
        explanations.append(
            f"Disease-friendly weather is medium because humidity is {humidity:.2f}% with moderate rainfall or suitable temperature."
        )
    else:
        explanations.append(
            "Disease risk is low because humidity, rainfall, or temperature are not strongly disease-favorable."
        )

    if rainfall_7day < 10:
        explanations.append(
            "The simulated 7-day rainfall is below 10 mm, which may increase water-stress risk."
        )

    if temp_max >= 35:
        explanations.append(
            "The simulated maximum temperature is above 35 \u00b0C, which may increase mango heat stress."
        )

    if humidity >= 75 and 24 <= temp_avg <= 30:
        explanations.append(
            "Humidity is high and average temperature is within a disease-favorable range, so fungal-risk conditions may increase."
        )

    return explanations


def render_what_if_simulator_page(latest: "object") -> None:
    """Render the What-if Simulator dashboard page."""

    st.title("What-if Simulator")
    show_freshness_indicator(label="What-if simulator", staleness_warning_days=0)

    st.write("Test how mango risk changes if rainfall, temperature, or humidity changes from the latest valid weather condition.")

    sim_col1, sim_col2, sim_col3 = st.columns(3)

    with sim_col1:
        rainfall_change_percent = st.slider("Rainfall change (%)", min_value=-100, max_value=100, value=0, step=5)

    with sim_col2:
        temperature_change_c = st.slider("Temperature change (\u00b0C)", min_value=-5.0, max_value=8.0, value=0.0, step=0.5)

    with sim_col3:
        humidity_change_percent = st.slider("Humidity change (%)", min_value=-50, max_value=50, value=0, step=5)

    simulation = simulate_weather_risk(
        rainfall_7day_mm=latest["rainfall_7day_mm"],
        temperature_max_c=latest["temperature_max_c"],
        temperature_avg_c=latest["temperature_avg_c"],
        relative_humidity_percent=latest["relative_humidity_percent"],
        solar_radiation_mj_m2=latest["solar_radiation_mj_m2"],
        rainfall_change_percent=rainfall_change_percent,
        temperature_change_c=temperature_change_c,
        humidity_change_percent=humidity_change_percent,
    )

    st.write("### Simulated Weather Condition")

    sim_weather_col1, sim_weather_col2, sim_weather_col3, sim_weather_col4 = st.columns(4)

    with sim_weather_col1:
        st.metric(label="Simulated 7-day rainfall", value=f"{simulation['simulated_rainfall_7day_mm']:.2f} mm")

    with sim_weather_col2:
        st.metric(label="Simulated max temperature", value=f"{simulation['simulated_temperature_max_c']:.2f} \u00b0C")

    with sim_weather_col3:
        st.metric(label="Simulated avg temperature", value=f"{simulation['simulated_temperature_avg_c']:.2f} \u00b0C")

    with sim_weather_col4:
        st.metric(label="Simulated humidity", value=f"{simulation['simulated_humidity_percent']:.2f} %")

    st.write("### Simulated Risk Result")

    sim_risk_col1, sim_risk_col2, sim_risk_col3 = st.columns(3)

    with sim_risk_col1:
        st.metric(label="Simulated irrigation risk", value=_risk_color(simulation["irrigation_risk_level"]), delta=f"{simulation['irrigation_risk_score']:.2f}")

    with sim_risk_col2:
        st.metric(label="Simulated heat stress risk", value=_risk_color(simulation["heat_stress_risk_level"]), delta=f"{simulation['heat_stress_risk_score']:.2f}")

    with sim_risk_col3:
        st.metric(label="Simulated disease risk", value=_risk_color(simulation["disease_risk_level"]), delta=f"{simulation['disease_risk_score']:.2f}")

    st.write("### Scenario Explanation")

    simulation_explanations = generate_simulation_explanation(simulation)

    for explanation in simulation_explanations:
        st.write(f"- {explanation}")
