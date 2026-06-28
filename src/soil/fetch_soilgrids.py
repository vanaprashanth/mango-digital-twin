"""
SoilGrids soil intelligence pipeline.

Fetches static soil properties (texture, pH, organic carbon, bulk density,
CEC) for the study area defined in configs/config.yaml and writes them to
data/raw/muthukur_soilgrids.csv.
"""

import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validation import validate_soil_data

log = get_logger(__name__)

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"


def fetch_soilgrids_point(
    latitude: float,
    longitude: float,
    properties: list[str],
    depths: list[str],
) -> dict:
    """
    Fetch SoilGrids soil properties for one point location.
    """

    params = {
        "lat": latitude,
        "lon": longitude,
        "property": properties,
        "depth": depths,
        "value": "mean",
    }

    try:
        response = requests.get(SOILGRIDS_URL, params=params, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            f"SoilGrids API request failed: {exc}. "
            "SoilGrids can be slow or briefly unavailable — check your "
            "internet connection and try again in a minute. "
            f"URL: {SOILGRIDS_URL}"
        ) from exc

    return response.json()


def parse_soilgrids_response(data: dict) -> pd.DataFrame:
    """
    Parse SoilGrids JSON response into a clean table.

    SoilGrids values often use scaling factors:
    - sand/silt/clay are usually g/kg, divide by 10 to get %
    - phh2o is usually pH x 10, divide by 10
    - soc is usually dg/kg, divide by 10 to get g/kg
    - bdod is usually cg/cm3, divide by 100 to get g/cm3
    - cec is usually mmol(c)/kg
    """

    rows = []

    if "properties" not in data or "layers" not in data["properties"]:
        raise RuntimeError(
            "SoilGrids API returned an unexpected response (no soil "
            f"layers found). Raw response: {data}"
        )

    layers = data["properties"]["layers"]

    for layer in layers:
        property_name = layer["name"]

        for depth_info in layer["depths"]:
            depth_label = depth_info["label"]
            raw_value = depth_info["values"]["mean"]

            converted_value = raw_value
            unit = "raw"

            if property_name in ["sand", "silt", "clay"]:
                converted_value = raw_value / 10
                unit = "percent"

            elif property_name == "phh2o":
                converted_value = raw_value / 10
                unit = "pH"

            elif property_name == "soc":
                converted_value = raw_value / 10
                unit = "g/kg"

            elif property_name == "bdod":
                converted_value = raw_value / 100
                unit = "g/cm3"

            elif property_name == "cec":
                converted_value = raw_value / 10
                unit = "cmol(c)/kg"

            rows.append(
                {
                    "property": property_name,
                    "depth": depth_label,
                    "raw_value": raw_value,
                    "converted_value": converted_value,
                    "unit": unit,
                }
            )

    return pd.DataFrame(rows)


def create_topsoil_summary(soil_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a simple topsoil summary using 0-30 cm average.
    """

    summary = (
        soil_df
        .groupby("property")
        .agg(
            average_0_30cm=("converted_value", "mean"),
            unit=("unit", "first"),
        )
        .reset_index()
    )

    return summary


def main():
    config = get_config()

    output_path = config.path("soilgrids_csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Starting SoilGrids soil data fetch...")
    log.info(
        "Location: %s, %s district (lat=%s, lon=%s)",
        config.study_area.name,
        config.study_area.district,
        config.latitude,
        config.longitude,
    )

    try:
        soil_json = fetch_soilgrids_point(
            latitude=config.latitude,
            longitude=config.longitude,
            properties=config.soil["properties"],
            depths=config.soil["depths"],
        )
        soil_df = parse_soilgrids_response(soil_json)
        validate_soil_data(soil_df)
    except Exception:
        log.error("SoilGrids fetch FAILED. See details below.")
        raise

    soil_df.to_csv(output_path, index=False)

    topsoil_summary = create_topsoil_summary(soil_df)

    log.info("SoilGrids soil data saved successfully.")
    log.info("Output file: %s", output_path)
    print()
    print("Detailed soil data:")
    print(soil_df)
    print()
    print("Topsoil 0-30 cm summary:")
    print(topsoil_summary)


if __name__ == "__main__":
    main()
