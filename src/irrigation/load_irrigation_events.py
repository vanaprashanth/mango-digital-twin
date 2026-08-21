"""
src/irrigation/load_irrigation_events.py

Load and validate manually recorded irrigation events from a CSV file.

The irrigation events CSV lives at:
    data/manual/muthukur_irrigation_events.csv

Expected columns:
    date          — ISO-8601 date (YYYY-MM-DD) when irrigation was applied
    irrigation_mm — Amount of irrigation water applied in mm (must be > 0)
    method        — Optional: how it was applied (e.g. drip, flood, sprinkler)
    source        — Optional: who recorded it (e.g. farmer, observer)
    notes         — Optional: free-text notes about the event

This module is imported by the three FAO-56 water balance scripts and the
irrigation advisory. It is kept intentionally simple and dependency-light
(only pandas, no project-specific imports) so tests can run standalone.

BEHAVIOUR GUARANTEES
  - Missing file        → returns empty DataFrame with correct schema
  - Header-only file    → returns empty DataFrame with correct schema
  - Invalid date rows   → silently dropped
  - Non-numeric irrigation_mm → silently dropped
  - Negative or zero irrigation_mm → silently dropped
  - Duplicate dates     → aggregated: sum irrigation_mm; join unique text for
                          method / source / notes with "; "
  - Never raises        → callers can rely on always getting a DataFrame back
"""

from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

import pandas as pd

_SCHEMA_COLS = ["date", "irrigation_mm", "method", "source", "notes"]
_TEXT_COLS = ["method", "source", "notes"]


def _empty_df() -> pd.DataFrame:
    """Return a correctly typed empty irrigation events DataFrame."""
    df = pd.DataFrame(columns=_SCHEMA_COLS)
    df["date"] = pd.to_datetime(df["date"])
    df["irrigation_mm"] = df["irrigation_mm"].astype(float)
    for col in _TEXT_COLS:
        df[col] = df[col].astype(str)
    return df


def _join_unique(series: pd.Series) -> str:
    """Join unique non-empty string values from a Series with '; '."""
    seen: list[str] = []
    for val in series.values:
        s = str(val).strip() if val is not None else ""
        if s and s != "nan" and s not in seen:
            seen.append(s)
    return "; ".join(seen)


def load_irrigation_events(path: "Path | str") -> pd.DataFrame:
    """
    Load and validate irrigation events from a CSV file.

    Parameters
    ----------
    path : Path or str
        Path to the irrigation events CSV.

    Returns
    -------
    pd.DataFrame
        Cleaned, aggregated, date-sorted DataFrame with columns:
          date (datetime64[ns]), irrigation_mm (float64),
          method (str), source (str), notes (str)

        Returns an empty DataFrame (correct schema, zero rows) when the file
        is missing, empty, or has no valid rows after cleaning.
    """
    path = Path(path)
    if not path.exists():
        return _empty_df()

    try:
        df = pd.read_csv(path)
    except Exception:
        return _empty_df()

    if df.empty:
        return _empty_df()

    # Ensure all expected columns are present; add missing ones as empty
    for col in _SCHEMA_COLS:
        if col not in df.columns:
            df[col] = "" if col in _TEXT_COLS else None

    # Parse dates — rows where the date cannot be parsed are dropped
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    if df.empty:
        return _empty_df()

    # Parse and validate irrigation_mm — must be numeric and strictly positive
    df["irrigation_mm"] = pd.to_numeric(df["irrigation_mm"], errors="coerce")
    df = df.dropna(subset=["irrigation_mm"])
    df = df[df["irrigation_mm"] > 0].copy()
    if df.empty:
        return _empty_df()

    # Clean text columns: fill NaN, convert to str, strip whitespace
    for col in _TEXT_COLS:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # Aggregate duplicate dates: sum mm, join unique text values
    df = (
        df.groupby("date", as_index=False)
        .agg(
            irrigation_mm=("irrigation_mm", "sum"),
            method=("method", _join_unique),
            source=("source", _join_unique),
            notes=("notes", _join_unique),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    return df


def validate_new_event(
    date: "dt.date | dt.datetime | str",
    irrigation_mm: float,
) -> "tuple[pd.Timestamp, float]":
    """
    Shared validation for a single new irrigation event, used by both the
    local CSV append path (append_irrigation_event, below) and the optional
    GitHub-backed writeback path (src/irrigation/github_persistence.py), so
    both persistence modes reject the same invalid input in the same way.

    Validation
    ----------
    - `date` must be a valid date (a `date`/`datetime` object, or a string
      parseable by `pd.to_datetime`).
    - `irrigation_mm` must be numeric and >= 0.

    Returns
    -------
    (parsed_date, mm_value) : (pd.Timestamp, float)

    Raises
    ------
    ValueError
        If `date` cannot be parsed, or `irrigation_mm` is not numeric or is
        negative.
    """
    try:
        parsed_date = pd.to_datetime(date)
        if pd.isna(parsed_date):
            raise ValueError
    except Exception as exc:
        raise ValueError(f"Invalid date: {date!r}") from exc

    try:
        mm_value = float(irrigation_mm)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"irrigation_mm must be numeric, got {irrigation_mm!r}") from exc
    if mm_value < 0:
        raise ValueError(f"irrigation_mm must be >= 0, got {mm_value}")

    return parsed_date, mm_value


def append_irrigation_event(
    path: "Path | str",
    date: "dt.date | dt.datetime | str",
    irrigation_mm: float,
    method: str = "",
    source: str = "",
    notes: str = "",
) -> None:
    """
    Append a single irrigation event row to the CSV at `path`.

    This is the only supported write path for the irrigation events CSV.
    It is intentionally narrow in scope:
      - Writes ONLY to the given path (callers must pass
        data/manual/muthukur_irrigation_events.csv — this function does not
        know or care about any other project file).
      - Creates the file with the correct header if it does not exist yet.
      - Appends a single row without reading, rewriting, or reordering any
        existing rows — existing data can never be corrupted by a call here.

    Validation
    ----------
    - `irrigation_mm` must be numeric and >= 0. Raises ValueError otherwise.
    - `date` must be a valid date (a `date`/`datetime` object, or a string
      parseable by `pd.to_datetime`). Raises ValueError otherwise.

    Parameters
    ----------
    path : Path or str
        Path to the irrigation events CSV.
    date : date, datetime, or str
        Date the irrigation was applied.
    irrigation_mm : float
        Amount of irrigation water applied, in mm. Must be >= 0.
    method : str, optional
        Irrigation method (e.g. "drip", "sprinkler", "flood", "manual", "other").
    source : str, optional
        Who/what recorded this event (e.g. "user_dashboard").
    notes : str, optional
        Free-text notes.

    Raises
    ------
    ValueError
        If `date` cannot be parsed, or `irrigation_mm` is not numeric or is
        negative.
    """
    parsed_date, mm_value = validate_new_event(date, irrigation_mm)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = path.exists() and path.stat().st_size > 0

    # Guard against a missing trailing newline on the existing file (e.g. a
    # hand-edited CSV) — without this, the new row would be concatenated
    # onto the last existing line instead of appended as its own row.
    if file_exists:
        with path.open("rb") as f:
            f.seek(-1, 2)
            last_byte = f.read(1)
        if last_byte != b"\n":
            with path.open("a", encoding="utf-8") as f:
                f.write("\n")

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(_SCHEMA_COLS)
        writer.writerow(
            [
                parsed_date.strftime("%Y-%m-%d"),
                mm_value,
                str(method).strip(),
                str(source).strip(),
                str(notes).strip(),
            ]
        )


def validate_irrigation_events(df: pd.DataFrame) -> list[str]:
    """
    Optional post-load validation: return human-readable warnings for the
    caller (e.g. for display in the dashboard or test assertions).

    Returns an empty list if no issues are found.
    """
    warnings: list[str] = []

    if df.empty:
        return warnings

    if "irrigation_mm" in df.columns:
        high_mask = df["irrigation_mm"] > 200
        if high_mask.any():
            dates = df.loc[high_mask, "date"].dt.strftime("%Y-%m-%d").tolist()
            warnings.append(
                f"Unusually high irrigation_mm (>200 mm) on: {', '.join(dates)}. "
                "Please verify these values are correct."
            )

    if "date" in df.columns:
        today = pd.Timestamp.today().normalize()
        future_mask = df["date"] > today
        if future_mask.any():
            dates = df.loc[future_mask, "date"].dt.strftime("%Y-%m-%d").tolist()
            warnings.append(
                f"Future irrigation dates found: {', '.join(dates)}. "
                "Verify these are intentional."
            )

    return warnings
