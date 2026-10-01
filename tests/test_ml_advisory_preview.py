"""
tests/test_ml_advisory_preview.py

Pure-helper tests for app.sections.ml_advisory_preview (read-only page).
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.sections.ml_advisory_preview import (
    classification_report_frame,
    confusion_matrix_frame,
    format_metrics_summary,
    load_feature_importance,
    load_metrics,
    summarize_training_dataset,
    target_distribution_frame,
)


def test_load_metrics_missing_file(tmp_path):
    assert load_metrics(tmp_path / "nope.json") is None
    assert load_metrics(None) is None


def test_load_metrics_bad_json(tmp_path):
    p = tmp_path / "m.json"
    p.write_text("{not json")
    assert load_metrics(p) is None


def test_load_feature_importance_missing_and_empty(tmp_path):
    assert load_feature_importance(tmp_path / "nope.csv").empty
    p = tmp_path / "e.csv"
    p.write_text("feature,importance\n")
    assert load_feature_importance(p).empty


def test_load_feature_importance_top_n(tmp_path):
    p = tmp_path / "i.csv"
    pd.DataFrame({"feature": [f"f{i}" for i in range(30)], "importance": range(30)}).to_csv(p, index=False)
    out = load_feature_importance(p, top_n=15)
    assert len(out) == 15
    assert out["feature"].iloc[0] == "f29"


def test_summarize_dataset_missing_file(tmp_path):
    assert summarize_training_dataset(tmp_path / "nope.csv") is None


def test_summarize_dataset(tmp_path):
    p = tmp_path / "d.csv"
    pd.DataFrame({
        "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "target_irrigation_priority": ["High", "High", "Low"],
    }).to_csv(p, index=False)
    s = summarize_training_dataset(p)
    assert s["rows"] == 3
    assert (s["date_min"], s["date_max"]) == ("2026-01-01", "2026-01-03")
    assert s["target_distribution"].set_index("class")["rows"]["High"] == 2


def test_metrics_formatting_handles_missing_keys():
    pairs = dict(format_metrics_summary({"accuracy": 0.98765, "model_type": "RF"}))
    assert pairs["Accuracy"] == "0.988"
    assert pairs["Model type"] == "RF"
    assert pairs["F1 (macro)"] == "n/a"
    assert pairs["Trained at"] == "n/a"
    assert all(v == "n/a" for v in dict(format_metrics_summary(None)).values())


def test_frames_handle_missing_and_present_keys():
    assert target_distribution_frame({}) is None
    assert classification_report_frame({}) is None
    assert confusion_matrix_frame({"confusion_matrix": {}}) is None
    m = {
        "target_distribution": {"train": {"High": 5, "Low": 2}, "test": {"High": 3}},
        "classification_report": {"High": {"precision": 1.0}, "accuracy": 0.9},
        "confusion_matrix": {"labels": ["High", "Low"], "matrix": [[3, 0], [0, 0]]},
    }
    assert target_distribution_frame(m).shape[0] == 2
    assert list(classification_report_frame(m).index) == ["High"]
    assert confusion_matrix_frame(m).shape == (2, 2)


def test_metrics_roundtrip_from_real_json(tmp_path):
    p = tmp_path / "m.json"
    p.write_text(json.dumps({"label_type": "surrogate_rule_based"}))
    assert load_metrics(p)["label_type"] == "surrogate_rule_based"


def test_dashboard_section_import():
    mod = importlib.import_module("app.sections.ml_advisory_preview")
    assert callable(mod.render_ml_advisory_preview_page)
    assert "surrogate" in mod.SURROGATE_WARNING
