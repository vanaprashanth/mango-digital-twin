"""
Central configuration loader for the Sensor-Free Mango Digital Twin.

Every script in the project should pull coordinates, dates, file paths, and
risk thresholds from here instead of hardcoding them. This makes it
possible to point the whole pipeline at a different orchard/location by
editing a single YAML file.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Optional

import yaml

# Project root = two levels up from this file (src/utils/config.py -> project root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "config.yaml"


@dataclass(frozen=True)
class StudyArea:
    name: str
    district: str
    state: str
    country: str
    latitude: float
    longitude: float


class Config:
    """
    Thin wrapper around the YAML config that resolves paths relative to the
    project root and exposes the most commonly used values as convenient
    attributes.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found at {self.config_path}. "
                "Expected a configs/config.yaml at the project root."
            )

        with open(self.config_path, "r") as f:
            self._raw: dict[str, Any] = yaml.safe_load(f)

        self.study_area = StudyArea(**self._raw["study_area"])
        self.historical_weather = self._raw["historical_weather"]
        self.forecast_weather = self._raw["forecast_weather"]
        self.soil = self._raw["soil"]
        self.risk_thresholds = self._raw["risk_thresholds"]
        # Optional: older config.yaml files (before the Sentinel-2 prep
        # phase) won't have this section. Default to an empty dict so
        # get_config() doesn't break on existing setups.
        self.remote_sensing = self._raw.get("remote_sensing", {})

    # ------------------------------------------------------------------
    # Path helpers — always resolved relative to the project root so the
    # pipeline behaves the same regardless of the current working directory.
    # ------------------------------------------------------------------

    def path(self, key: str) -> Path:
        """Return an absolute Path for a given key in the `paths` config section."""
        relative_path = self._raw["paths"][key]
        return PROJECT_ROOT / relative_path

    @property
    def latitude(self) -> float:
        return self.study_area.latitude

    @property
    def longitude(self) -> float:
        return self.study_area.longitude

    # ------------------------------------------------------------------
    # Historical date range helpers
    # ------------------------------------------------------------------

    def historical_start_date(self, fmt: str = "%Y%m%d") -> str:
        start = self.historical_weather["start_date"]
        return date.fromisoformat(start).strftime(fmt)

    def historical_end_date(self, fmt: str = "%Y%m%d") -> str:
        end = self.historical_weather.get("end_date")
        if end is None:
            return date.today().strftime(fmt)
        return date.fromisoformat(end).strftime(fmt)

    def get_threshold(self, group: str, key: str) -> float:
        return self.risk_thresholds[group][key]

    # ------------------------------------------------------------------
    # Remote sensing (Sentinel-2 / Google Earth Engine) helpers.
    # Setup-phase only: these just read the config values above. They do
    # not fetch satellite data or talk to Earth Engine.
    # ------------------------------------------------------------------

    def remote_sensing_start_date(self, fmt: str = "%Y-%m-%d") -> str:
        start = self.remote_sensing.get("start_date", self.historical_weather["start_date"])
        return date.fromisoformat(start).strftime(fmt)

    def remote_sensing_end_date(self, fmt: str = "%Y-%m-%d") -> str:
        end = self.remote_sensing.get("end_date")
        if end is None:
            return date.today().strftime(fmt)
        return date.fromisoformat(end).strftime(fmt)


_default_config_instance: Optional[Config] = None


def get_config(config_path: Optional[Path] = None) -> Config:
    """
    Return a cached Config instance. Pass an explicit config_path only if
    you need to load a non-default config (e.g. in tests).
    """
    global _default_config_instance

    if config_path is not None:
        return Config(config_path)

    if _default_config_instance is None:
        _default_config_instance = Config()

    return _default_config_instance
