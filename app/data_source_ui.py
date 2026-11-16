"""
Streamlit glue for the optional GCS snapshot data source.

Local files remain the default. Logic lives in ``src/cloud/data_source_manager.py`` (no Streamlit
dependency); this module only holds the process-wide manager and renders the status panel.

In local mode (``MANGOTWIN_DATA_SOURCE`` unset or ``local``, which is what the Streamlit Community
Cloud deployment uses) this adds ONE sidebar caption and nothing else: no network, no credentials,
no cache directory, and the GCS libraries are never imported.
"""

from __future__ import annotations

import streamlit as st

from src.cloud.data_source_manager import (
    INTEGRITY_NOTE,
    DataSourceManager,
    ResolvedSource,
    provenance_rows,
)

# One manager per server process, shared by all sessions: the refresh interval therefore applies
# per process, not per browser tab or rerun.
_MANAGER = DataSourceManager()


def resolve_dashboard_source() -> ResolvedSource:
    """Call ONCE per script run (before any dataset path is built) and keep the result."""
    return _MANAGER.get()


def render_data_source_notices(resolved: ResolvedSource) -> None:
    """Main-area warnings that the user must not miss (fallback, stale snapshot, differing local inputs)."""
    for notice in resolved.notices:
        if notice.prominent:
            st.warning(notice.text)


def render_data_source_panel(resolved: ResolvedSource) -> None:
    """Sidebar status: a caption in local mode; a provenance panel in snapshot mode."""
    if resolved.mode == "local":
        st.sidebar.caption("Data source: local files")
        return
    label = "GCS snapshot" if resolved.is_snapshot else "local files (fallback)"
    with st.sidebar.expander(f"Data source: {label}", expanded=not resolved.is_snapshot or not resolved.refresh_ok):
        st.markdown("\n".join(f"**{k}:** {v}" for k, v in provenance_rows(resolved)))
        if resolved.is_snapshot:
            st.caption(INTEGRITY_NOTE)
        for notice in resolved.notices:
            (st.warning if notice.level == "warning" else st.info)(notice.text)
