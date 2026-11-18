"""
AI/ML Advisory Preview page (read-only).

Shows the artifacts of the baseline surrogate-label irrigation-priority
classifier. No inference is made here and nothing is written to disk. The
labels come from FAO-56/rule-based logic, not field observations.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from app.theme import PALETTE, esc

SURROGATE_WARNING = (
    "This model is trained on surrogate FAO-56/rule-based labels, "
    "not field-observed irrigation outcomes."
)
DATASET_HINT = "Generate the training dataset locally with `python main.py --skip-soil-fetch`."
MODEL_HINT = "Train and evaluate the model locally with `python -m src.ml.train_irrigation_priority_model`."
GENERATE_HINT = f"{DATASET_HINT} {MODEL_HINT}"

SNAPSHOT_LABEL = "Published evaluation snapshot — training dataset not deployed"
MODEL_NOT_DEPLOYED = (
    "The trained model binary is not deployed. This page displays committed evaluation artifacts "
    "(metrics and feature importance) from the last published training run; no live inference is "
    "available here and no predictions are made."
)

LIMITATIONS = [
    "Labels are surrogate: they are derived from the FAO-56 water balance and rule-based advisory logic.",
    "There is no field validation (no soil-moisture sensors or observed irrigation outcomes).",
    "The chronological test split can be badly class-imbalanced.",
    "Accuracy can be misleading when the test window contains mostly one class.",
    "Feature importance is model-specific and not causal.",
]

TARGET_COLUMN = "target_irrigation_priority"


# ---------------------------------------------------------------------------
# Pure helpers (no Streamlit, no writes)
# ---------------------------------------------------------------------------

def load_metrics(path: "Path | str | None") -> dict | None:
    """Return the metrics dict, or None if the file is missing/unreadable."""
    if path is None or not Path(path).exists():
        return None
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def load_feature_importance(path: "Path | str | None", top_n: int = 15) -> pd.DataFrame:
    """Top-N features by importance; empty frame if missing/empty/malformed."""
    empty = pd.DataFrame(columns=["feature", "importance"])
    if path is None or not Path(path).exists():
        return empty
    try:
        df = pd.read_csv(path)
    except Exception:
        return empty
    if not {"feature", "importance"} <= set(df.columns) or df.empty:
        return empty
    df["importance"] = pd.to_numeric(df["importance"], errors="coerce")
    df = df.dropna(subset=["importance"])
    return df.sort_values("importance", ascending=False).head(top_n).reset_index(drop=True)


def summarize_training_dataset(path: "Path | str | None") -> dict | None:
    """Row count, date range and target distribution; None if unavailable."""
    if path is None or not Path(path).exists():
        return None
    try:
        df = pd.read_csv(path)
    except Exception:
        return None
    dates = pd.to_datetime(df["date"], errors="coerce").dropna() if "date" in df.columns else pd.Series(dtype="datetime64[ns]")
    dist = (
        df[TARGET_COLUMN].value_counts(dropna=False).rename_axis("class").reset_index(name="rows")
        if TARGET_COLUMN in df.columns else None
    )
    return {
        "rows": int(len(df)),
        "date_min": dates.min().strftime("%Y-%m-%d") if len(dates) else None,
        "date_max": dates.max().strftime("%Y-%m-%d") if len(dates) else None,
        "target_distribution": dist,
    }


def format_metrics_summary(metrics: dict | None) -> list[tuple[str, str]]:
    """(label, display value) pairs; missing keys show 'n/a'."""
    metrics = metrics or {}

    def num(key: str, nd: int = 3) -> str:
        v = metrics.get(key)
        return f"{v:.{nd}f}" if isinstance(v, (int, float)) else "n/a"

    def txt(key: str) -> str:
        v = metrics.get(key)
        return "n/a" if v in (None, "") else str(v)

    return [
        ("Model type", txt("model_type")),
        ("Label type", txt("label_type")),
        ("Train rows", txt("train_rows")),
        ("Test rows", txt("test_rows")),
        ("Feature count", txt("feature_count")),
        ("Accuracy", num("accuracy")),
        ("Balanced accuracy", num("balanced_accuracy")),
        ("Precision (macro)", num("precision_macro")),
        ("Recall (macro)", num("recall_macro")),
        ("F1 (macro)", num("f1_macro")),
        ("Trained at", txt("trained_at")),
    ]


def target_distribution_frame(metrics: dict | None) -> pd.DataFrame | None:
    dist = (metrics or {}).get("target_distribution")
    if not isinstance(dist, dict) or not dist:
        return None
    try:
        return pd.DataFrame(dist).fillna(0).astype(int).rename_axis("class").reset_index()
    except (ValueError, TypeError):
        return None


def classification_report_frame(metrics: dict | None) -> pd.DataFrame | None:
    rep = (metrics or {}).get("classification_report")
    if not isinstance(rep, dict) or not rep:
        return None
    rows = {k: v for k, v in rep.items() if isinstance(v, dict)}
    return pd.DataFrame(rows).T.round(3) if rows else None


def confusion_matrix_frame(metrics: dict | None) -> pd.DataFrame | None:
    cm = (metrics or {}).get("confusion_matrix")
    if not isinstance(cm, dict):
        return None
    labels, matrix = cm.get("labels"), cm.get("matrix")
    if not labels or not matrix:
        return None
    try:
        return pd.DataFrame(
            matrix,
            index=[f"actual: {l}" for l in labels],
            columns=[f"predicted: {l}" for l in labels],
        )
    except ValueError:
        return None


def _count(v) -> int | None:
    return int(v) if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else None


def _date_range(v) -> tuple[str, str] | None:
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        return None
    try:
        start, end = (pd.Timestamp(x) for x in v)
    except (ValueError, TypeError):
        return None
    if pd.isna(start) or pd.isna(end) or start > end:
        return None
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _split_distribution(dist, rows: int | None) -> dict[str, int] | None:
    """A class->count mapping, only if every count is valid and the total matches the stated row count."""
    if not isinstance(dist, dict) or not dist:
        return None
    counts = {str(k): _count(v) for k, v in dist.items()}
    if any(v is None for v in counts.values()):
        return None
    if rows is not None and sum(counts.values()) != rows:
        return None
    return counts


def _timestamp(v) -> datetime | None:
    if not isinstance(v, str):
        return None
    try:
        return datetime.fromisoformat(v)
    except ValueError:
        return None


def evaluation_snapshot(metrics: dict | None) -> dict | None:
    """Validated dataset details taken ONLY from what the committed metrics JSON states.

    Requires valid train and test sample counts; returns None otherwise. Date ranges and class
    distributions are included only when they are present and internally consistent. Nothing is
    reconstructed or inferred.
    """
    if not isinstance(metrics, dict):
        return None
    train_rows, test_rows = _count(metrics.get("train_rows")), _count(metrics.get("test_rows"))
    if not train_rows or not test_rows:
        return None
    dist = metrics.get("target_distribution")
    dist = dist if isinstance(dist, dict) else {}
    distribution = {}
    for split, rows in (("train", train_rows), ("test", test_rows)):
        counts = _split_distribution(dist.get(split), rows)
        if counts is not None:
            distribution[split] = counts
    return {
        "train_rows": train_rows,
        "test_rows": test_rows,
        "train_dates": _date_range(metrics.get("train_date_range")),
        "test_dates": _date_range(metrics.get("test_date_range")),
        "distribution": distribution,
        "trained_at": metrics.get("trained_at") if _timestamp(metrics.get("trained_at")) else None,
    }


def snapshot_distribution_frame(snapshot: dict | None) -> pd.DataFrame | None:
    dist = (snapshot or {}).get("distribution")
    if not dist:
        return None
    return pd.DataFrame(dist).fillna(0).astype(int).rename_axis("class").reset_index()


def stale_metrics_note(dataset_path: "Path | str | None", metrics: dict | None) -> str | None:
    """Note that the local dataset was rebuilt AFTER the published evaluation snapshot was trained.

    Needs two explicit timestamps: ``built_at`` in the dataset's metadata file and ``trained_at`` in
    the metrics. Observation dates are deliberately not compared: they measure data coverage, not
    when anything was built or trained. Returns None when either timestamp is missing, unparseable,
    or they are not comparable.
    """
    if dataset_path is None:
        return None
    path = Path(dataset_path)
    meta = load_metrics(path.with_name(path.stem + "_metadata.json"))
    built = _timestamp((meta or {}).get("built_at"))
    trained = _timestamp((metrics or {}).get("trained_at"))
    if built is None or trained is None or (built.tzinfo is None) != (trained.tzinfo is None):
        return None
    if built > trained:
        return (f"The training dataset was rebuilt ({built:%Y-%m-%d %H:%M}) after the evaluation metrics "
                f"were trained ({trained:%Y-%m-%d %H:%M}), so the metrics may not reflect the current "
                f"dataset. {MODEL_HINT}")
    return None


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

def render_ml_advisory_preview_page(
    model_path: Path,
    metrics_path: Path,
    importance_path: Path,
    dataset_path: Path,
) -> None:
    st.markdown(
        '<div class="mt-ai"><span class="mt-ai-badge">EXPERIMENTAL · SURROGATE LABELS</span>'
        '<div class="mt-title" style="margin-top:.5rem">AI/ML Advisory Preview</div>'
        f'<div class="mt-sub">{esc(SURROGATE_WARNING)} Read-only: no predictions are made on this page, '
        'and it is separate from the FAO-56 irrigation advisory.</div></div>',
        unsafe_allow_html=True,
    )
    st.info(SURROGATE_WARNING)

    # 1. Artifact status
    st.subheader("Model status")
    model_ok = Path(model_path).exists()
    c1, c2, c3 = st.columns(3)
    c1.metric("Model artifact", "Available (local)" if model_ok else "Not deployed")
    c2.metric("Metrics JSON", "Available" if Path(metrics_path).exists() else "Missing")
    c3.metric("Feature importance CSV", "Available" if Path(importance_path).exists() else "Missing")
    if not model_ok:
        st.info(MODEL_NOT_DEPLOYED)
    else:
        st.caption("Read-only: the local model binary is not used on this page; no predictions are made.")
    missing = [n for n, p in (("metrics JSON", metrics_path), ("feature importance CSV", importance_path))
               if not Path(p).exists()]
    if missing:
        st.warning(f"Missing evaluation artifact(s): {', '.join(missing)}. {MODEL_HINT}")

    # 2. Metrics
    metrics = load_metrics(metrics_path)
    st.subheader("Evaluation metrics (chronological hold-out)")
    if metrics is None:
        st.warning(f"Metrics not available. {MODEL_HINT}")
    else:
        pairs = format_metrics_summary(metrics)
        for start in range(0, len(pairs), 4):
            cols = st.columns(4)
            for col, (label, value) in zip(cols, pairs[start:start + 4]):
                col.metric(label, value)
        if metrics.get("test_set_note"):
            st.warning(metrics["test_set_note"])

        dist = target_distribution_frame(metrics)
        if dist is not None:
            st.markdown("**Target distribution (train / test)**")
            st.dataframe(dist, use_container_width=True, hide_index=True)

        report = classification_report_frame(metrics)
        if report is not None:
            st.markdown("**Classification report**")
            st.dataframe(report, use_container_width=True)

        cm = confusion_matrix_frame(metrics)
        if cm is not None:
            st.markdown("**Confusion matrix**")
            st.dataframe(cm, use_container_width=True)

    # 3. Feature importance
    st.subheader("Top feature importances")
    imp = load_feature_importance(importance_path, top_n=15)
    if imp.empty:
        st.warning(f"Feature importance not available. {MODEL_HINT}")
    else:
        fig = px.bar(
            imp.sort_values("importance"), x="importance", y="feature", orientation="h",
            title="Top 15 features (RandomForest impurity importance)",
            color_discrete_sequence=[PALETTE["purple"]],
        )
        fig.update_layout(yaxis_title=None, height=480)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Importance is model-specific and not causal.")

    # 4. Dataset status
    st.subheader("ML training dataset")
    ds = summarize_training_dataset(dataset_path)
    if ds is not None:
        d1, d2 = st.columns(2)
        d1.metric("Rows", ds["rows"])
        d2.metric("Date range", f"{ds['date_min'] or 'n/a'} to {ds['date_max'] or 'n/a'}")
        if ds["target_distribution"] is not None:
            st.markdown(f"**{TARGET_COLUMN} distribution**")
            st.dataframe(ds["target_distribution"], use_container_width=True, hide_index=True)
        note = stale_metrics_note(dataset_path, metrics)
        if note:
            st.warning(note)
    else:
        snap = evaluation_snapshot(metrics)
        if snap is None:
            st.warning("Training dataset not available and the published metrics do not state its sample "
                       f"counts. {DATASET_HINT}")
        else:
            st.info(f"**{SNAPSHOT_LABEL}.** These details come from the committed evaluation metrics, not "
                    f"from a dataset file. The raw dataset is intentionally not versioned. {DATASET_HINT}")
            t1, t2 = st.columns(2)
            t1.metric("Training samples", snap["train_rows"])
            t2.metric("Test samples", snap["test_rows"])
            if snap["train_dates"] or snap["test_dates"]:
                d1, d2 = st.columns(2)
                if snap["train_dates"]:
                    d1.metric("Training dates", " to ".join(snap["train_dates"]))
                if snap["test_dates"]:
                    d2.metric("Test dates", " to ".join(snap["test_dates"]))
            frame = snapshot_distribution_frame(snap)
            if frame is not None:
                st.markdown("**Class distribution (published, per split)**")
                st.dataframe(frame, use_container_width=True, hide_index=True)
            if snap["trained_at"]:
                st.caption(f"Evaluation snapshot trained at {snap['trained_at']}.")

    # 5. Limitations
    st.subheader("Limitations")
    st.warning("No field-observed ground truth exists. Metrics show how well the model reproduces "
               "rule-based labels, not operational predictive reliability.")
    for item in LIMITATIONS:
        st.markdown(f"- {item}")
