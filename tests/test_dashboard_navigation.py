"""
tests/test_dashboard_navigation.py

Navigation structure, routing, theme and page smoke tests (Streamlit AppTest).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import navigation as nav  # noqa: E402
from app.theme import PALETTE, kpi_card, status_pill  # noqa: E402

APP = PROJECT_ROOT / "app" / "streamlit_app.py"

EXPECTED_GROUPS = {
    "Overview": ["Overview & Map"],
    "Climate & Weather": ["Historical Risk", "Forecast Risk", "ET0 Validation"],
    "Orchard Intelligence": ["Soil Intelligence", "Remote Sensing Health", "Combined Intelligence",
                             "Mango Phenology"],
    "Water & Irrigation": ["Water Balance", "Phenology Water Balance", "FAO-56 Model Comparison",
                           "FAO-56 Sensitivity Analysis", "Irrigation Advisory", "Irrigation Events",
                           "Irrigation What-If"],
    "AI & Simulation": ["AI/ML Advisory Preview", "What-if Simulator"],
    "Data & System": ["Raw Data", "Data Sources & Health"],
}


# --- structure ---------------------------------------------------------------

def test_sidebar_category_structure():
    assert {g: p for g, _, p in nav.NAV_GROUPS} == EXPECTED_GROUPS
    assert [g for g, _, _ in nav.NAV_GROUPS] == list(EXPECTED_GROUPS)
    assert all(icon for _, icon, _ in nav.NAV_GROUPS)


def test_every_page_unique_and_has_icon():
    pages = nav.all_pages()
    assert len(pages) == len(set(pages)) == 19
    assert all(p in nav.PAGE_ICONS for p in pages)


def test_resolve_page_and_group_lookup():
    assert nav.resolve_page("Irrigation Events") == "Irrigation Events"
    assert nav.resolve_page("nonsense") == nav.DEFAULT_PAGE == "Overview & Map"
    assert nav.resolve_page(None) == nav.DEFAULT_PAGE
    assert nav.group_for_page("Water Balance") == "Water & Irrigation"
    assert nav.group_for_page("nope") is None


def test_every_destination_has_a_route_in_streamlit_app():
    src = APP.read_text(encoding="utf-8")
    routed = set(re.findall(r'page == "([^"]+)"', src))
    routed.add("Data Sources & Health" if "page == DATA_SOURCES_PAGE" in src else "")
    assert set(nav.all_pages()) <= routed


def test_no_radio_navigation_or_sidebar_source_list():
    src = APP.read_text(encoding="utf-8")
    assert "sidebar.radio" not in src
    assert "render_status_badge" not in src and "Data source status" not in src
    nav_src = (PROJECT_ROOT / "app" / "navigation.py").read_text(encoding="utf-8")
    assert "radio" not in nav_src


def test_no_nested_expanders_in_navigation():
    nav_src = (PROJECT_ROOT / "app" / "navigation.py").read_text(encoding="utf-8")
    assert nav_src.count("expander(") == 1       # one flat loop, buttons only inside


def test_theme_helpers_and_config():
    assert "#101A18" in (PROJECT_ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert "Fresh" in status_pill("Fresh") and PALETTE["green"] in status_pill("Fresh")
    assert "<script" not in kpi_card("<script>x</script>", "<b>")
    assert "Stale" in status_pill("Stale")


# --- AppTest: every page renders, clicks navigate, state persists ---------------

pytest.importorskip("streamlit.testing.v1")
from streamlit.testing.v1 import AppTest  # noqa: E402

pytestmark_data = pytest.mark.skipif(
    not (PROJECT_ROOT / "data" / "processed" / "muthukur_weather_risk_scores.csv").exists(),
    reason="processed data not available",
)


def _app() -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=90)
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def _click(at: AppTest, page: str) -> AppTest:
    [b for b in at.sidebar.button if b.key == f"nav_{page}"][0].click().run()
    return at


@pytestmark_data
def test_overview_renders_by_default():
    at = _app()
    assert at.session_state[nav.PAGE_KEY] == "Overview & Map"
    text = " ".join(m.value for m in at.markdown)
    assert "MangoTwin Intelligence" in text and "Sensor-Free Mango Orchard Digital Twin" in text
    assert "Muthukur / Peddapanjani" in text


@pytestmark_data
@pytest.mark.parametrize("page", nav.all_pages())
def test_click_navigates_and_page_renders(page):
    at = _click(_app(), page)
    assert at.session_state[nav.PAGE_KEY] == page
    assert not at.exception, [e.value for e in at.exception]
    active = [b for b in at.sidebar.button if b.key == f"nav_{page}"][0]
    assert active.proto.type == "primary"                 # highlighted
    others = [b for b in at.sidebar.button if b.key.startswith("nav_") and b.key != f"nav_{page}"
              and b.key != "nav_data_health_control"]
    assert all(b.proto.type == "secondary" for b in others)


@pytestmark_data
def test_data_sources_control_opens_internal_page():
    at = _app()
    [b for b in at.sidebar.button if b.key == "nav_data_health_control"][0].click().run()
    assert at.session_state[nav.PAGE_KEY] == "Data Sources & Health"
    assert not at.exception
    assert any("Data Sources &amp; Health" in m.value for m in at.markdown)


@pytestmark_data
def test_page_selection_persists_across_reruns():
    at = _click(_app(), "Irrigation Events")
    at.run()
    at.run()
    assert at.session_state[nav.PAGE_KEY] == "Irrigation Events"
    assert not at.exception


@pytestmark_data
def test_irrigation_form_widgets_preserve_page_state():
    """Interacting with widgets on the Irrigation Events page must not bounce navigation."""
    at = _click(_app(), "Irrigation Events")
    widgets = list(at.number_input) + list(at.date_input) + list(at.selectbox)
    assert widgets, "irrigation events page exposes input widgets"
    first = widgets[0]
    first.set_value(first.value).run()
    assert at.session_state[nav.PAGE_KEY] == "Irrigation Events"
    assert not at.exception


@pytestmark_data
def test_sidebar_has_no_source_status_list():
    at = _app()
    text = " ".join(m.value for m in at.sidebar.markdown) + " ".join(c.value for c in at.sidebar.caption)
    assert "NASA POWER (raw)" not in text and "Data source status" not in text
    assert not list(at.sidebar.radio)
