"""
tests/test_ml_evaluation_workflow.py

Static checks of the manual ML evaluation workflow plus the preflight/manifest
helper it uses.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ml import evaluation_manifest as em  # noqa: E402

WF_DIR = PROJECT_ROOT / ".github" / "workflows"
ML_WF = WF_DIR / "ml-training-evaluation.yml"
DAILY_WF = WF_DIR / "daily-data-refresh.yml"


@pytest.fixture(scope="module")
def wf():
    return yaml.safe_load(ML_WF.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def steps(wf):
    return wf["jobs"]["evaluate"]["steps"]


def _triggers(wf):
    return wf.get("on", wf.get(True))      # YAML 1.1 parses bare `on` as True


def _run_text(step):
    return step.get("run", "")


def _index(steps, needle):
    for i, s in enumerate(steps):
        if needle in _run_text(s):
            return i
    raise AssertionError(f"no step runs {needle!r}")


def test_name_and_manual_trigger(wf):
    assert wf["name"] == "ML Training and Evaluation"
    assert "workflow_dispatch" in _triggers(wf)


def test_no_schedule_or_other_triggers(wf):
    trig = _triggers(wf)
    assert "schedule" not in trig and "push" not in trig and "pull_request" not in trig
    assert "cron" not in ML_WF.read_text(encoding="utf-8")


def test_read_only_permissions_and_ubuntu_python312(wf, steps):
    assert wf["permissions"] == {"contents": "read"}
    assert wf["jobs"]["evaluate"]["runs-on"] == "ubuntu-latest"
    py = next(s for s in steps if str(s.get("uses", "")).startswith("actions/setup-python"))
    assert str(py["with"]["python-version"]) == "3.12"


def test_installs_project_dependencies(steps):
    assert any("pip install -r requirements.txt" in _run_text(s) for s in steps)


def test_preflight_check_precedes_dataset_build(steps):
    assert _index(steps, "evaluation_manifest check") < _index(steps, "build_ml_training_dataset")


def test_dataset_precedes_training_precedes_backtest_then_audit(steps):
    d = _index(steps, "build_ml_training_dataset")
    t = _index(steps, "train_irrigation_priority_model")
    b = _index(steps, "backtest_irrigation_priority_model")
    a = _index(steps, "audit_label_quality")
    assert d < t < b < a


def test_audit_executes(steps):
    assert any("src.ml.audit_label_quality" in _run_text(s) for s in steps)


def test_manifest_written_before_upload(steps):
    m = _index(steps, "evaluation_manifest manifest")
    up = next(i for i, s in enumerate(steps) if str(s.get("uses", "")).startswith("actions/upload-artifact"))
    assert m < up


def test_artifacts_uploaded_with_retention_and_expected_files(steps):
    up = next(s for s in steps if str(s.get("uses", "")).startswith("actions/upload-artifact"))
    assert up["with"]["retention-days"] == 14
    gather = "\n".join(_run_text(s) for s in steps)
    for name in ("muthukur_ml_model_metrics.json", "muthukur_ml_feature_importance.csv",
                 "muthukur_ml_backtest_folds.csv", "muthukur_ml_backtest_summary.json",
                 "muthukur_ml_label_audit_summary.json",
                 "muthukur_ml_training_dataset_metadata.json",
                 "muthukur_ml_evaluation_manifest.json"):
        assert name in gather


def test_full_dataset_and_model_binary_not_uploaded(steps):
    up = next(s for s in steps if str(s.get("uses", "")).startswith("actions/upload-artifact"))
    assert up["with"]["path"].strip() == "ml_evaluation_artifacts/"
    gather = "\n".join(_run_text(s) for s in steps)
    assert "muthukur_ml_training_dataset.csv" not in gather
    assert ".joblib" not in gather and "models/" not in gather


def test_no_commit_push_or_git_write(steps):
    text = ML_WF.read_text(encoding="utf-8")
    for forbidden in ("git commit", "git push", "git add", "git config", "contents: write"):
        assert forbidden not in text
    checkout = next(s for s in steps if str(s.get("uses", "")).startswith("actions/checkout"))
    assert checkout["with"]["persist-credentials"] is False


def test_no_gee_credentials_or_full_pipeline(steps):
    text = ML_WF.read_text(encoding="utf-8")
    assert "GEE_SERVICE_ACCOUNT_KEY" not in text and "secrets." not in text
    assert "main.py" not in text


def test_existing_daily_workflow_unchanged():
    """Compare against the committed version; the daily refresh must not be touched."""
    head = subprocess.run(
        ["git", "show", "HEAD:.github/workflows/daily-data-refresh.yml"],
        cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    if head.returncode != 0:
        pytest.skip("git history unavailable")
    assert yaml.safe_load(DAILY_WF.read_text(encoding="utf-8")) == yaml.safe_load(head.stdout)
    daily = yaml.safe_load(DAILY_WF.read_text(encoding="utf-8"))
    assert "schedule" in _triggers(daily) and daily["permissions"] == {"contents": "write"}


# --- preflight: missing upstream data fails clearly --------------------------

def _cfg(tmp_path, feat=True, fao=True, empty=False):
    paths = {
        "combined_feature_table_csv": tmp_path / "feat.csv",
        "fao56_interpolated_kc_water_balance_csv": tmp_path / "fao.csv",
        "forecast_risk_csv": tmp_path / "fc.csv",
        "irrigation_events_csv": tmp_path / "ev.csv",
        "ml_training_dataset_metadata_json": tmp_path / "meta.json",
        "ml_model_metrics_json": tmp_path / "metrics.json",
        "ml_backtest_summary_json": tmp_path / "bt.json",
        "ml_label_audit_summary_json": tmp_path / "audit.json",
    }
    body = "" if empty else "date,x\n2025-01-01,1\n"
    if feat:
        paths["combined_feature_table_csv"].write_text(body)
    if fao:
        paths["fao56_interpolated_kc_water_balance_csv"].write_text(body)
    return SimpleNamespace(path=lambda k: paths[k]), paths


def test_check_passes_with_upstream_present(tmp_path):
    cfg, _ = _cfg(tmp_path)
    problems, notes = em.check_upstream(cfg)
    assert problems == [] and len(notes) == 2          # optional files reported, not fatal


def test_check_fails_clearly_when_upstream_missing(tmp_path):
    cfg, _ = _cfg(tmp_path, feat=False)
    problems, _ = em.check_upstream(cfg)
    assert len(problems) == 1 and "missing" in problems[0] and "combined_feature_table_csv" in problems[0]


def test_check_fails_on_empty_or_header_only_files(tmp_path):
    cfg, _ = _cfg(tmp_path, empty=True)
    assert len(em.check_upstream(cfg)[0]) == 2
    cfg2, paths = _cfg(tmp_path)
    paths["fao56_interpolated_kc_water_balance_csv"].write_text("date,x\n")
    assert any("no data rows" in p for p in em.check_upstream(cfg2)[0])


def test_cli_check_exit_code_and_message(monkeypatch, capsys, tmp_path):
    cfg, _ = _cfg(tmp_path, fao=False)
    monkeypatch.setattr(em, "get_config", lambda: cfg)
    assert em.main(["check"]) == 1
    out = capsys.readouterr().out
    assert "ERROR" in out and "no stale or invented fallback" in out.lower()
    cfg_ok, _ = _cfg(tmp_path)
    monkeypatch.setattr(em, "get_config", lambda: cfg_ok)
    assert em.main(["check"]) == 0


def test_workflow_fails_fast_on_check_step(steps):
    """The check step is a plain `run` (no continue-on-error), so a non-zero exit fails the job."""
    step = steps[_index(steps, "evaluation_manifest check")]
    assert "continue-on-error" not in step
    for s in steps:
        assert not s.get("continue-on-error")


# --- manifest ---------------------------------------------------------------

def test_manifest_contents(tmp_path):
    cfg, paths = _cfg(tmp_path)
    paths["ml_training_dataset_metadata_json"].write_text(json.dumps({
        "dataset_cutoff_date": "2026-11-09", "date_range": ["2025-01-01", "2026-11-09"],
        "row_count": 678, "feature_count": 30,
        "target_distribution": {"target_irrigation_priority": {"High": 400, "Low": 278}},
        "per_class_support": {"High": 400, "Low": 278},
    }))
    paths["ml_model_metrics_json"].write_text(json.dumps({
        "model_type": "RandomForestClassifier", "macro_average_classes": ["High", "Low", "Medium"],
        "train_rows": 542, "test_rows": 136, "accuracy": 0.9, "balanced_accuracy": 0.8, "f1_macro": 0.7,
    }))
    paths["ml_backtest_summary_json"].write_text(json.dumps({
        "n_folds": 1, "classes": ["High", "Low", "Medium"],
        "mean_model_metrics": {}, "mean_baseline_metrics": {},
        "folds": [{"fold": 1, "train_start": "a", "train_end": "b", "test_start": "c", "test_end": "d",
                   "test_class_distribution": {"High": 5}, "classes_absent_from_test": ["Low", "Medium"],
                   "majority_class_baseline_prediction": "High",
                   "model": {"accuracy": 1, "balanced_accuracy": 1, "f1_macro_fixed": 0.3, "f1_macro_present": 1},
                   "baseline": {"accuracy": 1, "balanced_accuracy": 1, "f1_macro_fixed": 0.3, "f1_macro_present": 1}}],
    }))
    paths["ml_label_audit_summary_json"].write_text(json.dumps({
        "label_runs": {"run_count": 18, "longest_runs": []},
        "saturation": {"available": True, "days_at_taw_cap": 279},
        "findings": [{"id": "x", "supported": True}, {"id": "y", "supported": False}],
        "limitations": ["surrogate"],
    }))
    m = em.build_manifest(cfg)
    assert m["label_type"] == "surrogate_rule_based"
    assert m["dataset"]["cutoff_date"] == "2026-11-09" and m["dataset"]["row_count"] == 678
    assert m["dataset"]["per_class_support"] == {"High": 400, "Low": 278}
    assert m["dataset"]["classes_with_no_support"] == ["Medium"]
    assert m["model_configuration"]["n_estimators"] == 200
    fold = m["backtest"]["folds"][0]
    assert fold["classes_absent_from_test"] == ["Low", "Medium"]
    assert "f1_macro_fixed" in fold["model"] and "f1_macro_present" in fold["model"]
    assert fold["majority_baseline"]["accuracy"] == 1
    assert m["label_audit"]["saturation"]["days_at_taw_cap"] == 279
    assert m["label_audit"]["supported_findings"] == ["x"]
    assert m["published_metrics_unchanged"] is True
    assert "ground truth" in m["warning"].lower()


def test_manifest_tolerates_missing_outputs(tmp_path):
    cfg, _ = _cfg(tmp_path)
    m = em.build_manifest(cfg)
    assert m["backtest"] is None and m["label_audit"] is None and m["dataset"]["row_count"] is None
    out = em.write_manifest(cfg, tmp_path / "m.json")
    assert json.loads(out.read_text())["label_type"] == "surrogate_rule_based"
