from __future__ import annotations

import datetime as dt

import pandas as pd
import plotly.express as px
import streamlit as st
from app.sections.freshness import show_freshness_indicator


def render_irrigation_events_page(irrigation_df: pd.DataFrame | None) -> None:
    """Render the Irrigation Events read-only dashboard page."""

    st.title("Irrigation Events")
    show_freshness_indicator(label="Irrigation events", staleness_warning_days=0)

    st.info(
        "This page is **read-only**. To record irrigation events, edit the CSV file directly:\n\n"
        "`data/manual/muthukur_irrigation_events.csv`\n\n"
        "Columns: `date` (YYYY-MM-DD), `irrigation_mm` (mm applied), "
        "`method` (optional), `source` (optional), `notes` (optional).\n\n"
        "After editing, re-run `python main.py --skip-fetch` to update the FAO-56 "
        "water balance and irrigation advisory."
    )

    if irrigation_df is None or irrigation_df.empty:
        st.warning("No irrigation events recorded yet.")
        st.caption(
            "The irrigation events CSV exists but is header-only, or no valid rows were found. "
            "Add rows to `data/manual/muthukur_irrigation_events.csv` to track irrigation."
        )
        st.divider()
        st.subheader("CSV Format")
        example = pd.DataFrame(
            [
                {
                    "date": "2025-03-15",
                    "irrigation_mm": 25.0,
                    "method": "drip",
                    "source": "farmer",
                    "notes": "pre-flowering soil moisture top-up",
                },
                {
                    "date": "2025-04-02",
                    "irrigation_mm": 30.0,
                    "method": "flood",
                    "source": "farmer",
                    "notes": "fruit set stage irrigation",
                },
            ]
        )
        st.caption("Example rows (not real data):")
        st.dataframe(example, use_container_width=True)
        return

    today = dt.date.today()

    # ── Summary metrics ────────────────────────────────────────────────────
    st.subheader("Summary")

    total_events = len(irrigation_df)
    total_mm = float(irrigation_df["irrigation_mm"].sum())
    latest_date = irrigation_df["date"].max()
    latest_date_str = (
        latest_date.strftime("%Y-%m-%d")
        if hasattr(latest_date, "strftime")
        else str(latest_date)
    )
    try:
        days_since = (today - pd.to_datetime(latest_date).date()).days
        days_since_str = f"{days_since} day(s) ago"
    except Exception:
        days_since_str = "N/A"

    met_col1, met_col2, met_col3, met_col4 = st.columns(4)
    with met_col1:
        st.metric("Total events", total_events)
    with met_col2:
        st.metric("Total irrigation applied", f"{total_mm:.1f} mm")
    with met_col3:
        st.metric("Latest event", latest_date_str)
    with met_col4:
        st.metric("Days since last event", days_since_str)

    if total_events > 0:
        mean_mm = total_mm / total_events
        st.caption(f"Mean per event: {mean_mm:.1f} mm")

    st.divider()

    # ── Bar chart ──────────────────────────────────────────────────────────
    st.subheader("Irrigation Over Time")

    chart_df = irrigation_df.copy()
    chart_df["date_str"] = chart_df["date"].dt.strftime("%Y-%m-%d")

    irr_fig = px.bar(
        chart_df,
        x="date",
        y="irrigation_mm",
        title="Recorded Irrigation Events",
        labels={"date": "Date", "irrigation_mm": "Irrigation applied (mm)"},
        hover_data={"date_str": True, "irrigation_mm": ":.1f", "method": True, "notes": True},
    )
    irr_fig.update_traces(marker_color="steelblue")
    irr_fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Irrigation (mm)",
    )
    st.plotly_chart(irr_fig, use_container_width=True)

    st.divider()

    # ── Data table ─────────────────────────────────────────────────────────
    st.subheader("Irrigation Event Log")

    with st.expander("All recorded irrigation events", expanded=True):
        display_df = irrigation_df.copy()
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
        display_df = display_df.rename(
            columns={
                "date": "Date",
                "irrigation_mm": "Irrigation (mm)",
                "method": "Method",
                "source": "Source",
                "notes": "Notes",
            }
        )
        st.dataframe(display_df, use_container_width=True)

    st.divider()

    # ── Disclaimer ─────────────────────────────────────────────────────────
    st.caption(
        "Irrigation events are manually recorded and not validated against any "
        "field meter or flow measurement. Each row represents the best available "
        "estimate of water applied on that date. The FAO-56 water balance treats "
        "irrigation as an additive input alongside rainfall (FAO-56 eq 85), "
        "reducing root-zone depletion on recorded event days."
    )
