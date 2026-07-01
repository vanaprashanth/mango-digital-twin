"""
src/advisory/forecast_aware_irrigation.py

Standalone Forecast-Aware Irrigation Advisory for the Muthukur mango orchard.

Combines:
  - Phenology-aware FAO-56 water stress status (latest available row)
  - Open-Meteo forecast rainfall (daily resolution)
  - Mango crop stage and critical-period sensitivity

Decision logic:
  - High stress + rain >= 5 mm in next 24h   → Delay irrigation and recheck after rainfall
  - High stress + rain < 2 mm in next 24h    → Irrigate now or apply partial irrigation
  - High stress + rain 2–5 mm, critical stage → Apply partial irrigation and recheck
  - High stress + rain 2–5 mm, other stage   → Delay irrigation and recheck after rainfall
  - Medium stress + rain >= 2 mm in 24h      → Wait and monitor
  - Medium stress + rain < 2 mm in 24h       → Monitor closely; consider irrigation soon
  - Low stress (any forecast)                → No irrigation needed now
  - Forecast unavailable                     → Use FAO-56 advisory only

NOTE: Only daily forecast data is available from Open-Meteo in this project.
      6-hour and 12-hour rain amounts cannot be computed; thresholds are
      applied to the next-24-hour (i.e. next-day) rainfall total.
      Rain probability is not available in the current Open-Meteo daily output.

Output CSV:
  data/processed/muthukur_forecast_aware_irrigation_advisory.csv

Usage:
    python src/advisory/forecast_aware_irrigation.py
"""

from __future__ import annotations

import sys
from datetime import datetime, date
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so src.* imports work when called
# directly (e.g. python src/advisory/forecast_aware_irrigation.py).
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_config  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

log = get_logger(__name__)
config = get_config()

# ---------------------------------------------------------------------------
# Paths (all resolved from config.yaml so only one place to change)
# ---------------------------------------------------------------------------
FAO56_PHENOLOGY_WB_PATH = config.path("fao56_phenology_water_balance_csv")
FORECAST_RISK_PATH = config.path("forecast_risk_csv")
ADVISORY_OUTPUT_PATH = config.path("forecast_aware_irrigation_advisory_csv")

# ---------------------------------------------------------------------------
# Decision thresholds
# ---------------------------------------------------------------------------
# Rain in next 24 h that is large enough to fully meet crop demand → delay
RAIN_DELAY_THRESHOLD_MM: float = 5.0
# Rain in next 24 h that is non-negligible but uncertain → partial action
RAIN_PARTIAL_THRESHOLD_MM: float = 2.0
# Mango stages where moisture deficit is most damaging (spec §"Fruit set…")
CRITICAL_STAGES: frozenset[str] = frozenset({"Fruit set", "Fruit development"})


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def _load_phenology_water_balance(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def _load_forecast(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Forecast rain summary
# ---------------------------------------------------------------------------

def _build_forecast_rain_summary(forecast_df: pd.DataFrame, today: date) -> dict:
    """
    Derive near-term rainfall metrics from the daily forecast.

    Since only daily data is available:
      - rain_next_6h_mm  = None (hourly data required; not available)
      - rain_next_12h_mm = None (hourly data required; not available)
      - rain_next_24h_mm = rainfall on the first forecast day >= today
      - rain_probability_next_24h = None (not in Open-Meteo daily output)

    Returns a dict with those keys plus ``forecast_available`` (bool).
    """
    future = forecast_df[forecast_df["date"].dt.date >= today].copy()

    if future.empty:
        log.warning("No forecast rows found for dates >= %s.", today)
        return {
            "forecast_resolution": "daily",
            "rain_next_6h_mm": None,
            "rain_next_12h_mm": None,
            "rain_next_24h_mm": None,
            "rain_probability_next_24h": None,
            "forecast_available": False,
        }

    # Prefer rainfall_mm (rain only) over precipitation_mm (may include snow)
    rain_col = "rainfall_mm" if "rainfall_mm" in future.columns else "precipitation_mm"
    first_day_rain = float(future.iloc[0][rain_col])

    log.info(
        "Forecast: first available date=%s, %s=%.1f mm (resolution=daily).",
        future.iloc[0]["date"].date(),
        rain_col,
        first_day_rain,
    )

    return {
        "forecast_resolution": "daily",
        "rain_next_6h_mm": None,
        "rain_next_12h_mm": None,
        "rain_next_24h_mm": first_day_rain,
        "rain_probability_next_24h": None,
        "forecast_available": True,
    }


# ---------------------------------------------------------------------------
# Advisory decision engine
# ---------------------------------------------------------------------------

def _decide_advisory(
    stress_level: str,
    mango_stage: str,
    ks: float,
    rain_next_24h: float | None,
    forecast_available: bool,
) -> tuple[str, str, str]:
    """
    Apply the decision rules and return (advisory_action, advisory_priority, advisory_reason).

    Priority values: "High" | "Medium" | "Low"
    """
    # ── No forecast data ──────────────────────────────────────────────────
    if not forecast_available:
        if stress_level == "High":
            return (
                "Irrigate now or apply partial irrigation",
                "High",
                (
                    f"High water stress (Ks={ks:.3f}) and forecast data is unavailable. "
                    "Using FAO-56 advisory only: irrigation is recommended."
                ),
            )
        if stress_level == "Medium":
            return (
                "Monitor closely; forecast unavailable",
                "Medium",
                (
                    f"Moderate water stress (Ks={ks:.3f}) and forecast data is unavailable. "
                    "Monitor crop closely; irrigate if stress increases."
                ),
            )
        return (
            "No irrigation needed now",
            "Low",
            (
                f"Water stress is low (Ks={ks:.3f}) and forecast data is unavailable. "
                "No immediate action required."
            ),
        )

    # ── Forecast available ────────────────────────────────────────────────
    rain = rain_next_24h if rain_next_24h is not None else 0.0

    # Low stress — always safe to hold off regardless of rain
    if stress_level == "Low":
        return (
            "No irrigation needed now",
            "Low",
            (
                f"Water stress is low (Ks={ks:.3f}). "
                f"Forecast shows {rain:.1f} mm rain in the next 24 hours. "
                "No irrigation needed."
            ),
        )

    # Medium stress
    if stress_level == "Medium":
        if rain >= RAIN_PARTIAL_THRESHOLD_MM:
            return (
                "Wait and monitor",
                "Low",
                (
                    f"Moderate water stress (Ks={ks:.3f}) with {rain:.1f} mm rain forecast "
                    "in the next 24 hours. Wait for rainfall and reassess depletion afterwards."
                ),
            )
        return (
            "Monitor closely; consider irrigation soon",
            "Medium",
            (
                f"Moderate water stress (Ks={ks:.3f}) with low forecast rain ({rain:.1f} mm in 24 hours). "
                "Monitor root-zone depletion daily; irrigation may be needed within 1–2 days."
            ),
        )

    # High stress
    if rain >= RAIN_DELAY_THRESHOLD_MM:
        return (
            "Delay irrigation and recheck after rainfall",
            "Medium",
            (
                f"High water stress (Ks={ks:.3f}) but {rain:.1f} mm rain is forecast "
                f"within 24 hours (≥ {RAIN_DELAY_THRESHOLD_MM:.0f} mm threshold). "
                "Delay irrigation and reassess after rainfall."
            ),
        )

    if RAIN_PARTIAL_THRESHOLD_MM <= rain < RAIN_DELAY_THRESHOLD_MM:
        # Uncertain rain — distinguish critical vs non-critical stages
        if mango_stage in CRITICAL_STAGES:
            return (
                "Apply partial irrigation and recheck after forecast update",
                "High",
                (
                    f"High water stress (Ks={ks:.3f}) during a critical crop stage ({mango_stage}). "
                    f"Forecast rain is uncertain ({rain:.1f} mm; between "
                    f"{RAIN_PARTIAL_THRESHOLD_MM:.0f}–{RAIN_DELAY_THRESHOLD_MM:.0f} mm). "
                    "Apply partial irrigation now and reassess after the next forecast update."
                ),
            )
        return (
            "Delay irrigation and recheck after rainfall",
            "Medium",
            (
                f"High water stress (Ks={ks:.3f}) with moderate forecast rain ({rain:.1f} mm). "
                "Delay irrigation and reassess after rainfall."
            ),
        )

    # rain < RAIN_PARTIAL_THRESHOLD_MM — effectively no useful rain expected
    return (
        "Irrigate now or apply partial irrigation",
        "High",
        (
            f"High water stress (Ks={ks:.3f}) with very low forecast rain "
            f"({rain:.1f} mm in the next 24 hours, below {RAIN_PARTIAL_THRESHOLD_MM:.0f} mm threshold). "
            "Immediate irrigation is recommended."
        ),
    )


# ---------------------------------------------------------------------------
# Advisory limitations text
# ---------------------------------------------------------------------------

def _build_limitations(
    fao56_date: date,
    today: date,
    forecast_available: bool,
    forecast_resolution: str,
) -> str:
    parts = [
        "FAO-56 water-balance model is not locally calibrated; Kc values are assumed for this region and cultivar.",
        "No soil-moisture sensor validation — depletion estimates carry model uncertainty.",
        "No irrigation-event records; both FAO-56 models are rainfed-only depletion balances.",
    ]
    staleness = (today - fao56_date).days
    if staleness > 1:
        parts.append(
            f"FAO-56 status is {staleness} day(s) old (last date: {fao56_date}). "
            "Re-run `python main.py --skip-fetch` to refresh before acting on this advisory."
        )
    if forecast_available:
        parts.append(
            f"Forecast is at {forecast_resolution} resolution — 6-hour and 12-hour rainfall totals "
            "are not computable. Decision thresholds are applied to the next-24-hour total."
        )
        parts.append(
            "Rain probability is not provided in the current Open-Meteo daily output and "
            "has been omitted from this advisory."
        )
    else:
        parts.append(
            "Forecast data was unavailable; advisory is based on FAO-56 water stress status only."
        )
    return " | ".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_forecast_aware_advisory() -> Path:
    """
    Generate the irrigation advisory CSV and print a console summary.
    Returns the Path to the written output file.
    """
    today = datetime.now().date()
    generated_at = datetime.now().isoformat(timespec="seconds")

    # ── FAO-56 phenology water balance ────────────────────────────────────
    if not FAO56_PHENOLOGY_WB_PATH.exists():
        raise FileNotFoundError(
            f"Required input not found: {FAO56_PHENOLOGY_WB_PATH}\n"
            "Run `python main.py --skip-fetch` to generate it."
        )
    wb_df = _load_phenology_water_balance(FAO56_PHENOLOGY_WB_PATH)
    if wb_df.empty:
        raise ValueError(f"Phenology water balance file is empty: {FAO56_PHENOLOGY_WB_PATH}")

    latest = wb_df.iloc[-1]
    current_date: date = latest["date"].date()
    mango_stage: str = str(latest["mango_stage"])
    water_stress_level: str = str(latest["water_stress_level"])
    kc: float = float(latest["kc"])
    et0_mm_day: float = float(latest["et0_mm_day"])
    etc_mm_day: float = float(latest["etc_mm_day"])
    root_zone_depletion_mm: float = float(latest["root_zone_depletion_mm"])
    ks: float = float(latest["ks"])

    log.info(
        "FAO-56 status (%s): stage=%s, stress=%s, Ks=%.3f, depletion=%.1f mm",
        current_date, mango_stage, water_stress_level, ks, root_zone_depletion_mm,
    )

    # ── Forecast ──────────────────────────────────────────────────────────
    if FORECAST_RISK_PATH.exists():
        fc_df = _load_forecast(FORECAST_RISK_PATH)
        fc_summary = _build_forecast_rain_summary(fc_df, today)
    else:
        log.warning("Forecast file not found: %s. Advisory will use FAO-56 status only.", FORECAST_RISK_PATH)
        fc_summary = {
            "forecast_resolution": "daily",
            "rain_next_6h_mm": None,
            "rain_next_12h_mm": None,
            "rain_next_24h_mm": None,
            "rain_probability_next_24h": None,
            "forecast_available": False,
        }

    # ── Decision ──────────────────────────────────────────────────────────
    advisory_action, advisory_priority, advisory_reason = _decide_advisory(
        stress_level=water_stress_level,
        mango_stage=mango_stage,
        ks=ks,
        rain_next_24h=fc_summary["rain_next_24h_mm"],
        forecast_available=fc_summary["forecast_available"],
    )

    advisory_limitations = _build_limitations(
        fao56_date=current_date,
        today=today,
        forecast_available=fc_summary["forecast_available"],
        forecast_resolution=fc_summary["forecast_resolution"],
    )

    # ── Assemble output ───────────────────────────────────────────────────
    record = {
        "advisory_generated_at": generated_at,
        "current_date": str(current_date),
        "mango_stage": mango_stage,
        "water_stress_level": water_stress_level,
        "kc": round(kc, 4),
        "et0_mm_day": round(et0_mm_day, 4),
        "etc_mm_day": round(etc_mm_day, 4),
        "root_zone_depletion_mm": round(root_zone_depletion_mm, 4),
        "ks": round(ks, 4),
        "forecast_resolution": fc_summary["forecast_resolution"],
        "rain_next_6h_mm": fc_summary["rain_next_6h_mm"],
        "rain_next_12h_mm": fc_summary["rain_next_12h_mm"],
        "rain_next_24h_mm": fc_summary["rain_next_24h_mm"],
        "rain_probability_next_24h": fc_summary["rain_probability_next_24h"],
        "advisory_action": advisory_action,
        "advisory_priority": advisory_priority,
        "advisory_reason": advisory_reason,
        "advisory_limitations": advisory_limitations,
    }

    out_df = pd.DataFrame([record])
    ADVISORY_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(ADVISORY_OUTPUT_PATH, index=False)
    log.info("Advisory written to %s", ADVISORY_OUTPUT_PATH)

    # ── Console summary ───────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("FORECAST-AWARE IRRIGATION ADVISORY  —  Muthukur Mango Orchard")
    print("=" * 70)
    print(f"Generated at:          {generated_at}")
    print(f"FAO-56 status date:    {current_date}")
    print(f"Mango stage:           {mango_stage}")
    print(f"Water stress level:    {water_stress_level}  (Ks={ks:.3f})")
    print(f"ETc (mm/day):          {etc_mm_day:.3f}")
    print(f"Root zone depletion:   {root_zone_depletion_mm:.1f} mm")
    print(f"Forecast resolution:   {fc_summary['forecast_resolution']}")
    print(f"Rain next 24h (mm):    {fc_summary['rain_next_24h_mm']}")
    print(f"Rain next 6h (mm):     {fc_summary['rain_next_6h_mm']}  (hourly data not available)")
    print(f"Rain next 12h (mm):    {fc_summary['rain_next_12h_mm']}  (hourly data not available)")
    print(f"Rain probability 24h:  {fc_summary['rain_probability_next_24h']}  (not in Open-Meteo daily output)")
    print()
    print(f">>> Advisory action:   {advisory_action}")
    print(f">>> Priority:          {advisory_priority}")
    print(f">>> Reason:            {advisory_reason}")
    print()
    print("Limitations:")
    for part in advisory_limitations.split(" | "):
        print(f"  - {part}")
    print("=" * 70)
    print(f"\nSaved to: {ADVISORY_OUTPUT_PATH}")

    return ADVISORY_OUTPUT_PATH


if __name__ == "__main__":
    run_forecast_aware_advisory()
