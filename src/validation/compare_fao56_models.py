"""
Standalone comparison/validation report: constant-Kc FAO-56 vs
phenology-aware FAO-56 water balance.

WHAT THIS FILE DOES (and does NOT do):
  - Reads the two existing, already-built FAO-56 output CSVs:
      data/processed/muthukur_fao56_water_balance.csv            (constant Kc)
      data/processed/muthukur_fao56_phenology_water_balance.csv  (stage-aware Kc)
  - Joins them on `date` (inner join — only dates present in both files are
    compared).
  - Computes day-by-day differences (ETc, root-zone depletion, Ks, and
    whether the Low/Medium/High water-stress label changed) plus summary
    statistics, including a stage-wise breakdown.
  - Writes one new CSV:
      data/processed/muthukur_fao56_model_comparison.csv
  - Writes one new markdown summary:
      data/processed/muthukur_fao56_model_comparison_summary.md
  - Does NOT call any external API, does NOT touch main.py, does NOT modify
    src/pipeline/run_pipeline.py, the Streamlit dashboard, either existing
    FAO-56 script, or either existing FAO-56 output CSV's schema. It only
    reads the two CSVs that those scripts already produce, and writes two
    new files.

WHAT THIS IS, AND WHAT IT IS NOT
  This is a MODEL-TO-MODEL COMPARISON, not a validation against ground
  truth. It quantifies how much replacing a constant crop coefficient
  (Kc = 0.75 for the whole season) with a growth-stage-specific Kc changes
  the estimated crop water demand (ETc) and the resulting water-stress
  interpretation (Ks / Low-Medium-High level). It says nothing about which
  model is closer to what actually happened in a real orchard, because
  neither model has been checked against field soil-moisture sensors,
  irrigation records, or yield data yet. See "LIMITATIONS" below and in the
  generated markdown summary.

METHOD
  1. Load both CSVs, parse `date`.
  2. Rename each file's columns with a `constant_`/`phenology_` prefix so
     they can sit side by side after the join without colliding.
  3. Inner join on `date`.
  4. The constant-Kc file does not store Kc as a column (it is one constant
     read from configs/config.yaml -> fao56.kc_constant for the whole run),
     so `constant_kc` here is that same configured constant, broadcast to
     every row, for a fair side-by-side comparison against the phenology
     file's per-row `kc` (renamed `phenology_kc`).
  5. Compute `etc_difference` = phenology_etc - constant_etc (positive means
     the phenology-aware model estimates higher crop water demand that day),
     `etc_percent_difference` = etc_difference / constant_etc * 100, and the
     equivalent difference columns for root-zone depletion and Ks, plus a
     `stress_level_changed` boolean flag where the Low/Medium/High label
     differs between the two models.
  6. Aggregate into summary statistics (matched day count, date range, mean/
     mean-absolute/max ETc difference, percent of days the stress level
     changed, stage-wise average ETc difference, stage-wise stress-change
     counts, and the days with the single biggest ETc swings).

INPUT
  data/processed/muthukur_fao56_water_balance.csv
  data/processed/muthukur_fao56_phenology_water_balance.csv

OUTPUT
  data/processed/muthukur_fao56_model_comparison.csv
  data/processed/muthukur_fao56_model_comparison_summary.md

LIMITATIONS (also written into the markdown summary)
  - This is NOT ground-truth validation yet — it is a model-to-model
    comparison between two prototypes built by this same project.
  - The phenology-aware Kc values (configs/config.yaml ->
    fao56.phenology_kc_stages) are first-pass assumptions based on general
    mango/FAO-56 guidance, not locally calibrated for this orchard or
    cultivar.
  - No irrigation-event records are included in either model (both are
    rainfed-only depletion balances).
  - No field soil-moisture sensor data has been used to validate either
    model's depletion/Ks output.
  - No yield validation has been performed.

HOW TO USE THIS FILE
  Run after both FAO-56 outputs already exist (e.g. after
  `python main.py --skip-fetch`, which now regenerates the phenology-aware
  file automatically, or after running each FAO-56 script standalone):

      python src/validation/compare_fao56_models.py

  This is a standalone script only — it is not wired into main.py, the
  pipeline runner, or the dashboard. Nothing downstream depends on it yet.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src.utils.config import get_config
from src.utils.logger import get_logger

log = get_logger(__name__)

# Required columns this script needs from each input file. Kept local to
# this script (rather than added to src/utils/validation.py) since this is
# a standalone comparison report, not a pipeline-stage input/output check.
REQUIRED_CONSTANT_KC_COLUMNS = [
    "date",
    "et0_mm",
    "etc_mm",
    "root_zone_depletion_mm",
    "water_stress_coefficient_ks",
    "water_stress_level",
]

REQUIRED_PHENOLOGY_COLUMNS = [
    "date",
    "mango_stage",
    "kc",
    "et0_mm_day",
    "etc_mm_day",
    "root_zone_depletion_mm",
    "ks",
    "water_stress_level",
]


class MissingColumnsError(Exception):
    """Raised when an input CSV is missing a column this script needs."""


def _check_required_columns(df: pd.DataFrame, required: list[str], label: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise MissingColumnsError(
            f"{label} is missing required column(s): {missing}.\n"
            f"Columns present: {list(df.columns)}.\n"
            "This usually means the underlying FAO-56 script's output "
            "schema changed. This comparison script was not updated to "
            "match — re-check src/validation/compare_fao56_models.py."
        )


def _load_constant_kc_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Constant-Kc FAO-56 output not found: {path}\n"
            "Run python src/water_balance/fao56_water_balance.py first to create it."
        )
    df = pd.read_csv(path)
    _check_required_columns(df, REQUIRED_CONSTANT_KC_COLUMNS, "Constant-Kc FAO-56 CSV")
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def _load_phenology_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Phenology-aware FAO-56 output not found: {path}\n"
            "Run python src/water_balance/fao56_phenology_water_balance.py "
            "first to create it (or python main.py --skip-fetch, which now "
            "regenerates it automatically if its own inputs exist)."
        )
    df = pd.read_csv(path)
    _check_required_columns(df, REQUIRED_PHENOLOGY_COLUMNS, "Phenology-aware FAO-56 CSV")
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def build_comparison_table(
    constant_df: pd.DataFrame, phenology_df: pd.DataFrame, kc_constant: float
) -> pd.DataFrame:
    """Join the two FAO-56 outputs on date and compute comparison columns."""

    constant_renamed = constant_df[REQUIRED_CONSTANT_KC_COLUMNS].rename(
        columns={
            "et0_mm": "constant_et0",
            "etc_mm": "constant_etc",
            "root_zone_depletion_mm": "constant_root_zone_depletion",
            "water_stress_coefficient_ks": "constant_ks",
            "water_stress_level": "constant_water_stress_level",
        }
    )

    phenology_renamed = phenology_df[REQUIRED_PHENOLOGY_COLUMNS].rename(
        columns={
            "kc": "phenology_kc",
            "et0_mm_day": "phenology_et0",
            "etc_mm_day": "phenology_etc",
            "root_zone_depletion_mm": "phenology_root_zone_depletion",
            "ks": "phenology_ks",
            "water_stress_level": "phenology_water_stress_level",
        }
    )

    merged = constant_renamed.merge(phenology_renamed, on="date", how="inner")
    merged = merged.sort_values("date").reset_index(drop=True)

    merged.insert(1, "mango_stage", merged.pop("mango_stage"))
    merged.insert(2, "constant_kc", kc_constant)

    merged["etc_difference"] = merged["phenology_etc"] - merged["constant_etc"]
    merged["etc_percent_difference"] = (
        merged["etc_difference"] / merged["constant_etc"].replace(0, pd.NA) * 100
    )
    merged["depletion_difference"] = (
        merged["phenology_root_zone_depletion"] - merged["constant_root_zone_depletion"]
    )
    merged["ks_difference"] = merged["phenology_ks"] - merged["constant_ks"]
    merged["stress_level_changed"] = (
        merged["constant_water_stress_level"] != merged["phenology_water_stress_level"]
    )

    column_order = [
        "date",
        "mango_stage",
        "constant_kc",
        "phenology_kc",
        "constant_et0",
        "phenology_et0",
        "constant_etc",
        "phenology_etc",
        "etc_difference",
        "etc_percent_difference",
        "constant_root_zone_depletion",
        "phenology_root_zone_depletion",
        "depletion_difference",
        "constant_ks",
        "phenology_ks",
        "ks_difference",
        "constant_water_stress_level",
        "phenology_water_stress_level",
        "stress_level_changed",
    ]
    return merged[column_order]


def summarize_comparison(comparison: pd.DataFrame) -> dict:
    """Compute the summary statistics described in the module docstring."""

    abs_etc_diff = comparison["etc_difference"].abs()
    biggest_idx = abs_etc_diff.idxmax()

    biggest_change_dates = (
        comparison.reindex(abs_etc_diff.sort_values(ascending=False).index)
        .head(5)[["date", "mango_stage", "etc_difference", "stress_level_changed"]]
    )

    stage_avg_etc_diff = (
        comparison.groupby("mango_stage")["etc_difference"].mean().sort_values(ascending=False)
    )
    stage_stress_change_counts = comparison.groupby("mango_stage")["stress_level_changed"].sum()
    stage_day_counts = comparison.groupby("mango_stage").size()

    return {
        "matched_days": len(comparison),
        "date_min": comparison["date"].min(),
        "date_max": comparison["date"].max(),
        "mean_etc_difference": comparison["etc_difference"].mean(),
        "mean_abs_etc_difference": abs_etc_diff.mean(),
        "max_etc_difference": comparison.loc[biggest_idx, "etc_difference"],
        "max_etc_difference_date": comparison.loc[biggest_idx, "date"],
        "percent_days_stress_changed": comparison["stress_level_changed"].mean() * 100,
        "stage_avg_etc_diff": stage_avg_etc_diff,
        "stage_stress_change_counts": stage_stress_change_counts,
        "stage_day_counts": stage_day_counts,
        "biggest_change_dates": biggest_change_dates,
    }


def _print_console_summary(summary: dict, output_csv: Path) -> None:
    print()
    print("=" * 70)
    print("FAO-56 model comparison: constant-Kc vs phenology-aware")
    print("=" * 70)
    print(f"Matched days:                  {summary['matched_days']}")
    print(
        f"Date range:                    "
        f"{summary['date_min'].date()} to {summary['date_max'].date()}"
    )
    print(f"Mean ETc difference (mm/day):  {summary['mean_etc_difference']:+.3f}")
    print(f"Mean |ETc difference| (mm/day):{summary['mean_abs_etc_difference']:.3f}")
    print(
        f"Max ETc difference (mm/day):   {summary['max_etc_difference']:+.3f} "
        f"on {summary['max_etc_difference_date'].date()}"
    )
    print(f"Days with stress-level change: {summary['percent_days_stress_changed']:.1f}%")
    print()
    print("Stage-wise average ETc difference (phenology - constant, mm/day):")
    for stage, value in summary["stage_avg_etc_diff"].items():
        days = summary["stage_day_counts"][stage]
        print(f"  {stage:<35} {value:+.3f}  ({days} days)")
    print()
    print("Stage-wise stress-level-changed day counts:")
    for stage, count in summary["stage_stress_change_counts"].items():
        days = summary["stage_day_counts"][stage]
        print(f"  {stage:<35} {count} / {days} days")
    print()
    print("Biggest single-day ETc swings:")
    for _, row in summary["biggest_change_dates"].iterrows():
        flag = " (stress level changed)" if row["stress_level_changed"] else ""
        print(f"  {row['date'].date()}  {row['mango_stage']:<35} {row['etc_difference']:+.3f} mm/day{flag}")
    print()
    print(f"Saved comparison table to: {output_csv}")
    print()
    print("Reminder: this is a model-to-model comparison, not ground-truth")
    print("validation. See the generated markdown summary for full limitations.")


def _write_markdown_summary(
    summary: dict,
    comparison: pd.DataFrame,
    summary_md_path: Path,
    constant_kc_csv: Path,
    phenology_csv: Path,
) -> None:
    lines = []
    lines.append("# FAO-56 Model Comparison: Constant-Kc vs Phenology-Aware")
    lines.append("")
    lines.append(
        "A model-to-model comparison of the two FAO-56 soil-water balance "
        "prototypes built so far for this project, quantifying how much "
        "replacing a constant crop coefficient with a growth-stage-specific "
        "one changes estimated crop water demand and water-stress "
        "interpretation."
    )
    lines.append("")
    lines.append("## Input Files")
    lines.append("")
    lines.append(f"- Constant-Kc FAO-56 output: `{constant_kc_csv}`")
    lines.append(f"- Phenology-aware FAO-56 output: `{phenology_csv}`")
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append(
        "The two CSVs above are joined on `date` (inner join — only dates "
        "present in both files are compared). The constant-Kc file's "
        "single configured Kc value is broadcast to every row as "
        "`constant_kc`, alongside the phenology-aware file's per-day "
        "`phenology_kc`. Differences are computed as **phenology minus "
        "constant** for ETc, root-zone depletion, and Ks, plus a flag for "
        "whether the Low/Medium/High water-stress label changed between "
        "the two models. Full column-by-column detail is in "
        f"`{comparison_csv_name(summary)}`."
    )
    lines.append("")
    lines.append("## Key Findings")
    lines.append("")
    lines.append(f"- Matched days compared: **{summary['matched_days']}**")
    lines.append(
        f"- Date range: **{summary['date_min'].date()}** to "
        f"**{summary['date_max'].date()}**"
    )
    lines.append(
        f"- Mean ETc difference (phenology - constant): "
        f"**{summary['mean_etc_difference']:+.3f} mm/day**"
    )
    lines.append(
        f"- Mean absolute ETc difference: "
        f"**{summary['mean_abs_etc_difference']:.3f} mm/day**"
    )
    lines.append(
        f"- Largest single-day ETc difference: "
        f"**{summary['max_etc_difference']:+.3f} mm/day** on "
        f"**{summary['max_etc_difference_date'].date()}**"
    )
    lines.append(
        f"- Days where the Low/Medium/High water-stress label changed: "
        f"**{summary['percent_days_stress_changed']:.1f}%** of matched days"
    )
    lines.append("")
    lines.append("### Biggest single-day ETc swings")
    lines.append("")
    lines.append("| Date | Mango stage | ETc difference (mm/day) | Stress level changed |")
    lines.append("|---|---|---|---|")
    for _, row in summary["biggest_change_dates"].iterrows():
        lines.append(
            f"| {row['date'].date()} | {row['mango_stage']} | "
            f"{row['etc_difference']:+.3f} | {'Yes' if row['stress_level_changed'] else 'No'} |"
        )
    lines.append("")
    lines.append("## Stage-Wise Comparison")
    lines.append("")
    lines.append("| Mango stage | Days | Avg ETc difference (mm/day) | Days stress level changed |")
    lines.append("|---|---|---|---|")
    for stage in summary["stage_day_counts"].index:
        lines.append(
            f"| {stage} | {summary['stage_day_counts'][stage]} | "
            f"{summary['stage_avg_etc_diff'][stage]:+.3f} | "
            f"{summary['stage_stress_change_counts'][stage]} |"
        )
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append("- This is **not ground-truth validation** yet — it is a model-to-model")
    lines.append("  comparison between two prototypes built by this same project.")
    lines.append("- The phenology-aware Kc values are first-pass assumptions based on")
    lines.append("  general mango/FAO-56 guidance, not locally calibrated for this orchard")
    lines.append("  or cultivar.")
    lines.append("- No irrigation-event records are included in either model (both are")
    lines.append("  rainfed-only depletion balances).")
    lines.append("- No field soil-moisture sensor data has been used to validate either")
    lines.append("  model's depletion/Ks output.")
    lines.append("- No yield validation has been performed.")
    lines.append("")

    summary_md_path.parent.mkdir(parents=True, exist_ok=True)
    summary_md_path.write_text("\n".join(lines), encoding="utf-8")


def comparison_csv_name(summary: dict) -> str:
    # Small helper so the markdown's "Method" section can reference the CSV
    # filename without passing the path through every function signature.
    return "muthukur_fao56_model_comparison.csv"


def build_fao56_model_comparison() -> bool:
    """
    Build the constant-Kc vs phenology-aware FAO-56 comparison table and
    markdown summary.

    Returns True on success, False if an input is missing/malformed —
    always with a clear, friendly explanation printed first.
    """

    config = get_config()
    constant_kc_csv = config.path("fao56_water_balance_csv")
    phenology_csv = config.path("fao56_phenology_water_balance_csv")
    output_csv = config.path("fao56_model_comparison_csv")
    summary_md_path = config.path("fao56_model_comparison_summary_md")

    print("Starting FAO-56 model comparison (constant-Kc vs phenology-aware)...")
    print(f"Required input 1 (constant-Kc FAO-56 output):    {constant_kc_csv}")
    print(f"Required input 2 (phenology-aware FAO-56 output): {phenology_csv}")
    print(f"Output (comparison CSV):                          {output_csv}")
    print(f"Output (markdown summary):                        {summary_md_path}")

    try:
        constant_df = _load_constant_kc_csv(constant_kc_csv)
    except (FileNotFoundError, MissingColumnsError) as exc:
        print()
        print("FAILED: could not load the constant-Kc FAO-56 output.")
        print(str(exc))
        return False

    try:
        phenology_df = _load_phenology_csv(phenology_csv)
    except (FileNotFoundError, MissingColumnsError) as exc:
        print()
        print("FAILED: could not load the phenology-aware FAO-56 output.")
        print(str(exc))
        return False

    log.info("Loaded %d constant-Kc rows from %s", len(constant_df), constant_kc_csv)
    log.info("Loaded %d phenology-aware rows from %s", len(phenology_df), phenology_csv)

    fao56_settings = config._raw.get("fao56", {})
    kc_constant = fao56_settings.get("kc_constant", 0.75)

    comparison = build_comparison_table(constant_df, phenology_df, kc_constant)

    if comparison.empty:
        print()
        print(
            "No overlapping dates found between the constant-Kc output "
            f"({constant_df['date'].min().date()} to {constant_df['date'].max().date()}) "
            "and the phenology-aware output "
            f"({phenology_df['date'].min().date()} to {phenology_df['date'].max().date()}). "
            "Nothing to compare."
        )
        log.warning("FAO-56 model comparison skipped: no overlapping dates between the two inputs.")
        return False

    summary = summarize_comparison(comparison)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(output_csv, index=False)

    _write_markdown_summary(summary, comparison, summary_md_path, constant_kc_csv, phenology_csv)

    log.info("Computed FAO-56 model comparison for %d matched days.", summary["matched_days"])
    log.info(
        "Mean ETc difference=%.3f mm/day, mean abs=%.3f mm/day, max=%.3f mm/day on %s",
        summary["mean_etc_difference"],
        summary["mean_abs_etc_difference"],
        summary["max_etc_difference"],
        summary["max_etc_difference_date"],
    )
    log.info("Stress-level changed on %.1f%% of matched days.", summary["percent_days_stress_changed"])
    log.info("Wrote FAO-56 model comparison table to %s", output_csv)
    log.info("Wrote FAO-56 model comparison summary to %s", summary_md_path)

    _print_console_summary(summary, output_csv)
    print(f"Saved markdown summary to: {summary_md_path}")
    return True


def main():
    log.info("Building FAO-56 model comparison (constant-Kc vs phenology-aware)...")
    success = build_fao56_model_comparison()

    if success:
        log.info("FAO-56 model comparison completed successfully.")
    else:
        log.info("FAO-56 model comparison did not complete. See messages above.")


if __name__ == "__main__":
    main()
