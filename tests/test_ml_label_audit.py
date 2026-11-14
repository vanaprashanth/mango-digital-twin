"""
tests/test_ml_label_audit.py

Tests for src.ml.audit_label_quality (diagnostic audit of surrogate labels).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ml.audit_label_quality import (
    LABEL,
    audit_labels,
    class_distribution,
    ks_label_relationship,
    ks_to_label,
    label_runs,
    missing_value_summary,
    monthly_distribution,
    prepare_frame,
    run_label_audit,
    saturation_analysis,
    seasonal_distribution,
    unclipped_depletion,
)

TAW, RAW = 150.0, 75.0


def _frame(labels, start="2025-01-01", ks=None, depletion=None):
    n = len(labels)
    ks = np.array(ks if ks is not None else [1.0] * n, dtype=float)
    dep = np.array(depletion if depletion is not None else [10.0] * n, dtype=float)
    return pd.DataFrame({
        "date": pd.date_range(start, periods=n).strftime("%Y-%m-%d"),
        LABEL: labels,
        "ks": ks,
        "root_zone_depletion_mm": dep,
        "taw_mm": TAW,
        "raw_mm": RAW,
        "etc_mm_day": 4.0,
        "rainfall_mm": 0.0,
        "irrigation_mm": 0.0,
        "water_input_mm": 0.0,
        "mango_stage": "Flowering",
    })


# 1. Class counts and percentages ---------------------------------------------

def test_class_counts_and_percentages():
    d = class_distribution(pd.Series(["High"] * 6 + ["Low"] * 3 + ["Medium"]))
    assert d["labelled_records"] == 10 and d["missing_labels"] == 0
    assert d["classes"]["High"] == {"count": 6, "percent": 60.0}
    assert d["classes"]["Low"]["percent"] == 30.0
    assert d["classes"]["Medium"]["count"] == 1


# 2. Missing labels -----------------------------------------------------------

def test_missing_labels_are_counted_not_included_in_percentages():
    d = class_distribution(pd.Series(["High", None, "Low", np.nan]))
    assert d["total_records"] == 4 and d["labelled_records"] == 2 and d["missing_labels"] == 2
    assert d["classes"]["High"]["percent"] == 50.0


# 3. Monthly / seasonal distributions -----------------------------------------

def test_monthly_and_seasonal_distributions():
    df = prepare_frame(_frame(["Low"] * 31 + ["High"] * 28 + ["Medium"] * 3, start="2025-01-01"))
    m = monthly_distribution(df)
    assert m["2025-01"] == {"Low": 31, "Medium": 0, "High": 0}
    assert m["2025-02"]["High"] == 28
    assert m["2025-03"]["Medium"] == 3
    s = seasonal_distribution(df)
    assert s["Winter (Jan-Feb)"]["Low"] == 31 and s["Winter (Jan-Feb)"]["High"] == 28
    assert s["Summer (Mar-May)"]["Medium"] == 3


# 4. Consecutive runs ---------------------------------------------------------

def test_consecutive_label_runs():
    df = prepare_frame(_frame(["Low"] * 3 + ["High"] * 5 + ["Low"] * 2 + ["Medium"]))
    runs = label_runs(df)
    assert runs["label"].tolist() == ["Low", "High", "Low", "Medium"]
    assert runs["length"].tolist() == [3, 5, 2, 1]
    assert runs["start"].iloc[1] == pd.Timestamp("2025-01-04")
    assert runs["end"].iloc[1] == pd.Timestamp("2025-01-08")


def test_missing_label_breaks_a_run():
    df = prepare_frame(_frame(["High", "High", None, "High"]))
    assert label_runs(df)["length"].tolist() == [2, 1]


# 5. Missing Ks / depletion ---------------------------------------------------

def test_missing_ks_and_depletion_do_not_break_audit():
    df = _frame(["Low", "High", "High", "Medium"], ks=[1.0, np.nan, 0.0, 0.7],
                depletion=[5.0, np.nan, 150.0, 100.0])
    summary, table = audit_labels(df)
    assert summary["ks_relationship"]["ks_missing"] == 1
    assert summary["depletion_relationship"]["depletion_missing"] == 1
    assert len(table) == 4
    mv = summary["missing_values"]["missing_by_column"]
    assert mv["ks"]["missing"] == 1 and mv["root_zone_depletion_mm"]["missing"] == 1


def test_audit_without_ks_columns():
    df = _frame(["Low", "High"]).drop(columns=["ks", "root_zone_depletion_mm", "taw_mm", "raw_mm"])
    summary, table = audit_labels(df)
    assert summary["ks_relationship"] == {"available": False}
    assert summary["saturation"] == {"available": False}
    assert len(table) == 2


def test_ks_threshold_mapping_and_match_rate():
    assert [ks_to_label(k) for k in (1.0, 0.9, 0.89, 0.6, 0.59, 0.0)] == \
        ["Low", "Low", "Medium", "Medium", "High", "High"]
    df = prepare_frame(_frame(["Low", "Medium", "High", "High"], ks=[1.0, 0.7, 0.0, 0.95]))
    # last row is deliberately inconsistent with the Ks rule
    assert ks_label_relationship(df)["label_matches_ks_thresholds_percent"] == 75.0


# 6. Saturation diagnostics ---------------------------------------------------

def test_saturation_counts_cap_days_and_high_share():
    labels = ["Low"] * 2 + ["High"] * 4
    df = prepare_frame(_frame(labels, ks=[1, 1, 0, 0, 0, 0.3],
                              depletion=[5, 5, TAW, TAW, TAW, 120]))
    sat = saturation_analysis(df)
    assert sat["days_at_taw_cap"] == 3
    assert sat["percent_of_high_labels_at_cap"] == 75.0
    assert sat["longest_continuous_cap_run_days"] == 3


def test_unclipped_depletion_ignores_cap_but_floors_at_zero():
    out = unclipped_depletion(np.array([0, 0, 0, 20.0]), np.array([100.0, 100.0, 100.0, 0.0]))
    assert out.tolist() == [100.0, 200.0, 300.0, 280.0]       # not capped at TAW
    assert unclipped_depletion(np.array([50.0]), np.array([1.0]))[0] == 0.0


# 7. Empty datasets -----------------------------------------------------------

def test_empty_and_none_datasets():
    for empty in (None, pd.DataFrame(), pd.DataFrame({"date": [], LABEL: []})):
        summary, table = audit_labels(empty)
        assert summary["class_distribution"]["labelled_records"] == 0
        assert summary["date_range"] is None
        assert table.empty
        assert summary["findings"][0]["id"] == "no_labels"
    assert missing_value_summary(pd.DataFrame())["records"] == 0


# 8. Dates --------------------------------------------------------------------

def test_dates_are_parsed_sorted_and_invalid_dates_dropped():
    df = pd.DataFrame({
        "date": ["2025-03-02", "not-a-date", "2025-03-01", None],
        LABEL: ["High", "Low", "Low", "Low"],
    })
    out = prepare_frame(df)
    assert out["date"].dt.strftime("%Y-%m-%d").tolist() == ["2025-03-01", "2025-03-02"]
    assert out[LABEL].tolist() == ["Low", "High"]


# 9. Findings are evidence-driven, not unconditional ---------------------------

def test_findings_not_supported_on_balanced_non_saturated_data():
    labels = ["Low", "Medium", "High"] * 40
    ks = [1.0, 0.75, 0.3] * 40
    dep = [10.0, 95.0, 120.0] * 40                 # never at the cap
    summary, _ = audit_labels(_frame(labels, ks=ks, depletion=dep))
    by_id = {f["id"]: f for f in summary["findings"]}
    assert by_id["high_class_dominated_by_depletion_saturation"]["supported"] is False
    assert by_id["medium_class_is_a_narrow_transition_band"]["supported"] is False
    assert by_id["labels_follow_season_and_long_regimes"]["supported"] is False


def test_findings_supported_on_saturated_imbalanced_data():
    labels = ["Low"] * 20 + ["High"] * 100 + ["Medium"] * 5
    ks = [1.0] * 20 + [0.0] * 100 + [0.7] * 5
    dep = [10.0] * 20 + [TAW] * 100 + [100.0] * 5
    summary, _ = audit_labels(_frame(labels, ks=ks, depletion=dep))
    by_id = {f["id"]: f for f in summary["findings"]}
    assert by_id["high_class_dominated_by_depletion_saturation"]["supported"] is True
    assert by_id["medium_class_is_a_narrow_transition_band"]["supported"] is True
    assert by_id["threshold_positions_are_not_the_primary_cause"]["supported"] is True
    assert "recommendations" in summary and not summary["recommendations"][0]["recommended"]


def test_summary_states_surrogate_and_limitations():
    summary, _ = audit_labels(_frame(["Low", "High"]))
    assert summary["label_type"] == "surrogate_rule_based"
    assert any("surrogate" in l.lower() for l in summary["limitations"])


# 10. Output generation -------------------------------------------------------

def _config(tmp_path, df):
    data = tmp_path / "ds.csv"
    if df is not None:
        df.to_csv(data, index=False)
    paths = {
        "ml_training_dataset_csv": data,
        "ml_label_audit_csv": tmp_path / "out" / "audit.csv",
        "ml_label_audit_summary_json": tmp_path / "out" / "summary.json",
    }
    return SimpleNamespace(path=lambda k: paths[k]), paths


def test_output_generation(tmp_path):
    cfg, paths = _config(tmp_path, _frame(["Low"] * 5 + ["High"] * 5))
    assert run_label_audit(cfg) is True
    table = pd.read_csv(paths["ml_label_audit_csv"])
    assert len(table) == 10
    for col in ("date", "surrogate_label", "ks", "root_zone_depletion_mm", "mango_stage",
                "at_taw_cap", "depletion_unclipped_mm", "label_matches_ks_rule", "run_id"):
        assert col in table.columns
    summary = json.loads(paths["ml_label_audit_summary_json"].read_text())
    for key in ("class_distribution", "seasonal_distribution", "label_runs",
                "limitations", "findings", "recommendations"):
        assert key in summary
    assert summary["label_runs"]["run_count"] == 2


def test_run_audit_skips_when_dataset_missing_or_empty(tmp_path):
    cfg, paths = _config(tmp_path, None)
    assert run_label_audit(cfg) is False
    pd.DataFrame({"date": [], LABEL: []}).to_csv(paths["ml_training_dataset_csv"], index=False)
    assert run_label_audit(cfg) is False
    assert not paths["ml_label_audit_summary_json"].exists()
