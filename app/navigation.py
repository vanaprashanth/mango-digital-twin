"""
app/navigation.py

Grouped, state-managed sidebar navigation (Stage B).

Design:
  * One session_state key (``mt_page``) holds the selected page; it persists
    across ordinary reruns (forms, date filters, widgets) and is mirrored to
    the ``?page=`` query parameter so a browser refresh keeps the page.
  * Category groups are top-level st.expander blocks (never nested). The group
    containing the active page is open; the active page button is "primary".
  * Buttons use on_click callbacks, so a click sets the page before the rerun
    and the target page renders on that same rerun.
  * Page names are exactly the labels the app has always used; each maps to the
    unchanged render function in streamlit_app.py.
"""

from __future__ import annotations

import streamlit as st

PAGE_KEY = "mt_page"
QUERY_KEY = "page"
DEFAULT_PAGE = "Overview & Map"
DATA_SOURCES_PAGE = "Data Sources & Health"

# (group label, icon, pages). Order is display order.
NAV_GROUPS: list[tuple[str, str, list[str]]] = [
    ("Overview", "🏠", ["Overview & Map"]),
    ("Climate & Weather", "🌦️", ["Historical Risk", "Forecast Risk", "ET0 Validation"]),
    ("Orchard Intelligence", "🌳", ["Soil Intelligence", "Remote Sensing Health",
                                    "Combined Intelligence", "Mango Phenology"]),
    ("Water & Irrigation", "💧", ["Water Balance", "Phenology Water Balance",
                                  "FAO-56 Model Comparison", "FAO-56 Sensitivity Analysis",
                                  "Irrigation Advisory", "Irrigation Events", "Irrigation What-If"]),
    ("AI & Simulation", "🧠", ["AI/ML Advisory Preview", "What-if Simulator"]),
    ("Data & System", "🗄️", ["Raw Data", DATA_SOURCES_PAGE]),
]

PAGE_ICONS = {
    "Overview & Map": "🗺️", "Historical Risk": "📈", "Forecast Risk": "🔮", "ET0 Validation": "☀️",
    "Soil Intelligence": "🪨", "Remote Sensing Health": "🛰️", "Combined Intelligence": "🧩",
    "Mango Phenology": "🥭", "Water Balance": "🌊", "Phenology Water Balance": "🍃",
    "FAO-56 Model Comparison": "⚖️", "FAO-56 Sensitivity Analysis": "🎚️",
    "Irrigation Advisory": "🚿", "Irrigation Events": "📝", "Irrigation What-If": "🧪",
    "AI/ML Advisory Preview": "✨", "What-if Simulator": "🎛️", "Raw Data": "📄",
    DATA_SOURCES_PAGE: "📡",
}


def all_pages() -> list[str]:
    return [p for _, _, pages in NAV_GROUPS for p in pages]


def group_for_page(page: str) -> str | None:
    for group, _, pages in NAV_GROUPS:
        if page in pages:
            return group
    return None


def resolve_page(requested: str | None) -> str:
    """Return a valid page name; unknown/None falls back to the default."""
    return requested if requested in all_pages() else DEFAULT_PAGE


def _select(page: str) -> None:
    st.session_state[PAGE_KEY] = page
    try:
        st.query_params[QUERY_KEY] = page
    except Exception:   # query params unavailable in some contexts; state still works
        pass


def current_page() -> str:
    """Current page: session state first, then ?page=, then the default."""
    if PAGE_KEY not in st.session_state:
        try:
            requested = st.query_params.get(QUERY_KEY)
        except Exception:
            requested = None
        st.session_state[PAGE_KEY] = resolve_page(requested)
    else:
        st.session_state[PAGE_KEY] = resolve_page(st.session_state[PAGE_KEY])
    return st.session_state[PAGE_KEY]


def render_sidebar_navigation() -> str:
    """Render the grouped navigation in the sidebar and return the selected page."""
    page = current_page()
    active_group = group_for_page(page)

    for group, icon, pages in NAV_GROUPS:
        with st.sidebar.expander(f"{icon} {group}", expanded=(group == active_group)):
            for p in pages:
                st.button(
                    f"{PAGE_ICONS.get(p, '•')}  {p}",
                    key=f"nav_{p}",
                    type="primary" if p == page else "secondary",
                    use_container_width=True,
                    on_click=_select,
                    args=(p,),
                )
    return current_page()


def render_data_health_control() -> None:
    """Single, prominent sidebar control that opens the internal Data Sources & Health page."""
    st.sidebar.button(
        f"{PAGE_ICONS[DATA_SOURCES_PAGE]}  {DATA_SOURCES_PAGE}",
        key="nav_data_health_control",
        type="primary" if current_page() == DATA_SOURCES_PAGE else "secondary",
        use_container_width=True,
        on_click=_select,
        args=(DATA_SOURCES_PAGE,),
    )
