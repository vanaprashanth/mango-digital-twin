"""Regression tests: the Overview map must use the modern Plotly `map` API (no mapbox)."""
from __future__ import annotations

import sys
from pathlib import Path

import plotly
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.sections.overview_map import build_study_area_map  # noqa: E402

LAT, LON = 13.6, 79.4   # arbitrary test coordinates (real ones come from config)


def test_map_builds_without_attribute_error():
    fig = build_study_area_map(LAT, LON)
    assert fig.data[0].type == "scattermap"
    assert fig.layout.map.style == "carto-positron"
    assert fig.layout.map.zoom == 8
    assert fig.layout.map.center.lat == LAT and fig.layout.map.center.lon == LON
    assert fig.data[0].marker.size == 14 and fig.data[0].marker.color == "red"
    assert "Study orchard" in fig.data[0].hovertext
    fig.to_dict()                     # serialises cleanly


def test_dark_theme_style_and_marker():
    fig = build_study_area_map(LAT, LON, "dark")
    assert fig.layout.map.style == "carto-darkmatter"
    assert fig.data[0].marker.color == "#ff4444"


def test_uses_real_config_coordinates():
    from src.utils.config import get_config
    cfg = get_config()
    fig = build_study_area_map(cfg.latitude, cfg.longitude)
    assert fig.data[0].lat[0] == cfg.latitude and fig.data[0].lon[0] == cfg.longitude


def test_installed_plotly_has_scatter_map():
    import plotly.express as px
    assert hasattr(px, "scatter_map")
    assert tuple(int(x) for x in plotly.__version__.split(".")[:2]) >= (5, 24)


def test_no_legacy_mapbox_api_in_app_sources():
    for path in (ROOT / "app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for legacy in ("scatter_mapbox", "density_mapbox", "choropleth_mapbox",
                       "mapbox_style", "Scattermapbox", "layout.mapbox"):
            assert legacy not in text, f"{legacy} found in {path}"
