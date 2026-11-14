"""
src/ml/evaluation_manifest.py

Support for the manual "ML Training and Evaluation" GitHub Actions workflow.

Two sub-commands (run as ``python -m src.ml.evaluation_manifest <cmd>``):

  check     Verify the committed upstream snapshots needed to build the ML
            dataset exist and are non-empty. Exits 1 with a clear message if
            not (no silent fallbacks).
  manifest  Write a small, reviewable evaluation manifest JSON summarising a
            run: run date, git commit, dataset cutoff, rows, target
            distribution, model configuration, backtest and audit headlines
            and the surrogate-label warning.

This module only reads outputs; it never trains, retrains or promotes
anything, and it does not modify published metrics.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_config  # noqa: E402

LABEL_TYPE = "surrogate_rule_based"
NO_GROUND_TRUTH_WARNING = (
    "Labels are surrogate (FAO-56 / rule-based) and are NOT validated against "
    "field observations. There is no field-observed ground truth. Metrics "
    "describe how well a model reproduces the rule-based labels, not real "
    "irrigation need. Accuracy on single-class test periods is not evidence of "
    "generalisation. Review before promoting any result to the dashboard."
)

# Config keys that must exist (non-empty) before the dataset can be built.
REQUIRED_UPSTREAM_KEYS = (
    "combined_feature_table_csv",
    "fao56_interpolated_kc_water_balance_csv",
)
# Used by the builder when present; absence is reported but not fatal.
OPTIONAL_UPSTREAM_KEYS = ("forecast_risk_csv", "irrigation_events_csv")


def check_upstream(config=None) -> tuple[list[str], list[str]]:
    """Return (problems, notes). Any problem means the evaluation must not run."""
    config = config or get_config()
    problems, notes = [], []
    for key in REQUIRED_UPSTREAM_KEYS:
        p = Path(config.path(key))
        if not p.exists():
            problems.append(f"Required upstream file missing: {p} ({key})")
        elif p.stat().st_size == 0:
            problems.append(f"Required upstream file is empty: {p} ({key})")
        else:
            lines = sum(1 for _ in p.open("rb"))
            if lines < 2:
                problems.append(f"Required upstream file has no data rows: {p} ({key})")
    for key in OPTIONAL_UPSTREAM_KEYS:
        p = Path(config.path(key))
        if not p.exists():
            notes.append(f"Optional upstream file not found: {p} ({key})")
    return problems, notes


def _read_json(path: Path) -> dict | None:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _git_commit() -> str | None:
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT,
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _backtest_headline(bt: dict | None) -> dict | None:
    if not bt:
        return None
    folds = []
    for f in bt.get("folds", []):
        folds.append({
            "fold": f.get("fold"),
            "train_period": [f.get("train_start"), f.get("train_end")],
            "test_period": [f.get("test_start"), f.get("test_end")],
            "test_support": f.get("test_class_distribution"),
            "classes_absent_from_test": f.get("classes_absent_from_test"),
            "majority_class_baseline_prediction": f.get("majority_class_baseline_prediction"),
            "model": {k: f["model"].get(k) for k in
                      ("accuracy", "balanced_accuracy", "f1_macro_fixed", "f1_macro_present")},
            "majority_baseline": {k: f["baseline"].get(k) for k in
                                  ("accuracy", "balanced_accuracy", "f1_macro_fixed", "f1_macro_present")},
        })
    return {
        "evaluation": bt.get("evaluation"),
        "n_folds": bt.get("n_folds"),
        "classes": bt.get("classes"),
        "folds_with_absent_test_classes": bt.get("folds_with_absent_test_classes"),
        "folds_with_single_class_test": bt.get("folds_with_single_class_test"),
        "mean_model_metrics": bt.get("mean_model_metrics"),
        "mean_majority_baseline_metrics": bt.get("mean_baseline_metrics"),
        "interpretation_note": bt.get("interpretation_note"),
        "folds": folds,
    }


def _audit_headline(audit: dict | None) -> dict | None:
    if not audit:
        return None
    runs = audit.get("label_runs") or {}
    sat = audit.get("saturation") or {}
    return {
        "label_run_count": runs.get("run_count"),
        "longest_label_runs": runs.get("longest_runs"),
        "saturation": {k: sat.get(k) for k in (
            "available", "days_at_taw_cap", "percent_of_records",
            "percent_of_high_labels_at_cap", "longest_continuous_cap_run_days")},
        "supported_findings": [f.get("id") for f in audit.get("findings", []) if f.get("supported")],
        "limitations": audit.get("limitations"),
    }


def _model_headline(metrics: dict | None) -> dict | None:
    if not metrics:
        return None
    return {
        "model_type": metrics.get("model_type"),
        "train_rows": metrics.get("train_rows"),
        "test_rows": metrics.get("test_rows"),
        "train_period": metrics.get("train_date_range"),
        "test_period": metrics.get("test_date_range"),
        "accuracy": metrics.get("accuracy"),
        "balanced_accuracy": metrics.get("balanced_accuracy"),
        "f1_macro_present_classes": metrics.get("f1_macro"),
        "macro_average_classes": metrics.get("macro_average_classes"),
        "test_set_note": metrics.get("test_set_note"),
        "trained_at": metrics.get("trained_at"),
    }


def build_manifest(config=None, now: datetime | None = None) -> dict:
    """Assemble the manifest from the outputs of this run (missing parts -> None)."""
    config = config or get_config()
    meta = _read_json(config.path("ml_training_dataset_metadata_json"))
    metrics = _read_json(config.path("ml_model_metrics_json"))
    backtest = _read_json(config.path("ml_backtest_summary_json"))
    audit = _read_json(config.path("ml_label_audit_summary_json"))
    now = now or datetime.now(timezone.utc)

    dist = (meta or {}).get("target_distribution", {}) or {}
    classes = sorted((metrics or {}).get("macro_average_classes") or
                     (backtest or {}).get("classes") or [])
    support = (meta or {}).get("per_class_support") or {}
    all_classes = sorted(set(classes) | set(support))
    missing_classes = [c for c in all_classes if not support.get(c)]

    return {
        "manifest_type": "ml_evaluation",
        "label_type": LABEL_TYPE,
        "run_date": now.date().isoformat(),
        "run_at_utc": now.isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "dataset": {
            "cutoff_date": (meta or {}).get("dataset_cutoff_date"),
            "date_range": (meta or {}).get("date_range"),
            "row_count": (meta or {}).get("row_count"),
            "feature_count": (meta or {}).get("feature_count"),
            "target_distribution": dist,
            "per_class_support": support,
            "classes_with_no_support": missing_classes,
        },
        "model_configuration": {
            "model_type": (metrics or {}).get("model_type"),
            "n_estimators": 200,
            "class_weight": "balanced",
            "random_state": 42,
            "preprocessing": "median imputer (numeric); most-frequent + one-hot (categorical)",
            "split": "chronological 80/20 holdout plus expanding-window backtest",
        },
        "trained_model": _model_headline(metrics),
        "backtest": _backtest_headline(backtest),
        "label_audit": _audit_headline(audit),
        "published_metrics_unchanged": True,
        "promotion": "NOT promoted. This run only uploads artifacts for review; "
                     "published dashboard metrics remain those committed on master.",
        "warning": NO_GROUND_TRUTH_WARNING,
    }


def write_manifest(config=None, out_path: Path | None = None) -> Path:
    config = config or get_config()
    manifest = build_manifest(config)
    out = Path(out_path) if out_path else Path(config.path("ml_training_dataset_metadata_json")).with_name(
        "muthukur_ml_evaluation_manifest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else ""
    if cmd == "check":
        problems, notes = check_upstream()
        for n in notes:
            print(f"NOTE: {n}")
        if problems:
            print("ERROR: cannot run ML evaluation - required upstream data is unavailable.")
            for p in problems:
                print(f"ERROR: {p}")
            print("ERROR: Run the daily data refresh (or `python main.py`) and commit the "
                  "upstream snapshots first. No stale or invented fallback will be used.")
            return 1
        print("Upstream data check passed.")
        return 0
    if cmd == "manifest":
        out = write_manifest(out_path=Path(argv[1]) if len(argv) > 1 else None)
        print(f"Evaluation manifest written to: {out}")
        return 0
    print("usage: python -m src.ml.evaluation_manifest {check|manifest [out_path]}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
