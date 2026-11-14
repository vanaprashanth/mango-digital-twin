"""
Label-quality audit for the surrogate irrigation-priority targets.

PURPOSE
  Explain WHY the surrogate labels in the ML training dataset are heavily
  imbalanced and why Medium vs High is not reliably separable, using only
  evidence in the data. This is a diagnostic: it does not change the target,
  thresholds, FAO-56 parameters, the trainer, or any irrigation records, and
  it never invents irrigation events.

  The "unclipped depletion" column is a DIAGNOSTIC re-computation of the
  running balance without the TAW cap (same water input and ETc), used only
  to show how much deficit the cap hides. It is not a model output.

INPUT   data/processed/muthukur_ml_training_dataset.csv
OUTPUTS data/processed/muthukur_ml_label_audit.csv
        data/processed/muthukur_ml_label_audit_summary.json

      python src/ml/audit_label_quality.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_config  # noqa: E402
from src.utils.logger import get_logger  # noqa: E402

log = get_logger(__name__)

LABEL = "target_irrigation_priority"
CLASSES = ["Low", "Medium", "High"]

# Same thresholds as src/water_balance/fao56_water_balance.py (_water_stress_label).
# Duplicated deliberately as audit constants so the audit can detect drift.
KS_LOW_STRESS_MIN = 0.90
KS_MEDIUM_STRESS_MIN = 0.60

IMPORTANT_FEATURES = [
    "ks", "root_zone_depletion_mm", "taw_mm", "raw_mm", "mango_stage", "interpolated_kc",
    "et0_mm_day", "etc_mm_day", "rainfall_mm", "irrigation_mm", "water_input_mm",
    "temperature_avg_c", "relative_humidity_percent", "solar_radiation_mj_m2",
    "wind_speed_m_s", "ndvi_mean", "ndmi_mean", "vv_mean", "vh_mean",
    "days_since_last_irrigation",
]

SEASONS = {
    1: "Winter (Jan-Feb)", 2: "Winter (Jan-Feb)",
    3: "Summer (Mar-May)", 4: "Summer (Mar-May)", 5: "Summer (Mar-May)",
    6: "SW monsoon (Jun-Sep)", 7: "SW monsoon (Jun-Sep)",
    8: "SW monsoon (Jun-Sep)", 9: "SW monsoon (Jun-Sep)",
    10: "NE monsoon (Oct-Dec)", 11: "NE monsoon (Oct-Dec)", 12: "NE monsoon (Oct-Dec)",
}

LIMITATIONS = [
    "All labels are surrogate labels derived from the FAO-56 water balance and rule-based "
    "thresholds; there are no field observations (soil moisture, canopy stress, yield) to check them against.",
    "The audit covers roughly two calendar years, i.e. very few independent wet/dry regime changes, "
    "so seasonal conclusions rest on a small number of cycles.",
    "Only the irrigation events recorded in data/manual/muthukur_irrigation_events.csv are modelled; "
    "whether the orchard was actually irrigated at other times is unknown and cannot be inferred from this data.",
    "Unclipped depletion is a diagnostic re-computation using rounded daily columns, not a model output.",
    "Percentages describe this dataset only and do not estimate real-world irrigation need.",
]


# ---------------------------------------------------------------------------
# Preparation
# ---------------------------------------------------------------------------

def prepare_frame(df: pd.DataFrame | None) -> pd.DataFrame:
    """Date-sorted copy with parsed dates; rows without a valid date are dropped."""
    if df is None or df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=["date", LABEL])
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if LABEL not in out.columns:
        out[LABEL] = np.nan
    return out


def ks_to_label(ks: float) -> str | float:
    """Label implied by the FAO-56 Ks thresholds (NaN stays NaN)."""
    if pd.isna(ks):
        return np.nan
    if ks >= KS_LOW_STRESS_MIN:
        return "Low"
    if ks >= KS_MEDIUM_STRESS_MIN:
        return "Medium"
    return "High"


def unclipped_depletion(water_input_mm: np.ndarray, etc_mm: np.ndarray) -> np.ndarray:
    """Running depletion with a floor at 0 but NO cap at TAW (diagnostic only)."""
    out = np.zeros(len(etc_mm))
    prev = 0.0
    for i in range(len(etc_mm)):
        w = 0.0 if np.isnan(water_input_mm[i]) else water_input_mm[i]
        e = 0.0 if np.isnan(etc_mm[i]) else etc_mm[i]
        prev = max(0.0, prev - w + e)
        out[i] = prev
    return out


# ---------------------------------------------------------------------------
# Distributions
# ---------------------------------------------------------------------------

def class_distribution(labels: pd.Series) -> dict:
    """Total/labelled/missing counts and per-class counts and percentages."""
    total = int(len(labels))
    labelled = labels.dropna()
    n = int(len(labelled))
    counts = labelled.value_counts()
    return {
        "total_records": total,
        "labelled_records": n,
        "missing_labels": total - n,
        "classes": {
            c: {
                "count": int(counts.get(c, 0)),
                "percent": round(100.0 * counts.get(c, 0) / n, 2) if n else None,
            }
            for c in sorted(set(CLASSES) | set(counts.index), key=lambda c: (c not in CLASSES, CLASSES.index(c) if c in CLASSES else 0, str(c)))
        },
    }


def _crosstab_dict(index: pd.Series, labels: pd.Series) -> dict:
    mask = labels.notna() & index.notna()
    if not mask.any():
        return {}
    ct = pd.crosstab(index[mask], labels[mask])
    for c in CLASSES:
        if c not in ct.columns:
            ct[c] = 0
    ct = ct[CLASSES + [c for c in ct.columns if c not in CLASSES]]
    return {str(k): {c: int(v) for c, v in row.items()} for k, row in ct.iterrows()}


def monthly_distribution(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    return _crosstab_dict(df["date"].dt.strftime("%Y-%m"), df[LABEL])


def seasonal_distribution(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    return _crosstab_dict(df["date"].dt.month.map(SEASONS), df[LABEL])


def yearly_distribution(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    return _crosstab_dict(df["date"].dt.year.astype(str), df[LABEL])


def stage_distribution(df: pd.DataFrame) -> dict:
    if df.empty or "mango_stage" not in df.columns:
        return {}
    return _crosstab_dict(df["mango_stage"], df[LABEL])


def pure_month_share(monthly: dict) -> float | None:
    """Share of months in which one class accounts for every labelled day."""
    if not monthly:
        return None
    pure = sum(1 for row in monthly.values() if sum(v > 0 for v in row.values()) == 1)
    return round(pure / len(monthly), 3)


# ---------------------------------------------------------------------------
# Runs and transitions
# ---------------------------------------------------------------------------

def label_runs(df: pd.DataFrame) -> pd.DataFrame:
    """Consecutive runs of identical labels (missing labels break a run)."""
    cols = ["run_id", "label", "start", "end", "length"]
    if df.empty:
        return pd.DataFrame(columns=cols)
    lab = df[LABEL].astype(object).where(df[LABEL].notna(), None)
    change = (lab != lab.shift()).cumsum()
    g = df.assign(_lab=lab, _run=change).groupby("_run")
    out = g.agg(label=("_lab", "first"), start=("date", "min"), end=("date", "max"), length=("date", "size"))
    out = out[out["label"].notna()].reset_index(drop=True)
    out.insert(0, "run_id", np.arange(1, len(out) + 1))
    return out[cols]


def run_summary(runs: pd.DataFrame, top_n: int = 5) -> dict:
    if runs.empty:
        return {"run_count": 0, "longest_runs": [], "by_class": {}}
    longest = runs.sort_values("length", ascending=False).head(top_n)
    by_class = {}
    for c, g in runs.groupby("label"):
        by_class[str(c)] = {
            "runs": int(len(g)),
            "median_length_days": float(g["length"].median()),
            "max_length_days": int(g["length"].max()),
        }
    return {
        "run_count": int(len(runs)),
        "longest_runs": [
            {"label": r.label, "start": r.start.strftime("%Y-%m-%d"),
             "end": r.end.strftime("%Y-%m-%d"), "length_days": int(r.length)}
            for r in longest.itertuples()
        ],
        "by_class": by_class,
    }


def transition_analysis(df: pd.DataFrame) -> dict:
    """Day-to-day label transitions and how abruptly Ks changes."""
    lab = df[LABEL]
    prev = lab.shift()
    pairs = pd.DataFrame({"from": prev, "to": lab}).dropna()
    changed = pairs[pairs["from"] != pairs["to"]]
    matrix = {
        f: {t: int(((pairs["from"] == f) & (pairs["to"] == t)).sum()) for t in CLASSES}
        for f in CLASSES
    }
    skip = int((((changed["from"] == "Low") & (changed["to"] == "High"))
                | ((changed["from"] == "High") & (changed["to"] == "Low"))).sum())
    out = {
        "label_changes": int(len(changed)),
        "change_rate_per_day": round(len(changed) / len(pairs), 4) if len(pairs) else None,
        "transition_matrix": matrix,
        "direct_low_high_jumps_skipping_medium": skip,
    }
    if "ks" in df.columns and df["ks"].notna().any():
        d = df["ks"].diff().abs().dropna()
        out["ks_abs_daily_change"] = {
            "median": round(float(d.median()), 4),
            "p95": round(float(d.quantile(0.95)), 4),
            "max": round(float(d.max()), 4),
        }
        out["ks_daily_jumps_over_0.2"] = int((d > 0.2).sum())
    return out


# ---------------------------------------------------------------------------
# Relationships with Ks, depletion, thresholds
# ---------------------------------------------------------------------------

def _by_class_stats(df: pd.DataFrame, col: str) -> dict:
    if col not in df.columns:
        return {}
    out = {}
    for c in CLASSES:
        s = df.loc[df[LABEL] == c, col].dropna()
        out[c] = (
            {"n": int(len(s)), "min": round(float(s.min()), 4), "median": round(float(s.median()), 4),
             "max": round(float(s.max()), 4)} if len(s) else {"n": 0}
        )
    return out


def ks_label_relationship(df: pd.DataFrame) -> dict:
    """How well the label is determined by Ks, and how Ks is distributed."""
    if "ks" not in df.columns or df["ks"].notna().sum() == 0:
        return {"available": False}
    both = df.dropna(subset=["ks", LABEL])
    implied = both["ks"].map(ks_to_label)
    ks = df["ks"].dropna()
    return {
        "available": True,
        "ks_by_class": _by_class_stats(df, "ks"),
        "label_matches_ks_thresholds_percent": (
            round(100.0 * float((implied == both[LABEL]).mean()), 2) if len(both) else None),
        "ks_missing": int(df["ks"].isna().sum()),
        "share_ks_exactly_0_percent": round(100.0 * float((ks <= 1e-9).mean()), 2),
        "share_ks_exactly_1_percent": round(100.0 * float((ks >= 1 - 1e-9).mean()), 2),
        "share_ks_between_0_and_0.9_percent": round(
            100.0 * float(((ks > 1e-9) & (ks < KS_LOW_STRESS_MIN)).mean()), 2),
        "share_ks_in_medium_band_percent": round(
            100.0 * float(((ks >= KS_MEDIUM_STRESS_MIN) & (ks < KS_LOW_STRESS_MIN)).mean()), 2),
        "thresholds": {"low_min": KS_LOW_STRESS_MIN, "medium_min": KS_MEDIUM_STRESS_MIN},
    }


def depletion_label_relationship(df: pd.DataFrame) -> dict:
    col = "root_zone_depletion_mm"
    if col not in df.columns or df[col].notna().sum() == 0:
        return {"available": False}
    out = {
        "available": True,
        "depletion_by_class": _by_class_stats(df, col),
        "depletion_missing": int(df[col].isna().sum()),
    }
    if "taw_mm" in df.columns and df["taw_mm"].notna().any():
        taw = float(df["taw_mm"].dropna().iloc[0])
        out["taw_mm"] = round(taw, 3)
        if "raw_mm" in df.columns and df["raw_mm"].notna().any():
            raw = float(df["raw_mm"].dropna().iloc[0])
            out["raw_mm"] = round(raw, 3)
            span = taw - raw
            out["depletion_band_mm"] = {
                "Low_below": round(taw - KS_LOW_STRESS_MIN * span, 2),
                "Medium_width": round((KS_LOW_STRESS_MIN - KS_MEDIUM_STRESS_MIN) * span, 2),
                "High_from": round(taw - KS_MEDIUM_STRESS_MIN * span, 2),
                "High_width_to_taw": round(KS_MEDIUM_STRESS_MIN * span, 2),
            }
            if "etc_mm_day" in df.columns and df["etc_mm_day"].notna().any():
                et = float(df["etc_mm_day"].median())
                out["median_etc_mm_day"] = round(et, 3)
                if et > 0:
                    out["days_to_cross_medium_band_at_median_etc"] = round(
                        (KS_LOW_STRESS_MIN - KS_MEDIUM_STRESS_MIN) * span / et, 1)
    return out


def saturation_analysis(df: pd.DataFrame) -> dict:
    """How often depletion sits on the TAW cap (Ks = 0) and what the cap hides."""
    need = {"root_zone_depletion_mm", "taw_mm"}
    if not need <= set(df.columns) or df["taw_mm"].notna().sum() == 0:
        return {"available": False}
    at_cap = (df["root_zone_depletion_mm"] >= df["taw_mm"] - 1e-6) & df["root_zone_depletion_mm"].notna()
    n = int(len(df))
    high = df[LABEL] == "High"
    run_lengths, cur = [], 0
    for v in at_cap.to_numpy():
        if v:
            cur += 1
        else:
            if cur:
                run_lengths.append(cur)
            cur = 0
    if cur:
        run_lengths.append(cur)
    out = {
        "available": True,
        "days_at_taw_cap": int(at_cap.sum()),
        "percent_of_records": round(100.0 * at_cap.sum() / n, 2) if n else None,
        "percent_of_high_labels_at_cap": (
            round(100.0 * float((at_cap & high).sum()) / high.sum(), 2) if high.sum() else None),
        "longest_continuous_cap_run_days": int(max(run_lengths)) if run_lengths else 0,
        "cap_run_count": len(run_lengths),
    }
    if high.any():
        frac = (df.loc[high, "root_zone_depletion_mm"] / df.loc[high, "taw_mm"]).dropna()
        if len(frac):
            out["high_labels_depletion_fraction_of_taw"] = {
                "min": round(float(frac.min()), 3), "p25": round(float(frac.quantile(0.25)), 3),
                "median": round(float(frac.median()), 3), "mean": round(float(frac.mean()), 3),
            }
    if {"water_input_mm", "etc_mm_day"} <= set(df.columns):
        unc = unclipped_depletion(df["water_input_mm"].to_numpy(float), df["etc_mm_day"].to_numpy(float))
        taw = float(df["taw_mm"].dropna().iloc[0])
        out["diagnostic_unclipped_depletion"] = {
            "max_mm": round(float(unc.max()), 1),
            "max_as_multiple_of_taw": round(float(unc.max()) / taw, 2),
            "days_beyond_taw": int((unc > taw + 1e-6).sum()),
        }
    return out


def rain_irrigation_assumptions(df: pd.DataFrame) -> dict:
    out: dict = {}
    if "irrigation_mm" in df.columns:
        irr = df["irrigation_mm"].fillna(0)
        ev = df[irr > 0]
        out["irrigation_event_days"] = int(len(ev))
        out["irrigation_total_mm"] = round(float(irr.sum()), 2)
        out["irrigation_event_dates"] = [d.strftime("%Y-%m-%d") for d in ev["date"]]
        out["irrigation_largest_event_mm"] = round(float(irr.max()), 2) if len(irr) else None
    if {"rainfall_mm", "etc_mm_day"} <= set(df.columns) and not df.empty:
        g = df.groupby(df["date"].dt.year)
        out["rain_vs_etc_by_year_mm"] = {
            str(y): {"rain": round(float(s["rainfall_mm"].sum()), 1),
                     "etc": round(float(s["etc_mm_day"].sum()), 1),
                     "days": int(len(s))}
            for y, s in g
        }
        sg = df.groupby(df["date"].dt.month.map(SEASONS))
        out["rain_to_etc_ratio_by_season"] = {
            str(k): round(float(s["rainfall_mm"].sum() / max(s["etc_mm_day"].sum(), 1e-9)), 3)
            for k, s in sg
        }
        wet = df["rainfall_mm"].fillna(0) >= 1.0
        longest, cur = 0, 0
        for v in wet.to_numpy():
            cur = 0 if v else cur + 1
            longest = max(longest, cur)
        out["longest_stretch_days_without_1mm_rain"] = int(longest)
    return out


def missing_value_summary(df: pd.DataFrame, columns: list[str] | None = None) -> dict:
    cols = [c for c in (columns or IMPORTANT_FEATURES) if c in df.columns]
    n = len(df)
    absent = [c for c in (columns or IMPORTANT_FEATURES) if c not in df.columns]
    return {
        "records": int(n),
        "columns_missing_from_dataset": absent,
        "missing_by_column": {
            c: {"missing": int(df[c].isna().sum()),
                "percent": round(100.0 * df[c].isna().mean(), 2) if n else None}
            for c in cols
        },
    }


# ---------------------------------------------------------------------------
# Row-level audit table
# ---------------------------------------------------------------------------

def build_audit_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per-date audit rows: label, Ks, depletion, stage and derived diagnostics."""
    out = pd.DataFrame({"date": df["date"].dt.strftime("%Y-%m-%d"), "surrogate_label": df[LABEL]})
    for col in ("ks", "root_zone_depletion_mm", "taw_mm", "mango_stage",
                "rainfall_mm", "irrigation_mm", "etc_mm_day"):
        out[col] = df[col] if col in df.columns else np.nan
    out["month"] = df["date"].dt.month
    out["season"] = df["date"].dt.month.map(SEASONS)
    if "taw_mm" in df.columns and "root_zone_depletion_mm" in df.columns:
        out["depletion_fraction_of_taw"] = (df["root_zone_depletion_mm"] / df["taw_mm"]).round(4)
        out["at_taw_cap"] = (df["root_zone_depletion_mm"] >= df["taw_mm"] - 1e-6)
    else:
        out["depletion_fraction_of_taw"] = np.nan
        out["at_taw_cap"] = False
    if {"water_input_mm", "etc_mm_day"} <= set(df.columns):
        out["depletion_unclipped_mm"] = np.round(
            unclipped_depletion(df["water_input_mm"].to_numpy(float), df["etc_mm_day"].to_numpy(float)), 2)
    else:
        out["depletion_unclipped_mm"] = np.nan
    out["label_from_ks_thresholds"] = df["ks"].map(ks_to_label) if "ks" in df.columns else np.nan
    out["label_matches_ks_rule"] = out["label_from_ks_thresholds"] == out["surrogate_label"]
    out["ks_abs_change"] = df["ks"].diff().abs().round(4) if "ks" in df.columns else np.nan
    out["label_changed"] = df[LABEL].ne(df[LABEL].shift()) & df[LABEL].shift().notna()

    runs = label_runs(df)
    run_id = np.full(len(df), np.nan)
    run_len = np.full(len(df), np.nan)
    day_in_run = np.full(len(df), np.nan)
    dates = df["date"].to_numpy()
    for r in runs.itertuples():
        m = (dates >= np.datetime64(r.start)) & (dates <= np.datetime64(r.end)) & df[LABEL].eq(r.label).to_numpy()
        idx = np.flatnonzero(m)
        run_id[idx] = r.run_id
        run_len[idx] = r.length
        day_in_run[idx] = np.arange(1, len(idx) + 1)
    out["run_id"], out["run_length_days"], out["day_in_run"] = run_id, run_len, day_in_run

    if "rainfall_mm" in df.columns:
        out["rain_7d_mm"] = df["rainfall_mm"].fillna(0).rolling(7, min_periods=1).sum().round(2)
    if "etc_mm_day" in df.columns:
        out["etc_7d_mm"] = df["etc_mm_day"].fillna(0).rolling(7, min_periods=1).sum().round(2)
    return out


# ---------------------------------------------------------------------------
# Findings and recommendations (every statement is computed from the data)
# ---------------------------------------------------------------------------

def build_findings(summary: dict) -> list[dict]:
    """Evidence-supported findings; each has supported=True/False and its evidence."""
    f: list[dict] = []
    dist = summary["class_distribution"]["classes"]
    n_lab = summary["class_distribution"]["labelled_records"]
    sat = summary["saturation"]
    ks = summary["ks_relationship"]
    dep = summary["depletion_relationship"]
    runs = summary["label_runs"]
    ass = summary["rain_irrigation_assumptions"]
    seasonal = summary["seasonal_distribution"]
    trans = summary["transitions"]

    if not n_lab:
        return [{"id": "no_labels", "supported": True,
                 "statement": "No labelled records; nothing to audit.", "evidence": {}}]

    high_pct = dist.get("High", {}).get("percent")
    med_pct = dist.get("Medium", {}).get("percent")

    # 1. Label is a deterministic function of Ks
    match = ks.get("label_matches_ks_thresholds_percent")
    f.append({
        "id": "labels_are_deterministic_function_of_ks",
        "supported": bool(match is not None and match >= 99.9),
        "statement": "Labels reproduce the FAO-56 Ks thresholds exactly, so they carry no information "
                     "beyond the water-balance state.",
        "evidence": {"label_matches_ks_thresholds_percent": match},
    })

    # 2. Saturation dominates High
    hi_at_cap = sat.get("percent_of_high_labels_at_cap")
    f.append({
        "id": "high_class_dominated_by_depletion_saturation",
        "supported": bool(hi_at_cap is not None and hi_at_cap >= 50),
        "statement": "Most High labels are days where root-zone depletion sits exactly on the TAW cap "
                     "(Ks = 0) and the rest are close to it, so High marks a saturated state rather than "
                     "grading degrees of stress. The cap discards any deficit beyond TAW.",
        "evidence": {
            "percent_of_high_labels_at_cap": hi_at_cap,
            "high_labels_depletion_fraction_of_taw": sat.get("high_labels_depletion_fraction_of_taw"),
            "days_at_taw_cap": sat.get("days_at_taw_cap"),
            "longest_continuous_cap_run_days": sat.get("longest_continuous_cap_run_days"),
            "diagnostic_unclipped_depletion": sat.get("diagnostic_unclipped_depletion"),
        },
    })

    # 3. Medium is a narrow transitional band
    cross = dep.get("days_to_cross_medium_band_at_median_etc")
    med_median_run = runs.get("by_class", {}).get("Medium", {}).get("median_length_days")
    f.append({
        "id": "medium_class_is_a_narrow_transition_band",
        "supported": bool(med_pct is not None and med_pct < 10),
        "statement": "Medium covers a narrow depletion band that is crossed in about a week; it exists "
                     "only transiently between Low and a saturated High, so it is rare and hard to learn.",
        "evidence": {
            "medium_percent": med_pct,
            "medium_band_width_mm": (dep.get("depletion_band_mm") or {}).get("Medium_width"),
            "high_band_width_mm_to_taw": (dep.get("depletion_band_mm") or {}).get("High_width_to_taw"),
            "days_to_cross_medium_band_at_median_etc": cross,
            "median_medium_run_days": med_median_run,
            "share_ks_between_0_and_0.9_percent": ks.get("share_ks_between_0_and_0.9_percent"),
        },
    })

    # 4. Rainfed assumption / few irrigation events
    events = ass.get("irrigation_event_days")
    total_irr = ass.get("irrigation_total_mm")
    f.append({
        "id": "water_balance_is_effectively_rainfed",
        "supported": bool(events is not None and events <= 3 and high_pct is not None and high_pct > 40),
        "statement": "Almost no irrigation is recorded, so the balance is effectively rainfed; depletion "
                     "sits at or near TAW through dry spells. If the orchard was irrigated, simulated stress "
                     "is overstated. The data cannot tell which.",
        "evidence": {
            "irrigation_event_days": events,
            "irrigation_total_mm": total_irr,
            "irrigation_event_dates": ass.get("irrigation_event_dates"),
            "rain_vs_etc_by_year_mm": ass.get("rain_vs_etc_by_year_mm"),
            "longest_stretch_days_without_1mm_rain": ass.get("longest_stretch_days_without_1mm_rain"),
        },
    })

    # 5. Seasonal / regime structure
    pure = summary.get("pure_month_share")
    f.append({
        "id": "labels_follow_season_and_long_regimes",
        "supported": bool(pure is not None and pure >= 0.6),
        "statement": "Labels are constant for months at a time and follow the wet/dry calendar, so a "
                     "model can score well by learning season/regime rather than day-level irrigation need.",
        "evidence": {
            "share_of_months_with_single_class": pure,
            "label_run_count": runs.get("run_count"),
            "longest_runs": runs.get("longest_runs"),
            "label_changes": trans.get("label_changes"),
            "seasonal_distribution": seasonal,
        },
    })

    # 6. Thresholds are not the main driver of the imbalance
    ks0 = ks.get("share_ks_exactly_0_percent")
    f.append({
        "id": "threshold_positions_are_not_the_primary_cause",
        "supported": bool(ks0 is not None and high_pct is not None and ks0 >= 0.5 * high_pct),
        "statement": "A large share of days have Ks exactly 0, so moving the Medium/High cut-off would "
                     "relabel few days; the imbalance comes from where the water balance sits, not the "
                     "threshold position.",
        "evidence": {"share_ks_exactly_0_percent": ks0, "high_percent": high_pct,
                     "share_ks_in_medium_band_percent": ks.get("share_ks_in_medium_band_percent")},
    })

    # 7. FAO-56 implementation facts (static, from reading the water-balance code)
    f.append({
        "id": "fao56_balance_structure_amplifies_saturation",
        "supported": bool((sat.get("diagnostic_unclipped_depletion") or {}).get("days_beyond_taw", 0) > 0),
        "statement": "Code review: the interpolated-Kc balance subtracts all rain and irrigation and adds full "
                     "unadjusted ETc (no Ks feedback, no runoff/effective-rainfall split), starts at field "
                     "capacity, and clips depletion to [0, TAW]. Under a dry/rainfed regime the balance "
                     "therefore spends long periods at the cap. These are existing model assumptions; this "
                     "audit does not change or judge them beyond noting the effect on labels.",
        "evidence": {
            "source": "src/water_balance/fao56_interpolated_kc_water_balance.py "
                      "(compute_interpolated_kc_water_balance)",
            "diagnostic_unclipped_depletion": sat.get("diagnostic_unclipped_depletion"),
            "first_label": summary.get("first_label"),
        },
    })

    # 8. Short record
    f.append({
        "id": "few_independent_regime_changes",
        "supported": bool((runs.get("run_count") or 0) <= 30),
        "statement": "Only a handful of label runs exist, so chronological evaluation folds mostly sample "
                     "one regime each and class support in test folds is unreliable.",
        "evidence": {"label_run_count": runs.get("run_count"),
                     "date_range": summary.get("date_range")},
    })
    return f


def build_recommendations(summary: dict) -> list[dict]:
    """Evidence-conditional recommendations. None of these are applied automatically."""
    dist = summary["class_distribution"]["classes"]
    med = dist.get("Medium", {}).get("percent") or 0
    sat_hi = summary["saturation"].get("percent_of_high_labels_at_cap") or 0
    events = summary["rain_irrigation_assumptions"].get("irrigation_event_days") or 0
    return [
        {
            "option": "Retain the current three-class surrogate target",
            "recommended": False,
            "reason": f"Medium is {med}% of labels and is a transient band; High is mostly a saturated state. "
                      "A 3-class model cannot be trained or validated meaningfully on this.",
        },
        {
            "option": "Switch to a binary task (High vs not High)",
            "recommended": False,
            "reason": "Reduces class count but still predicts a saturated, season-driven label; it would mostly "
                      "rediscover the wet/dry calendar. Acceptable only as an explicitly labelled demo.",
        },
        {
            "option": "Regress a continuous water-balance quantity (e.g. Ks or depletion fraction over a "
                      "3-7 day horizon) as an explicit FAO-56 emulator",
            "recommended": True,
            "reason": f"Avoids threshold artefacts, but {sat_hi}% of High labels sit on the TAW cap, so the "
                      "target is clipped; use a forecast horizon or change-in-depletion target and compare to a "
                      "persistence baseline. Because the target is computable directly from FAO-56, this shows "
                      "emulation skill only, not agronomic value.",
        },
        {
            "option": "Collect real-world observations (soil moisture, canopy/leaf-water status, grower irrigation log)",
            "recommended": True,
            "reason": "Highest priority. The only way to turn surrogate labels into validated ones; nothing in "
                      "the current data can substitute for it.",
        },
        {
            "option": "Add historically realistic irrigation information",
            "recommended": events <= 3,
            "reason": f"Only {events} irrigation event day(s) recorded (a 1 mm connectivity test). Obtain the "
                      "grower's actual irrigation history; do not infer or fabricate events to improve ML scores.",
        },
        {
            "option": "Review FAO-56 assumptions (rainfed balance, TAW cap, no Ks feedback on ETc, effective "
                      "rainfall, initial condition, soil and rooting parameters)",
            "recommended": True,
            "reason": "Months of Ks = 0 imply a tree at wilting point, which a surviving orchard makes doubtful; "
                      "this points to missing water inputs or parameters. Review separately with agronomic "
                      "input; this audit changes nothing.",
        },
    ]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def audit_labels(df: pd.DataFrame | None) -> tuple[dict, pd.DataFrame]:
    """Run the full audit. Returns (summary dict, per-date audit table)."""
    data = prepare_frame(df)
    runs = label_runs(data)
    monthly = monthly_distribution(data)
    summary = {
        "audit_type": "surrogate_label_quality",
        "label_column": LABEL,
        "label_type": "surrogate_rule_based",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "first_label": (data[LABEL].dropna().iloc[0] if data[LABEL].notna().any() else None),
        "date_range": (
            [data["date"].min().strftime("%Y-%m-%d"), data["date"].max().strftime("%Y-%m-%d")]
            if len(data) else None),
        "class_distribution": class_distribution(data[LABEL]),
        "monthly_distribution": monthly,
        "pure_month_share": pure_month_share(monthly),
        "seasonal_distribution": seasonal_distribution(data),
        "yearly_distribution": yearly_distribution(data),
        "stage_distribution": stage_distribution(data),
        "label_runs": run_summary(runs),
        "transitions": transition_analysis(data) if len(data) else {},
        "ks_relationship": ks_label_relationship(data),
        "depletion_relationship": depletion_label_relationship(data),
        "saturation": saturation_analysis(data),
        "rain_irrigation_assumptions": rain_irrigation_assumptions(data),
        "missing_values": missing_value_summary(data),
        "limitations": LIMITATIONS,
    }
    summary["findings"] = build_findings(summary)
    summary["recommendations"] = build_recommendations(summary)
    table = build_audit_table(data) if len(data) else pd.DataFrame()
    return summary, table


def run_label_audit(config=None) -> bool:
    """Read the ML dataset, run the audit and write both outputs."""
    config = config or get_config()
    data_path = config.path("ml_training_dataset_csv")
    csv_path = config.path("ml_label_audit_csv")
    json_path = config.path("ml_label_audit_summary_json")

    if not data_path.exists():
        print(f"\nML training dataset not found: {data_path}\n"
              "Run: python src/ml/build_ml_training_dataset.py")
        log.warning("Label audit skipped: dataset missing (%s)", data_path)
        return False

    summary, table = audit_labels(pd.read_csv(data_path))
    if table.empty:
        print("\nML training dataset has no usable dated rows; nothing to audit.")
        log.warning("Label audit skipped: no usable rows")
        return False

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(summary, indent=2, default=_json_default), encoding="utf-8")
    log.info("Label audit written: %d rows", len(table))
    _print_report(summary)
    print(f">>> Audit CSV:     {csv_path}")
    print(f">>> Audit summary: {json_path}")
    return True


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return str(o)


def _print_report(s: dict) -> None:
    cd = s["class_distribution"]
    print()
    print(f">>> Label audit: {cd['labelled_records']} labelled of {cd['total_records']} records, {s['date_range']}")
    print(">>> Classes: " + ", ".join(f"{c}={v['count']} ({v['percent']}%)" for c, v in cd["classes"].items()))
    sat = s["saturation"]
    print(f">>> Depletion at TAW cap (Ks=0): {sat.get('days_at_taw_cap')} days; "
          f"{sat.get('percent_of_high_labels_at_cap')}% of High labels; "
          f"longest run {sat.get('longest_continuous_cap_run_days')} days")
    print(f">>> Label runs: {s['label_runs']['run_count']}; longest: {s['label_runs']['longest_runs'][:2]}")
    print(f">>> Irrigation events recorded: {s['rain_irrigation_assumptions'].get('irrigation_event_days')}")
    for fnd in s["findings"]:
        print(f">>> [{'SUPPORTED' if fnd['supported'] else 'not supported'}] {fnd['id']}")
    print(">>> NOTE: labels are surrogate (FAO-56/rule-based), not field observations.")


if __name__ == "__main__":
    sys.exit(0 if run_label_audit() else 1)
