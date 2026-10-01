from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from app.sections.freshness import show_freshness_indicator
from src.irrigation.load_irrigation_events import append_irrigation_event

_METHOD_OPTIONS = ["drip", "sprinkler", "flood", "manual", "other"]

_RERUN_PIPELINE_HINT = (
    "Run python main.py --skip-soil-fetch to apply irrigation events to the water balance."
)

_IMPACT_COLS = [
    "date",
    "irrigation_mm",
    "method",
    "source",
    "notes",
    "depletion_before_mm",
    "depletion_on_event_mm",
    "depletion_reduction_mm",
    "water_stress_level",
    "ks",
    "in_water_balance",
]


def build_irrigation_impact_table(
    irrigation_df: "pd.DataFrame | None",
    fao56_df: "pd.DataFrame | None",
) -> pd.DataFrame:
    """
    Join recorded irrigation events with FAO-56 (interpolated-Kc preferred)
    water balance output to show how each event affected root-zone
    depletion. Pure function — read-only, no Streamlit dependency, no file
    writes; safe to unit test directly.

    For each irrigation event (by date):
      - depletion_before_mm    : root_zone_depletion_mm on the prior
                                  calendar day (event date − 1), if that day
                                  exists in fao56_df, else NaN.
      - depletion_on_event_mm  : root_zone_depletion_mm on the event date
                                  itself, if present in fao56_df, else NaN.
      - depletion_reduction_mm : depletion_before_mm − depletion_on_event_mm,
                                  if both are available, else NaN.
      - water_stress_level     : from fao56_df on the event date, else None.
      - ks                     : from fao56_df on the event date, else NaN.
      - in_water_balance       : bool — True only if the event date itself
                                  is present in fao56_df (i.e. the pipeline
                                  has been rerun since this event was added).

    Returns an empty DataFrame (correct schema, zero rows) if
    `irrigation_df` is None or empty. Never raises — if `fao56_df` is None,
    empty, or missing expected columns, every row is returned with
    in_water_balance=False and the depletion/stress columns left as NaN/None.
    """
    if irrigation_df is None or irrigation_df.empty:
        return pd.DataFrame(columns=_IMPACT_COLS)

    events = irrigation_df.copy()
    events["date"] = pd.to_datetime(events["date"])

    fao56_lookup = None
    fao56_required = {"date", "root_zone_depletion_mm"}
    if (
        fao56_df is not None
        and not fao56_df.empty
        and fao56_required.issubset(set(fao56_df.columns))
    ):
        fao56_lookup = fao56_df.copy()
        fao56_lookup["date"] = pd.to_datetime(fao56_lookup["date"])
        fao56_lookup = fao56_lookup.set_index("date").sort_index()

    rows = []
    for _, ev in events.iterrows():
        ev_date = ev["date"]
        prior_date = ev_date - pd.Timedelta(days=1)

        depletion_before = float("nan")
        depletion_on_event = float("nan")
        stress_level = None
        ks_value = float("nan")
        in_balance = False

        if fao56_lookup is not None:
            if prior_date in fao56_lookup.index:
                depletion_before = float(fao56_lookup.loc[prior_date, "root_zone_depletion_mm"])
            if ev_date in fao56_lookup.index:
                in_balance = True
                depletion_on_event = float(fao56_lookup.loc[ev_date, "root_zone_depletion_mm"])
                if "water_stress_level" in fao56_lookup.columns:
                    stress_level = fao56_lookup.loc[ev_date, "water_stress_level"]
                if "ks" in fao56_lookup.columns:
                    ks_value = float(fao56_lookup.loc[ev_date, "ks"])

        if pd.notna(depletion_before) and pd.notna(depletion_on_event):
            depletion_reduction = depletion_before - depletion_on_event
        else:
            depletion_reduction = float("nan")

        rows.append(
            {
                "date": ev_date,
                "irrigation_mm": ev.get("irrigation_mm"),
                "method": ev.get("method", ""),
                "source": ev.get("source", ""),
                "notes": ev.get("notes", ""),
                "depletion_before_mm": depletion_before,
                "depletion_on_event_mm": depletion_on_event,
                "depletion_reduction_mm": depletion_reduction,
                "water_stress_level": stress_level,
                "ks": ks_value,
                "in_water_balance": in_balance,
            }
        )

    return pd.DataFrame(rows, columns=_IMPACT_COLS).sort_values("date").reset_index(drop=True)


def _render_persistence_status() -> None:
    """
    Show a small note about how irrigation events are currently persisted.

    Reads the configured mode via src.irrigation.persistence — this is a
    read-only status display, it does not write anything or contact any
    external service. If config/persistence cannot be loaded for any
    reason, this fails silently (the form itself must keep working
    regardless).
    """
    try:
        from src.irrigation.persistence import (
            get_github_persistence_settings,
            get_irrigation_persistence_mode,
            persistence_mode_label,
        )
        from src.utils.config import get_config

        _cfg = get_config()
        mode = get_irrigation_persistence_mode(_cfg)
        label = persistence_mode_label(mode)
        github_settings = get_github_persistence_settings(_cfg)
    except Exception:
        mode, label, github_settings = "local_csv", "Local CSV", {"enabled": False}

    st.caption(f"📌 Current persistence mode: **{label}**")

    if mode == "local_csv":
        st.warning(
            "⚠️ On Streamlit Cloud, local CSV writes may not persist after app "
            "restart unless GitHub-backed or database persistence is configured."
        )
    elif mode == "github_csv" and not github_settings.get("enabled"):
        st.warning(
            "⚠️ GitHub CSV persistence is selected but not fully configured "
            "(`GITHUB_TOKEN`/`GITHUB_REPO` missing). New events cannot be saved "
            "until this is fixed — the form will block saves rather than lose data."
        )


def _handle_local_save(
    csv_path: "Path | str",
    event_date,
    mm_value: float,
    method: str,
    notes: str,
) -> bool:
    """Save via the local CSV append path (unchanged local_csv behavior)."""
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


def _handle_github_save(
    event_date,
    mm_value: float,
    method: str,
    notes: str,
    github_settings: dict,
) -> bool:
    """
    Save via GitHub-backed persistence (github_csv mode). Only called when
    github_settings["enabled"] is True (mode selected AND repo/token present).

    Never displays the token. On any failure, no data is written locally or
    remotely for this submission — the user sees a clear error rather than
    silently losing the event.
    """
    try:
        from src.irrigation.github_persistence import append_irrigation_event_github
        from src.irrigation.persistence import get_github_token
        from src.utils.config import get_config

        token = get_github_token(get_config())
    except Exception as exc:
        st.error(f"Could not load GitHub persistence module: {type(exc).__name__}")
        return False

    if not token:
        # Shouldn't happen if github_settings["enabled"] is True, but guard anyway.
        st.warning(
            "⚠️ GitHub CSV persistence is selected but GITHUB_TOKEN/GITHUB_REPO "
            "is not configured. To avoid silently losing this event, the save "
            "has been blocked."
        )
        return False

    event = {
        "date": event_date,
        "irrigation_mm": mm_value,
        "method": method,
        "source": "user_dashboard",
        "notes": notes,
    }

    try:
        result = append_irrigation_event_github(
            repo=github_settings["repo"],
            branch=github_settings["branch"],
            token=token,
            csv_path=github_settings["csv_path"],
            event=event,
        )
    except ValueError as exc:
        st.error(f"Could not save irrigation event: {exc}")
        return False
    except Exception:
        st.error("Unexpected error while saving to GitHub. No data was written.")
        return False

    if result.get("success"):
        st.success(f"✅ {result.get('message', 'Saved to GitHub.')}")
        if result.get("commit_url"):
            st.markdown(f"[View commit on GitHub]({result['commit_url']})")
        st.info(
            "ℹ️ This event was committed to GitHub, not written to the local "
            "filesystem. The running dashboard may need a data reload or "
            "redeploy to reflect this new commit, and the FAO-56 water balance "
            "will not include it until the pipeline is rerun."
        )
        return True

    st.error(f"❌ GitHub save failed: {result.get('message', 'Unknown error.')}")
    st.caption("No data was written locally or to GitHub for this submission.")
    return False


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

    # ── Determine persistence mode ──────────────────────────────────────
    try:
        from src.irrigation.persistence import (
            get_github_persistence_settings,
            get_irrigation_persistence_mode,
        )
        from src.utils.config import get_config

        _cfg = get_config()
        mode = get_irrigation_persistence_mode(_cfg)
        github_settings = get_github_persistence_settings(_cfg)
    except Exception:
        mode, github_settings = "local_csv", {"enabled": False}

    # ── Write (append-only, single file — local CSV or GitHub commit) ───
    if mode == "github_csv":
        if github_settings.get("enabled"):
            return _handle_github_save(event_date, mm_value, method, notes, github_settings)

        st.warning(
            "⚠️ GitHub CSV persistence is selected but GITHUB_TOKEN/GITHUB_REPO "
            "is not configured. To avoid silently losing this event, the save "
            "has been blocked. Configure `GITHUB_TOKEN`, `GITHUB_REPO`, and "
            "optionally `GITHUB_BRANCH` as environment variables or Streamlit "
            "secrets, or set `irrigation_persistence_mode: \"local_csv\"` in "
            "`configs/config.yaml` to use local storage instead."
        )
        return False

    return _handle_local_save(csv_path, event_date, mm_value, method, notes)


def _render_impact_summary(
    irrigation_df: pd.DataFrame,
    fao56_df: "pd.DataFrame | None",
) -> None:
    """
    Render the "Irrigation Impact Summary" section: joins recorded
    irrigation events with the FAO-56 (interpolated-Kc preferred) water
    balance output to show how each event affected root-zone depletion.

    Read-only: only reads `irrigation_df` and `fao56_df` (already loaded by
    the caller); never writes any file.
    """
    st.subheader("Irrigation Impact Summary")
    st.caption(
        "How recorded irrigation events affected the FAO-56 root-zone depletion "
        "balance. Depletion before/after is read from the interpolated-Kc FAO-56 "
        "output where available."
    )

    impact_df = build_irrigation_impact_table(irrigation_df, fao56_df)

    if impact_df.empty:
        st.info("No irrigation events available to summarize impact for.")
        return

    total_events = len(impact_df)
    total_mm = float(impact_df["irrigation_mm"].sum())
    latest_row = impact_df.iloc[-1]
    latest_date_str = latest_row["date"].strftime("%Y-%m-%d")

    imp_col1, imp_col2, imp_col3, imp_col4 = st.columns(4)
    with imp_col1:
        st.metric("Total recorded events", total_events)
    with imp_col2:
        st.metric("Total irrigation applied", f"{total_mm:.1f} mm")
    with imp_col3:
        st.metric("Latest irrigation date", latest_date_str)
    with imp_col4:
        if latest_row["in_water_balance"] and pd.notna(latest_row["depletion_reduction_mm"]):
            st.metric(
                "Latest event impact",
                f"−{latest_row['depletion_reduction_mm']:.1f} mm depletion",
            )
        elif latest_row["in_water_balance"]:
            st.metric("Latest event impact", "No prior-day baseline")
        else:
            st.metric("Latest event impact", "Not yet in water balance")

    if not bool(impact_df["in_water_balance"].all()):
        st.warning(f"⚠️ {_RERUN_PIPELINE_HINT}")

    # ── Table: irrigation events joined with FAO-56 status ──────────────
    display_df = impact_df.copy()
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
    display_df["depletion_before_mm"] = display_df["depletion_before_mm"].map(
        lambda v: f"{v:.1f}" if pd.notna(v) else "—"
    )
    display_df["depletion_on_event_mm"] = display_df["depletion_on_event_mm"].map(
        lambda v: f"{v:.1f}" if pd.notna(v) else "—"
    )
    display_df["depletion_reduction_mm"] = display_df["depletion_reduction_mm"].map(
        lambda v: f"{v:.1f}" if pd.notna(v) else "—"
    )
    display_df["ks"] = display_df["ks"].map(lambda v: f"{v:.3f}" if pd.notna(v) else "—")
    display_df["water_stress_level"] = display_df["water_stress_level"].fillna("—")
    display_df["in_water_balance"] = display_df["in_water_balance"].map(
        lambda v: "✅ Yes" if v else "⏳ Not yet"
    )
    display_df = display_df.rename(
        columns={
            "date": "Date",
            "irrigation_mm": "Irrigation (mm)",
            "method": "Method",
            "source": "Source",
            "notes": "Notes",
            "depletion_before_mm": "Depletion before (mm)",
            "depletion_on_event_mm": "Depletion on event date (mm)",
            "depletion_reduction_mm": "Depletion reduction (mm)",
            "water_stress_level": "Stress level on event date",
            "ks": "Ks on event date",
            "in_water_balance": "In water balance?",
        }
    )
    st.dataframe(display_df, use_container_width=True)

    # ── Chart: irrigation_mm vs root_zone_depletion_mm ───────────────────
    if (
        fao56_df is not None
        and not fao56_df.empty
        and {"date", "root_zone_depletion_mm"}.issubset(set(fao56_df.columns))
    ):
        chart_fao56 = fao56_df.copy()
        chart_fao56["date"] = pd.to_datetime(chart_fao56["date"])
        chart_fao56 = chart_fao56.sort_values("date")

        impact_fig = go.Figure()
        impact_fig.add_trace(
            go.Scatter(
                x=chart_fao56["date"],
                y=chart_fao56["root_zone_depletion_mm"],
                mode="lines",
                name="Root-zone depletion (mm)",
                line=dict(color="#636EFA", width=2),
                yaxis="y1",
            )
        )
        impact_fig.add_trace(
            go.Bar(
                x=impact_df["date"],
                y=impact_df["irrigation_mm"],
                name="Irrigation applied (mm)",
                marker_color="steelblue",
                opacity=0.7,
                yaxis="y2",
            )
        )
        impact_fig.update_layout(
            title="Irrigation Events vs Root-Zone Depletion",
            xaxis_title="Date",
            yaxis=dict(title="Root-zone depletion (mm)"),
            yaxis2=dict(title="Irrigation (mm)", overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=420,
        )
        st.plotly_chart(impact_fig, use_container_width=True)
    else:
        st.caption(
            "FAO-56 water balance output not available — cannot chart depletion "
            "alongside irrigation events."
        )

    st.caption(
        "\"Depletion before\" is the FAO-56 root-zone depletion on the day "
        "before the event; \"Depletion on event date\" includes that day's "
        "irrigation, rainfall, and crop water use (FAO-56 eq 85). Events not "
        "yet reflected in the FAO-56 output show as \"⏳ Not yet\" — rerun the "
        "pipeline to include them."
    )


def render_irrigation_events_page(
    irrigation_df: pd.DataFrame | None,
    csv_path: "Path | str | None" = None,
    fao56_df: "pd.DataFrame | None" = None,
) -> None:
    """Render the Irrigation Events dashboard page: add-event form + read-only summary."""

    st.title("Irrigation Events")
    show_freshness_indicator(label="Irrigation events", staleness_warning_days=0)
    _render_persistence_status()

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

    # ── Irrigation Impact Summary ────────────────────────────────────────
    _render_impact_summary(irrigation_df, fao56_df)

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
