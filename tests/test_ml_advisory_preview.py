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


# ---------------------------------------------------------------------------
# Deployment fix: dataset not deployed / model binary not deployed
# ---------------------------------------------------------------------------

import pytest
from streamlit.testing.v1 import AppTest

from app.sections import ml_advisory_preview as page

REAL_METRICS = {
    "model_type": "RandomForestClassifier", "label_type": "surrogate_rule_based",
    "train_rows": 542, "test_rows": 136,
    "train_date_range": ["2025-01-01", "2026-06-26"], "test_date_range": ["2026-06-27", "2026-11-09"],
    "target_distribution": {"train": {"High": 321, "Low": 198, "Medium": 23},
                            "test": {"High": 91, "Low": 26, "Medium": 19}},
    "trained_at": "2026-11-14T09:17:53", "accuracy": 0.86,
    "confusion_matrix": {"labels": ["High", "Low", "Medium"], "matrix": [[89, 2, 0], [0, 26, 0], [15, 4, 0]]},
}


def _render(tmp_path, metrics=None, raw_metrics=None, dataset=False, model=False, dataset_meta=None):
    """Run the real page against temp paths (the Streamlit Cloud layout: only committed artifacts exist)."""
    paths = {k: tmp_path / n for k, n in (("model", "m.joblib"), ("metrics", "metrics.json"),
                                          ("imp", "imp.csv"), ("data", "ml_training_dataset.csv"))}
    if raw_metrics is not None:
        paths["metrics"].write_text(raw_metrics)
    elif metrics is not None:
        paths["metrics"].write_text(json.dumps(metrics))
    pd.DataFrame({"feature": ["a", "b"], "importance": [0.6, 0.4]}).to_csv(paths["imp"], index=False)
    if model:
        paths["model"].write_bytes(b"x")
    if dataset:
        pd.DataFrame({"date": ["2026-11-01", "2026-11-09"], "target_irrigation_priority": ["High", "Low"]}
                     ).to_csv(paths["data"], index=False)
    if dataset_meta is not None:
        (tmp_path / "ml_training_dataset_metadata.json").write_text(json.dumps(dataset_meta))
    script = (
        "from pathlib import Path\n"
        "from app.sections.ml_advisory_preview import render_ml_advisory_preview_page\n"
        f"render_ml_advisory_preview_page(Path({str(paths['model'])!r}), Path({str(paths['metrics'])!r}), "
        f"Path({str(paths['imp'])!r}), Path({str(paths['data'])!r}))\n"
    )
    at = AppTest.from_string(script, default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at


def _text(at):
    parts = [e.value for e in list(at.warning) + list(at.info) + list(at.markdown) + list(at.caption)]
    parts += [f"{m.label}={m.value}" for m in at.metric]
    return "\n".join(str(p) for p in parts)


def _warnings(at):
    return " ".join(str(e.value) for e in at.warning)


# --- missing CSV + valid metrics (Streamlit Cloud) ---------------------------------------------------------

def test_missing_csv_with_valid_metrics_shows_the_published_snapshot_without_the_false_warning(tmp_path):
    at = _render(tmp_path, REAL_METRICS)
    text, warns = _text(at), _warnings(at)
    assert "Published evaluation snapshot — training dataset not deployed" in text
    assert "Training samples=542" in text and "Test samples=136" in text          # shown separately
    assert "Training dates=2025-01-01 to 2026-06-26" in text and "Test dates=2026-06-27 to 2026-11-09" in text
    assert "Training dataset not available" not in warns
    frame = page.snapshot_distribution_frame(page.evaluation_snapshot(REAL_METRICS))
    assert frame.set_index("class").loc["Medium"].tolist() == [23, 19]            # train, test


def test_present_csv_keeps_the_existing_dataset_summary(tmp_path):
    at = _render(tmp_path, REAL_METRICS, dataset=True)
    text = _text(at)
    assert "Rows=2" in text and "Date range=2026-11-01 to 2026-11-09" in text
    assert page.SNAPSHOT_LABEL not in text and "Training dataset not available" not in _warnings(at)


# --- missing / malformed / partial metrics ------------------------------------------------------------------

@pytest.mark.parametrize("raw", [None, "{not json", "[1, 2]"])
def test_missing_or_malformed_metrics_keep_an_accurate_warning_and_invent_nothing(tmp_path, raw):
    at = _render(tmp_path, raw_metrics=raw)
    warns, text = _warnings(at), _text(at)
    assert "Training dataset not available" in warns and "do not state its sample counts" in warns
    assert page.SNAPSHOT_LABEL not in text and "Training samples" not in text
    assert "python main.py --skip-soil-fetch" in warns


def test_partial_metrics_show_only_what_is_explicit(tmp_path):
    at = _render(tmp_path, {"train_rows": 100, "test_rows": 25})                  # no dates, no distribution
    text = _text(at)
    assert "Training samples=100" in text and "Test samples=25" in text
    assert "Training dates" not in text and "Test dates" not in text
    assert "Class distribution (published" not in text and "trained at" not in text


def test_snapshot_validation_rejects_inconsistent_details():
    assert page.evaluation_snapshot({"train_rows": 10}) is None                   # test count missing
    assert page.evaluation_snapshot({"train_rows": 0, "test_rows": 5}) is None
    assert page.evaluation_snapshot({"train_rows": True, "test_rows": 5}) is None
    assert page.evaluation_snapshot({"train_rows": "10", "test_rows": 5}) is None
    snap = page.evaluation_snapshot({
        "train_rows": 10, "test_rows": 5,
        "train_date_range": ["2026-02-01", "2026-01-01"],                         # reversed
        "test_date_range": ["bad", "2026-03-01"],
        "target_distribution": {"train": {"High": 9}, "test": {"High": 3, "Low": 2}},   # train sum != rows
        "trained_at": "not-a-time"})
    assert snap["train_dates"] is None and snap["test_dates"] is None
    assert snap["distribution"] == {"test": {"High": 3, "Low": 2}} and snap["trained_at"] is None


# --- stale-metrics note ------------------------------------------------------------------------------------

def test_stale_note_needs_both_timestamps_and_a_newer_dataset(tmp_path):
    data = tmp_path / "ml_training_dataset.csv"
    metrics = {"trained_at": "2026-11-14T09:17:53"}
    assert page.stale_metrics_note(data, metrics) is None                          # no metadata file
    (tmp_path / "ml_training_dataset_metadata.json").write_text(json.dumps({"built_at": "2026-11-14T11:08:21"}))
    note = page.stale_metrics_note(data, metrics)
    assert note and "rebuilt" in note and "python -m src.ml.train_irrigation_priority_model" in note
    assert page.stale_metrics_note(data, {}) is None                               # no trained_at
    assert page.stale_metrics_note(data, {"trained_at": "2026-11-15T00:00:00"}) is None   # metrics newer
    assert page.stale_metrics_note(data, {"trained_at": "2026-11-14T09:17:53+00:00"}) is None   # not comparable
    (tmp_path / "ml_training_dataset_metadata.json").write_text("{bad")
    assert page.stale_metrics_note(data, metrics) is None


def test_observation_dates_alone_never_trigger_a_stale_note(tmp_path):
    # the dataset's latest date (2026-11-09) is after the test-window start; that is not evidence of staleness
    at = _render(tmp_path, REAL_METRICS, dataset=True)
    assert "rebuilt" not in _warnings(at)
    other = tmp_path / "with_build_timestamp"
    other.mkdir()
    at = _render(other, REAL_METRICS, dataset=True, dataset_meta={"built_at": "2026-11-14T11:08:21"})
    assert "rebuilt (2026-11-14 11:08)" in _warnings(at)


# --- model binary ------------------------------------------------------------------------------------------

def test_missing_model_binary_is_explained_and_never_presented_as_live(tmp_path):
    at = _render(tmp_path, REAL_METRICS)
    text = _text(at)
    assert "Model artifact=Not deployed" in text
    assert "trained model binary is not deployed" in text and "no live inference" in text
    assert "Model artifact=Available" not in text
    assert "Run python main.py" not in _warnings(at)                              # the old misleading hint


def test_local_model_binary_is_still_not_used_for_inference(tmp_path):
    at = _render(tmp_path, REAL_METRICS, model=True)
    text = _text(at)
    assert "Model artifact=Available (local)" in text and "no predictions are made" in text
    assert "trained model binary is not deployed" not in text


def test_setup_hints_name_the_real_entry_points():
    assert "python main.py --skip-soil-fetch" in page.DATASET_HINT
    assert "python -m src.ml.train_irrigation_priority_model" in page.MODEL_HINT
    assert "--skip-soil-fetch" in (PROJECT_ROOT / "main.py").read_text(encoding="utf-8")
    assert (PROJECT_ROOT / "src" / "ml" / "train_irrigation_priority_model.py").is_file()
    assert "main.py" not in page.MODEL_HINT                                       # main.py does not train the model
