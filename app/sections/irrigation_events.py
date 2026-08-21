from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from app.sections.freshness import show_freshness_indicator
from src.irrigation.load_irrigation_events import append_irrigation_event

_METHOD_OPTIONS = ["drip", "sprinkler", "flood", "manual", "other"]


def _render_add_event_form(csv_path: "Path | str") -> bool:
    """
    Render the "Add Irrigation Event" form and handle submission.

    Writes ONLY to `csv_path` (expected to be
    data/manual/muthukur_irrigation_events.csv) via append_irrigation_event.
    Never touches data/raw, data/processed, or any other file.

    Returns True if an event was successfully saved this run (so the caller
    can refresh/reload the irrigation events data), False otherwise.
    """
    st.subheader("Record a New Irrigation Event")

    with st.form("add_irrigation_event_form", clear_on_submit=True):
        form_col1, form_col2, form_col3 = st.columns(3)

        with form_col1:
            event_date = st.date_input(
                "Date",
                value=dt.date.today(),
                help="Date the irrigation was applied.",
            )

        with form_col2:
            irrigation_mm = st.number_input(
                "Irrigation amount (mm)",
                min_value=0.0,
                max_value=500.0,
                value=20.0,
                step=5.0,
                help="Amount of water applied, in mm. Must be zero or greater.",
            )

        with form_col3:
            method = st.selectbox(
                "Method",
                options=_METHOD_OPTIONS,
                index=0,
                help="How the irrigation was applied.",
            )

        notes = st.text_area(
            "Notes (optional)",
            value="",
            max_chars=300,
            help="Any additional context about this irrigation event.",
        )

        submitted = st.form_submit_button("Save irrigation event")

    if not submitted:
        return False

    # ── Validation ───────────────────────────────────────────────────────
    if event_date is None:
        st.error("A valid date is required.")
        return False

    try:
        mm_value = float(irrigation_mm)
    except (TypeError, ValueError):
        st.error("Irrigation amount must be numeric.")
        return False

    if mm_value < 0:
        st.error("Irrigation amount must be zero or greater.")
        return False

    # ── Write (append-only, single file) ────────────────────────────────
    try:
        append_irrigation_event(
            path=csv_path,
            date=event_date,
            irrigation_mm=mm_value,
            method=method,
            source="user_dashboard",
            notes=notes,
        )
    except ValueError as exc:
        st.error(f"Could not save irrigation event: {exc}")
        return False
    except Exception as exc:
        st.error(f"Unexpected error saving irrigation event: {exc}")
        return False

    st.success(
        f"✅ Saved irrigation event: {event_date.strftime('%Y-%m-%d')}, "
        f"{mm_value:.1f} mm ({method})."
    )
    st.warning(
        "⚠️ This records the irrigation event only. The FAO-56 water balance and "
        "irrigation advisory will **not** reflect it until the pipeline is rerun "
        "(`python main.py --skip-fetch`)."
    )
    st.caption(
        "This records the irrigation event. It does not automatically recompute "
        "the water balance until the pipeline is rerun."
    )
    return True


def render_irrigation_events_page(
    irrigation_df: pd.DataFrame | None,
    csv_path: "Path | str | None" = None,
) -> None:
    """Render the Irrigation Events dashboard page: add-event form + read-only summary."""

    st.title("Irrigation Events")
    show_freshness_indicator(label="Irrigation events", staleness_warning_days=0)

    if csv_path is not None:
        saved = _render_add_event_form(csv_path)
        if saved:
            # Reload so the summary/table/chart below reflect the new event
            # immediately, without requiring a manual page refresh.
            from src.irrigation.load_irrigation_events import load_irrigation_events

            irrigation_df = load_irrigation_events(csv_path)
            if irrigation_df.empty:
                irrigation_df = None
        st.divider()
    else:
        st.info(
            "Adding events from this page is unavailable right now (CSV path not "
            "configured). You can still edit the CSV file directly:\n\n"
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
        "reducing root-zone depletion on recorded event days. This records the "
        "irrigation event. It does not automatically recompute the water balance "
        "until the pipeline is rerun."
    )
