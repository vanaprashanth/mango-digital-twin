"""
AI/ML Advisory Preview page (read-only).

Shows the artifacts of the baseline surrogate-label irrigation-priority
classifier. No inference is made here and nothing is written to disk. The
labels come from FAO-56/rule-based logic, not field observations.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

SURROGATE_WARNING = (
    "This model is trained on surrogate FAO-56/rule-based labels, "
    "not field-observed irrigation outcomes."
)
GENERATE_HINT = "Run python main.py --skip-soil-fetch to generate ML artifacts."

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


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

def render_ml_advisory_preview_page(
    model_path: Path,
    metrics_path: Path,
    importance_path: Path,
    dataset_path: Path,
) -> None:
    st.title("AI/ML Advisory Preview")
    st.info(SURROGATE_WARNING)
    st.caption(
        "Surrogate-label ML prototype. Read-only: no predictions are made on this page."
    )

    # 1. Artifact status
    st.subheader("Model status")
    c1, c2, c3 = st.columns(3)
    for col, label, p in (
        (c1, "Model artifact", model_path),
        (c2, "Metrics JSON", metrics_path),
        (c3, "Feature importance CSV", importance_path),
    ):
        col.metric(label, "Available" if Path(p).exists() else "Missing")
    if not all(Path(p).exists() for p in (model_path, metrics_path, importance_path)):
        st.warning(GENERATE_HINT)

    # 2. Metrics
    metrics = load_metrics(metrics_path)
    st.subheader("Evaluation metrics (chronological hold-out)")
    if metrics is None:
        st.warning(f"Metrics not available. {GENERATE_HINT}")
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
        st.warning(f"Feature importance not available. {GENERATE_HINT}")
    else:
        fig = px.bar(
            imp.sort_values("importance"), x="importance", y="feature", orientation="h",
            title="Top 15 features (RandomForest impurity importance)",
        )
        fig.update_layout(yaxis_title=None, height=480)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Importance is model-specific and not causal.")

    # 4. Dataset status
    st.subheader("ML training dataset")
    ds = summarize_training_dataset(dataset_path)
    if ds is None:
        st.warning(f"Training dataset not available. {GENERATE_HINT}")
    else:
        d1, d2 = st.columns(2)
        d1.metric("Rows", ds["rows"])
        d2.metric("Date range", f"{ds['date_min'] or 'n/a'} to {ds['date_max'] or 'n/a'}")
        if ds["target_distribution"] is not None:
            st.markdown(f"**{TARGET_COLUMN} distribution**")
            st.dataframe(ds["target_distribution"], use_container_width=True, hide_index=True)

    # 5. Limitations
    st.subheader("Limitations")
    for item in LIMITATIONS:
        st.markdown(f"- {item}")
