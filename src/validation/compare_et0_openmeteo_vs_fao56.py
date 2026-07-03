"""
Validation/comparison: Open-Meteo ET0 vs FAO-56 Penman-Monteith ET0.

WHAT THIS FILE DOES (and does NOT do)
  Compares two independent ET0 estimates for the same location on the same
  calendar days, where the dates overlap:

    Open-Meteo ET0 source:
      data/raw/muthukur_weather_open_meteo.csv
      Column: openmeteo_et0_mm  (Open-Meteo's own ET0 estimate, mm/day)

    FAO-56 Penman-Monteith ET0 source:
      data/processed/muthukur_fao56_water_balance.csv
      Column: et0_mm  (computed by this project's FAO-56 PM implementation
               applied to NASA POWER historical weather inputs)

  It writes:
      data/processed/muthukur_et0_openmeteo_fao56_comparison.csv
      data/processed/muthukur_et0_openmeteo_fao56_summary.md

  It does NOT modify any existing pipeline output, change any FAO-56 model
  logic, or call any external API.

WHAT THIS IS, AND WHAT IT IS NOT
  This is a SOURCE-TO-SOURCE COMPARISON, not a ground-truth validation.
  Both ET0 estimates are model-derived (Open-Meteo uses its own NWP-based
  ET0 calculation; this project uses the standard FAO-56 Penman-Monteith
  formula applied to NASA POWER inputs). Neither source has been validated
  against on-site lysimeter or eddy-covariance measurements.

  Differences can arise from:
    - Different input weather data (Open-Meteo NWP vs NASA POWER reanalysis)
    - Different ET0 formulations (Open-Meteo internally vs FAO-56 PM)
    - Different spatial resolution and temporal aggregation
    - Date-range mismatches (see "No overlapping dates" handling below)

NO-OVERLAP HANDLING
  Open-Meteo weather data is only fetched for recent/forecast dates; the
  FAO-56 water balance is built from NASA POWER historical weather. These
  date ranges may not overlap, especially if the Open-Meteo cache only holds
  forecast data (future dates) while the FAO-56 WB only holds historical
  dates.

  When there is no overlap, the script writes an empty comparison CSV and a
  summary markdown explaining the situation. It never raises in this case --
  this is an expected outcome, not an error.

HOW TO USE
  python src/validation/compare_et0_openmeteo_vs_fao56.py

  Or via the pipeline:
      python main.py --skip-fetch

INPUT
  data/raw/muthukur_weather_open_meteo.csv
  data/processed/muthukur_fao56_water_balance.csv

OUTPUT
  data/processed/muthukur_et0_openmeteo_fao56_comparison.csv
  data/processed/muthukur_et0_openmeteo_fao56_summary.md
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger(__name__)

config = get_config()

OPEN_METEO_CSV_PATH = config.path("open_meteo_csv")
FAO56_WB_CSV_PATH = config.path("fao56_water_balance_csv")
ET0_COMPARISON_CSV_PATH = config.path("et0_comparison_csv")
ET0_COMPARISON_SUMMARY_MD_PATH = config.path("et0_comparison_summary_md")

# Minimum rows needed to compute Pearson correlation (otherwise NaN).
_MIN_ROWS_FOR_CORRELATION = 3

_LIMITATIONS = """\
## Limitations

- **Source-to-source comparison only**: neither ET0 series has been
  validated against on-site lysimeter or eddy-covariance measurements.
- **Different input data**: Open-Meteo uses its own NWP weather model;
  this project's FAO-56 ET0 uses NASA POWER reanalysis weather.
- **Different formulations**: Open-Meteo publishes its own ET0 estimate;
  this project applies the standard FAO-56 Penman-Monteith formula
  independently. Both use the same reference crop definition, but input
  fields and computation details may differ.
- **Limited overlap window**: Open-Meteo data is only fetched for
  recent/forecast dates; NASA POWER data covers the historical period.
  Overlap may be zero or very small depending on when `python main.py`
  was last run.
- Differences < 0.5 mm/day are within normal inter-source variability
  for reference evapotranspiration and do not indicate an error.
"""


def _load_open_meteo(path: Path) -> pd.DataFrame | None:
    """Load Open-Meteo raw CSV; return None if missing or no ET0 column."""
    if not path.exists():
        log.warning("Open-Meteo raw CSV not found: %s", path)
        return None
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        log.warning("Could not read Open-Meteo CSV %s: %s", path, exc)
        return None

    if "openmeteo_et0_mm" not in df.columns:
        log.warning(
            "Open-Meteo CSV missing 'openmeteo_et0_mm' column "
            "(columns present: %s)", list(df.columns)
        )
        return None
    if "date" not in df.columns:
        log.warning("Open-Meteo CSV missing 'date' column")
        return None

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "openmeteo_et0_mm"])
    df = df[["date", "openmeteo_et0_mm"]].rename(
        columns={"openmeteo_et0_mm": "open_meteo_et0_mm_day"}
    )
    return df.sort_values("date").reset_index(drop=True)


def _load_fao56_wb(path: Path) -> pd.DataFrame | None:
    """Load FAO-56 water-balance CSV; return None if missing or no ET0 column."""
    if not path.exists():
        log.warning("FAO-56 water balance CSV not found: %s", path)
        return None
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        log.warning("Could not read FAO-56 WB CSV %s: %s", path, exc)
        return None

    if "et0_mm" not in df.columns:
        log.warning(
            "FAO-56 WB CSV missing 'et0_mm' column "
            "(columns present: %s)", list(df.columns)
        )
        return None
    if "date" not in df.columns:
        log.warning("FAO-56 WB CSV missing 'date' column")
        return None

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "et0_mm"])
    df = df[["date", "et0_mm"]].rename(columns={"et0_mm": "fao56_et0_mm_day"})
    return df.sort_values("date").reset_index(drop=True)


def _write_summary(
    path: Path,
    merged: pd.DataFrame,
    om_range: str,
    fao56_range: str,
    generated_at: str,
) -> None:
    """Write the markdown summary file."""
    n = len(merged)

    if n == 0:
        body = f"""\
# ET0 Comparison: Open-Meteo vs FAO-56 Penman-Monteith

*Generated: {generated_at}*

## Result: No overlapping dates

The Open-Meteo ET0 dataset covers **{om_range}** and the FAO-56 computed
ET0 dataset covers **{fao56_range}**. These date ranges do not overlap, so
no day-by-day comparison is possible with current cached data.

**What this means:** Open-Meteo data is fetched for recent and forecast
dates; the FAO-56 water balance is built from NASA POWER historical weather.
After a full `python main.py` run that fetches both sources and they cover
overlapping dates, this comparison will populate automatically.

{_LIMITATIONS}
"""
    else:
        mean_om = merged["open_meteo_et0_mm_day"].mean()
        mean_fao56 = merged["fao56_et0_mm_day"].mean()
        mean_diff = merged["difference_mm_day"].mean()
        mean_abs = merged["absolute_difference_mm_day"].mean()
        max_abs = merged["absolute_difference_mm_day"].max()
        date_min = merged["date"].min().strftime("%Y-%m-%d")
        date_max = merged["date"].max().strftime("%Y-%m-%d")

        corr_line = ""
        if n >= _MIN_ROWS_FOR_CORRELATION:
            corr = merged["open_meteo_et0_mm_day"].corr(merged["fao56_et0_mm_day"])
            corr_line = f"| Pearson correlation | {corr:.3f} |"

        body = f"""\
# ET0 Comparison: Open-Meteo vs FAO-56 Penman-Monteith

*Generated: {generated_at}*

## Summary

| Metric | Value |
|--------|-------|
| Matched days | {n} |
| Date range | {date_min} to {date_max} |
| Open-Meteo date coverage | {om_range} |
| FAO-56 date coverage | {fao56_range} |
| Mean Open-Meteo ET0 | {mean_om:.3f} mm/day |
| Mean FAO-56 ET0 | {mean_fao56:.3f} mm/day |
| Mean difference (Open-Meteo − FAO-56) | {mean_diff:.3f} mm/day |
| Mean absolute difference | {mean_abs:.3f} mm/day |
| Max absolute difference | {max_abs:.3f} mm/day |
{corr_line}

## Interpretation

A positive mean difference means Open-Meteo estimates higher ET0 than
FAO-56 Penman-Monteith (computed from NASA POWER weather) on average, and
vice versa. Differences < 0.5 mm/day are within normal inter-source
variability.

{_LIMITATIONS}
"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    log.info("Wrote ET0 comparison summary to %s", path)


def build_et0_comparison(
    open_meteo_path: Path | None = None,
    fao56_wb_path: Path | None = None,
    output_csv_path: Path | None = None,
    output_summary_path: Path | None = None,
) -> Path:
    """
    Build the Open-Meteo vs FAO-56 ET0 comparison CSV and markdown summary.

    Returns the path to the output CSV. Never raises — if inputs are missing
    or the date ranges don't overlap, writes an empty CSV and an explanatory
    summary markdown instead of crashing.

    Parameters (all optional; defaults come from config.yaml):
        open_meteo_path    — path to Open-Meteo raw CSV
        fao56_wb_path      — path to FAO-56 water balance CSV
        output_csv_path    — path for comparison output CSV
        output_summary_path — path for summary markdown
    """
    om_path = open_meteo_path or OPEN_METEO_CSV_PATH
    wb_path = fao56_wb_path or FAO56_WB_CSV_PATH
    csv_out = output_csv_path or ET0_COMPARISON_CSV_PATH
    md_out = output_summary_path or ET0_COMPARISON_SUMMARY_MD_PATH
    generated_at = dt.datetime.now().isoformat(timespec="seconds")

    om_df = _load_open_meteo(om_path)
    wb_df = _load_fao56_wb(wb_path)

    def _date_range_str(df: pd.DataFrame | None, label: str) -> str:
        if df is None or df.empty:
            return f"{label}: no data"
        return (
            f"{df['date'].min().strftime('%Y-%m-%d')} to "
            f"{df['date'].max().strftime('%Y-%m-%d')}"
        )

    om_range = _date_range_str(om_df, "Open-Meteo")
    fao56_range = _date_range_str(wb_df, "FAO-56")

    if om_df is None or wb_df is None:
        log.warning(
            "ET0 comparison skipped — one or both input sources unavailable "
            "(open_meteo=%s, fao56_wb=%s)",
            om_df is not None,
            wb_df is not None,
        )
        merged = pd.DataFrame(
            columns=[
                "date",
                "open_meteo_et0_mm_day",
                "fao56_et0_mm_day",
                "difference_mm_day",
                "absolute_difference_mm_day",
            ]
        )
        _write_summary(md_out, merged, om_range, fao56_range, generated_at)
        csv_out.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(csv_out, index=False)
        log.info("Wrote empty ET0 comparison CSV to %s", csv_out)
        return csv_out

    merged = pd.merge(
        om_df[["date", "open_meteo_et0_mm_day"]],
        wb_df[["date", "fao56_et0_mm_day"]],
        on="date",
        how="inner",
    )

    n = len(merged)
    log.info("ET0 comparison: %d overlapping dates (Open-Meteo %s, FAO-56 %s)", n, om_range, fao56_range)

    if n > 0:
        merged["difference_mm_day"] = (
            merged["open_meteo_et0_mm_day"] - merged["fao56_et0_mm_day"]
        ).round(4)
        merged["absolute_difference_mm_day"] = merged["difference_mm_day"].abs().round(4)
        merged["open_meteo_et0_mm_day"] = merged["open_meteo_et0_mm_day"].round(4)
        merged["fao56_et0_mm_day"] = merged["fao56_et0_mm_day"].round(4)
    else:
        merged["difference_mm_day"] = pd.Series(dtype=float)
        merged["absolute_difference_mm_day"] = pd.Series(dtype=float)

    csv_out.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(csv_out, index=False)
    log.info("Wrote ET0 comparison CSV (%d rows) to %s", n, csv_out)

    _write_summary(md_out, merged, om_range, fao56_range, generated_at)
    return csv_out


if __name__ == "__main__":
    out = build_et0_comparison()
    print(f"ET0 comparison complete. Output: {out}")
    summary = ET0_COMPARISON_SUMMARY_MD_PATH.read_text(encoding="utf-8")
    print(summary)
