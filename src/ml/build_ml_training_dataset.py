"""
Build an ML-ready training dataset (one row per date) for the Sensor-Free
Mango Digital Twin.

WHAT THIS IS (and is NOT):
  - Dataset builder only. No model is trained and nothing here is an AI/ML
    feature yet; no dashboard page reads this file.
  - Target columns are SURROGATE labels derived from the existing
    FAO-56 water balance and the rule-based advisory logic. They are NOT
    field-validated labels (no soil-moisture sensors, no observed stress).
    A model trained on them can at best learn to imitate the rules.

INPUTS
  data/processed/muthukur_combined_feature_table.csv
  data/processed/muthukur_fao56_interpolated_kc_water_balance.csv
  data/processed/muthukur_open_meteo_forecast_risk.csv   (optional)
  data/manual/muthukur_irrigation_events.csv             (optional)

  The forecast-aware advisory CSV is a single "current day" row, so it is
  not joined; per-date priority labels are produced by applying the same
  decision function (`_decide_advisory`) to every date instead.

TARGET LABEL RULES
  target_water_stress_level      = FAO-56 water_stress_level
  target_irrigation_priority     = advisory rules with NO forecast available
                                   (historical rows have no forecast issued
                                   at the time), i.e. High/Medium/Low stress
                                   -> High/Medium/Low priority
  target_irrigation_needed_binary = 1 if priority == "High" else 0

OUTPUT
  data/processed/muthukur_ml_training_dataset.csv

      python src/ml/build_ml_training_dataset.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.advisory.forecast_aware_irrigation import _decide_advisory  # noqa: E402
from src.irrigation.load_irrigation_events import load_irrigation_events  # noqa: E402
from src.utils.config import get_config  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

log = get_logger(__name__)

TARGET_COLUMNS = [
    "target_irrigation_priority",
    "target_water_stress_level",
    "target_irrigation_needed_binary",
]

IRRIGATION_HISTORY_COLUMNS = [
    "days_since_last_irrigation",
    "irrigation_last_7d_mm",
    "irrigation_last_14d_mm",
    "irrigation_event_count_last_30d",
]

# FAO-56 columns carried into the dataset (rainfall_mm already comes from
# the feature table).
_FAO_COLUMNS = [
    "mango_stage", "stage_kc", "interpolated_kc", "et0_mm_day", "etc_mm_day",
    "irrigation_mm", "water_input_mm", "root_zone_depletion_mm",
    "taw_mm", "raw_mm", "ks", "water_stress_level",
]

# Free-form identifier/text columns that are not model features.
_DROP_FEATURE_COLUMNS = ["data_source", "sentinel2_date", "sentinel1_date"]


def _read_dated_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["date"])


def _dedupe_by_date(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Drop exact duplicate rows, then keep the last row for any repeated date."""
    df = df.drop_duplicates()
    dup = int(df["date"].duplicated().sum())
    if dup:
        log.warning("%s: %d duplicate date(s) with differing values; keeping last.", label, dup)
        df = df.drop_duplicates(subset="date", keep="last")
    return df


def add_irrigation_history_features(df: pd.DataFrame, events: pd.DataFrame | None) -> pd.DataFrame:
    """
    Add days_since_last_irrigation, irrigation_last_{7,14}d_mm and
    irrigation_event_count_last_30d. Windows are inclusive of the row's own
    date and look backwards only. Events are irrigation days (the loader
    already merges same-day entries). days_since_last_irrigation is NaN
    until the first recorded event.
    """
    out = df.copy()
    if events is None or events.empty:
        out["days_since_last_irrigation"] = np.nan
        out["irrigation_last_7d_mm"] = 0.0
        out["irrigation_last_14d_mm"] = 0.0
        out["irrigation_event_count_last_30d"] = 0
        return out

    ev = events.groupby("date")["irrigation_mm"].sum()
    dates = pd.DatetimeIndex(out["date"])
    full = pd.date_range(
        min(dates.min(), ev.index.min()), max(dates.max(), ev.index.max()), freq="D"
    )
    daily = ev.reindex(full, fill_value=0.0)
    is_event = (daily > 0).astype(int)

    last_event = pd.Series(full.where(daily > 0), index=full).ffill()
    days_since = (pd.Series(full, index=full) - last_event).dt.days

    sums7 = daily.rolling(7, min_periods=1).sum()
    sums14 = daily.rolling(14, min_periods=1).sum()
    count30 = is_event.rolling(30, min_periods=1).sum()

    out["days_since_last_irrigation"] = days_since.reindex(dates).to_numpy()
    out["irrigation_last_7d_mm"] = sums7.reindex(dates).to_numpy()
    out["irrigation_last_14d_mm"] = sums14.reindex(dates).to_numpy()
    out["irrigation_event_count_last_30d"] = count30.reindex(dates).astype(int).to_numpy()
    return out


def add_surrogate_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the surrogate target columns from FAO-56 stress + advisory rules."""
    out = df.copy()
    stress = out.get("water_stress_level", pd.Series(np.nan, index=out.index, dtype=object))
    stage = out.get("mango_stage", pd.Series("", index=out.index))
    ks = out.get("ks", pd.Series(np.nan, index=out.index))

    priorities = []
    for s, st, k in zip(stress, stage, ks):
        if pd.isna(s) or s not in ("Low", "Medium", "High"):
            priorities.append(np.nan)
            continue
        _, priority, _ = _decide_advisory(
            stress_level=s,
            mango_stage="" if pd.isna(st) else st,
            ks=0.0 if pd.isna(k) else float(k),
            rain_next_24h=None,
            forecast_available=False,
        )
        priorities.append(priority)

    out["target_irrigation_priority"] = priorities
    out["target_water_stress_level"] = stress.where(stress.isin(["Low", "Medium", "High"]))
    out["target_irrigation_needed_binary"] = pd.array(
        [pd.NA if pd.isna(p) else int(p == "High") for p in priorities], dtype="Int64"
    )
    return out


def build_dataset_frame(
    features: pd.DataFrame,
    fao56: pd.DataFrame,
    events: pd.DataFrame | None = None,
    forecast: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Pure assembly step (no file I/O). Optional inputs may be None/empty."""
    feat = features.copy()
    feat["date"] = pd.to_datetime(feat["date"], errors="coerce")
    feat = _dedupe_by_date(feat.dropna(subset=["date"]), "combined feature table")
    feat = feat.drop(columns=[c for c in _DROP_FEATURE_COLUMNS if c in feat.columns])
    # The FAO-56 side owns irrigation/water-input; avoid suffix collisions.
    feat = feat.drop(columns=[c for c in ("irrigation_mm", "water_input_mm") if c in feat.columns])

    fao = fao56.copy()
    fao["date"] = pd.to_datetime(fao["date"], errors="coerce")
    fao = _dedupe_by_date(fao.dropna(subset=["date"]), "FAO-56 water balance")
    fao = fao[["date"] + [c for c in _FAO_COLUMNS if c in fao.columns]].copy()
    if "irrigation_mm" not in fao.columns:
        fao["irrigation_mm"] = 0.0
    if "water_input_mm" not in fao.columns:
        fao["water_input_mm"] = np.nan

    df = feat.merge(fao, on="date", how="left")
    if "interpolated_kc" in df.columns:
        df["kc"] = df["interpolated_kc"]

    if forecast is not None and not forecast.empty:
        fc = forecast.copy()
        fc["date"] = pd.to_datetime(fc["date"], errors="coerce")
        fc = _dedupe_by_date(fc.dropna(subset=["date"]), "forecast risk")
        fc_cols = [
            c for c in (
                "irrigation_risk_score", "heat_stress_risk_score", "disease_risk_score",
                "irrigation_risk_level", "heat_stress_risk_level", "disease_risk_level",
                "soil_adjusted_irrigation_risk_score", "soil_adjusted_irrigation_risk_level",
            ) if c in fc.columns
        ]
        fc = fc[["date"] + fc_cols].rename(columns={c: f"forecast_{c}" for c in fc_cols})
        df = df.merge(fc, on="date", how="left")

    df = add_irrigation_history_features(df, events)
    df = add_surrogate_targets(df)

    df = df.drop_duplicates().sort_values("date").reset_index(drop=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df


def summarize_dataset(df: pd.DataFrame) -> dict:
    feature_cols = [c for c in df.columns if c != "date" and c not in TARGET_COLUMNS]
    missing = df.isna().sum()
    return {
        "row_count": int(len(df)),
        "date_min": df["date"].min() if len(df) else None,
        "date_max": df["date"].max() if len(df) else None,
        "feature_count": len(feature_cols),
        "target_distribution": {
            t: {(k if isinstance(k, str) or pd.isna(k) else int(k)): int(v)
                for k, v in df[t].value_counts(dropna=False).items()}
            for t in TARGET_COLUMNS if t in df.columns
        },
        "missing_values": {c: int(n) for c, n in missing.items() if n > 0},
    }


def build_ml_training_dataset(config=None) -> bool:
    """Build and write the ML training dataset. Returns True on success."""
    config = config or get_config()
    feat_path = config.path("combined_feature_table_csv")
    fao_path = config.path("fao56_interpolated_kc_water_balance_csv")
    out_path = config.path("ml_training_dataset_csv")

    for p in (feat_path, fao_path):
        if not p.exists():
            print(f"\nMissing required input: {p}")
            return False

    features = _read_dated_csv(feat_path)
    fao56 = _read_dated_csv(fao_path)

    fc_path = config.path("forecast_risk_csv")
    forecast = _read_dated_csv(fc_path) if fc_path.exists() else None
    events = load_irrigation_events(config.path("irrigation_events_csv"))

    df = build_dataset_frame(features, fao56, events, forecast)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    s = summarize_dataset(df)
    log.info(
        "ML training dataset: %d rows, %s to %s, %d features -> %s",
        s["row_count"], s["date_min"], s["date_max"], s["feature_count"], out_path,
    )
    print()
    print(f">>> ML training dataset written to: {out_path}")
    print(f">>> Rows: {s['row_count']}   Date range: {s['date_min']} to {s['date_max']}")
    print(f">>> Feature columns: {s['feature_count']}   Target columns: {len(TARGET_COLUMNS)}")
    for t, dist in s["target_distribution"].items():
        print(f">>> {t}: {dist}")
    if s["missing_values"]:
        top = sorted(s["missing_values"].items(), key=lambda kv: -kv[1])[:10]
        print(">>> Columns with missing values (top 10): " + ", ".join(f"{c}={n}" for c, n in top))
    print(">>> NOTE: target_* columns are surrogate labels from FAO-56/rule-based "
          "advisory logic, NOT field-validated.")
    return True


if __name__ == "__main__":
    sys.exit(0 if build_ml_training_dataset() else 1)
