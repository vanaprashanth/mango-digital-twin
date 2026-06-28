"""
Standalone mango phenology calendar script.

WHAT THIS FILE DOES (and does NOT do):
  - Reads the existing combined weather + soil + vegetation feature table
    (data/processed/muthukur_combined_feature_table.csv) ONLY to discover
    the historical date range already used elsewhere in this project — it
    does not read or depend on any weather/soil/vegetation values from that
    file.
  - Assigns one approximate mango growth stage to every date in that range,
    using a simple, fixed seasonal calendar for Andhra Pradesh / South
    India.
  - Writes one new CSV:
        data/processed/muthukur_mango_phenology_calendar.csv
  - It does NOT call any external API, does NOT touch main.py, does NOT
    change the Streamlit dashboard, and does NOT modify the FAO-56
    water-balance script or its crop coefficient (Kc). It only reads one
    CSV's date column and writes one new CSV.

IMPORTANT, BEGINNER-FRIENDLY DISCLAIMERS (please read before trusting this):
  1. This is a SIMPLIFIED REGIONAL phenology calendar — a first-version,
     rule-of-thumb seasonal calendar for mango in Andhra Pradesh / South
     India, built from general agronomy references, not from this specific
     orchard.
  2. It is NOT yet calibrated to a specific mango cultivar (e.g. Banganapalli,
     Totapuri, Alphonso/Benishan all differ somewhat in bloom/harvest
     timing). "Mango" here means a generic South Indian mango calendar.
  3. It does NOT yet use any field observations (no actual bloom dates,
     fruit-set dates, or harvest dates from this orchard have been
     recorded or used). Every date is assigned a stage purely from the
     calendar day-of-year, regardless of the year's actual weather.
  4. It will LATER be used to make the FAO-56 crop coefficient (Kc) and the
     existing irrigation/heat/disease risk thresholds stage-aware (see
     ROADMAP.md Phase 5) — but that wiring has NOT happened yet. Today,
     this script's output is not read by any other script.

WHY A FIXED CALENDAR (NOT WEATHER-DRIVEN) FOR THIS FIRST VERSION
  Real mango phenology timing shifts year to year with temperature and
  rainfall (e.g. a warm winter can pull flowering earlier). Modeling that
  properly needs accumulated-temperature ("growing degree day") logic and
  field-validated bloom dates, neither of which exist yet for this project.
  This first version intentionally uses a fixed calendar so the phenology
  layer can be reviewed and corrected easily, before any weather-driven
  logic is layered on top of it later.

STAGE BOUNDARIES USED IN THIS SCRIPT
  The task that requested this script suggested these approximate,
  overlapping month ranges (typical of general mango agronomy references):

      Rest / vegetative phase ............. June to September
      Flower induction / pre-flowering ..... October to December
      Flowering ............................ January to February
      Fruit set ............................. February to March
      Fruit development ..................... March to May
      Maturity / harvest ..................... May to June

  Because a calendar date can only belong to one stage, the overlaps above
  (Jan-Feb vs Feb-Mar, Mar-May vs May-Jun, and the May/June vs June/Sept
  boundary) are resolved with a single explicit cutover day per boundary,
  chosen as a simple midpoint within the overlapping month. This is a
  DOCUMENTED ASSUMPTION, not a precise agronomic finding:

      Jan 1   - Feb 15  : Flowering
      Feb 16  - Mar 15  : Fruit set
      Mar 16  - May 15  : Fruit development
      May 16  - Jun 15  : Maturity / harvest
      Jun 16  - Sep 30  : Rest / vegetative phase
      Oct 1   - Dec 31  : Flower induction / pre-flowering

  These six ranges are non-overlapping and cover all 365/366 days of the
  year. Leap years (Feb 29) fall inside the "Flowering" range and are
  handled the same as any other February date.

INPUT
  data/processed/muthukur_combined_feature_table.csv (date column only)

OUTPUT
  data/processed/muthukur_mango_phenology_calendar.csv, with one row per
  date and these columns:
      date                          - calendar date (YYYY-MM-DD)
      month                         - calendar month number (1-12)
      day_of_year                  - day of year (1-366)
      mango_stage                   - short stage name
      stage_description             - one-sentence plain-language description
      water_sensitivity             - Low / Medium / High
      heat_sensitivity              - Low / Medium / High
      disease_sensitivity           - Low / Medium / High
      recommended_monitoring_focus  - what to watch for during this stage

HOW TO USE THIS FILE
  Run after the combined feature table has been built at least once (only
  its date range is needed):

      python src/phenology/mango_phenology_calendar.py

  This is a standalone script only — it is not wired into main.py, the
  FAO-56 water-balance script, or the dashboard. Nothing downstream depends
  on it yet.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validation import MissingColumnsError, validate_phenology_output

log = get_logger(__name__)


# ---------------------------------------------------------------------
# Stage definitions
# ---------------------------------------------------------------------
# Each entry is (month, day) marking the FIRST day of that stage. Stages
# are checked in this order; a date belongs to the stage whose start date
# is the latest one on or before that date (wrapping around the new year
# for January/February, which start the list).
#
# These sensitivity ratings (Low/Medium/High) are a documented, simplified
# first-pass judgment call for this project based on general mango
# agronomy knowledge, not a calibrated model:
#   - water_sensitivity: how much a water deficit during this stage is
#     expected to hurt the tree/crop (e.g. fruit development is very
#     sensitive to water stress; the rest phase tolerates it better).
#   - heat_sensitivity: how much unusually high temperatures during this
#     stage are expected to cause stress or yield/quality loss.
#   - disease_sensitivity: how favorable this stage is for fungal/disease
#     pressure, mostly driven by typical humidity/rainfall overlap with
#     flowering and fruit set.
PHENOLOGY_STAGES = [
    {
        "start_month": 1,
        "start_day": 1,
        "mango_stage": "Flowering",
        "stage_description": (
            "Trees are in bloom; flower panicles are open and pollination is "
            "occurring. This is a short, sensitive window for the whole "
            "season's crop."
        ),
        "water_sensitivity": "Medium",
        "heat_sensitivity": "Medium",
        "disease_sensitivity": "High",
        "recommended_monitoring_focus": (
            "Watch for unseasonal rain or high humidity (anthracnose / powdery "
            "mildew risk on flowers) and avoid waterlogging around the root zone."
        ),
    },
    {
        "start_month": 2,
        "start_day": 16,
        "mango_stage": "Fruit set",
        "stage_description": (
            "Pollinated flowers are developing into small fruitlets; a large "
            "share of fruitlets will naturally drop, but stress can increase "
            "drop further."
        ),
        "water_sensitivity": "High",
        "heat_sensitivity": "High",
        "disease_sensitivity": "Medium",
        "recommended_monitoring_focus": (
            "Watch for excessive fruitlet drop, maintain steady (not excessive) "
            "soil moisture, and monitor for early heat spikes."
        ),
    },
    {
        "start_month": 3,
        "start_day": 16,
        "mango_stage": "Fruit development",
        "stage_description": (
            "Retained fruit are actively growing in size; this stage drives most "
            "of the season's final yield and fruit quality."
        ),
        "water_sensitivity": "High",
        "heat_sensitivity": "High",
        "disease_sensitivity": "Low",
        "recommended_monitoring_focus": (
            "Prioritize consistent irrigation scheduling and monitor for peak "
            "summer heat stress affecting fruit sizing."
        ),
    },
    {
        "start_month": 5,
        "start_day": 16,
        "mango_stage": "Maturity / harvest",
        "stage_description": (
            "Fruit are reaching full size and ripening; harvest typically "
            "occurs during this window."
        ),
        "water_sensitivity": "Medium",
        "heat_sensitivity": "Medium",
        "disease_sensitivity": "Low",
        "recommended_monitoring_focus": (
            "Track fruit maturity indicators and plan harvest timing; avoid "
            "water stress that could affect final fruit quality."
        ),
    },
    {
        "start_month": 6,
        "start_day": 16,
        "mango_stage": "Rest / vegetative phase",
        "stage_description": (
            "Post-harvest recovery and vegetative growth (new shoots/leaves); "
            "the tree is rebuilding reserves for the next flowering cycle."
        ),
        "water_sensitivity": "Low",
        "heat_sensitivity": "Low",
        "disease_sensitivity": "Medium",
        "recommended_monitoring_focus": (
            "Monitor vegetative flush health and watch for monsoon-season "
            "fungal/bacterial disease pressure."
        ),
    },
    {
        "start_month": 10,
        "start_day": 1,
        "mango_stage": "Flower induction / pre-flowering",
        "stage_description": (
            "Trees are transitioning toward bud differentiation ahead of "
            "flowering; mild, controlled moisture stress is often associated "
            "with better flower induction."
        ),
        "water_sensitivity": "Medium",
        "heat_sensitivity": "Low",
        "disease_sensitivity": "Low",
        "recommended_monitoring_focus": (
            "Watch for bud differentiation signs and avoid excess irrigation "
            "that could delay flower induction."
        ),
    },
]


def _stage_lookup_table() -> pd.DataFrame:
    """Build a small DataFrame of stage start dates, sorted chronologically."""
    lookup = pd.DataFrame(PHENOLOGY_STAGES)
    lookup["start_day_of_year"] = pd.to_datetime(
        {
            "year": 2001,  # any non-leap reference year; only month/day matter
            "month": lookup["start_month"],
            "day": lookup["start_day"],
        }
    ).dt.dayofyear
    return lookup.sort_values("start_day_of_year").reset_index(drop=True)


def _assign_stage_for_day_of_year(day_of_year: int, lookup: pd.DataFrame) -> pd.Series:
    """
    Return the stage row whose start_day_of_year is the latest one at or
    before `day_of_year`, wrapping around to the last stage in the list if
    `day_of_year` falls before the first stage's start (i.e. very early
    January, before day_of_year 1 — not actually reachable since stage 1
    starts on day 1, but kept for safety/clarity).
    """
    eligible = lookup[lookup["start_day_of_year"] <= day_of_year]
    if eligible.empty:
        return lookup.iloc[-1]
    return eligible.iloc[-1]


def _load_date_range_from_combined_feature_table(path: Path) -> pd.DatetimeIndex:
    """
    Read only the `date` column of the combined feature table to discover
    the historical date range already used elsewhere in this project, then
    return one date per calendar day across that full range (min to max,
    inclusive of every day, not just the days present in that file).
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Combined feature table not found: {path}\n"
            "Run python src/features/build_feature_table.py first to create it."
        )

    df = pd.read_csv(path, usecols=["date"])
    if "date" not in df.columns:
        raise MissingColumnsError(
            "Combined feature table is missing the required 'date' column.\n"
            f"Columns actually found: {list(df.columns)}."
        )

    dates = pd.to_datetime(df["date"])
    if dates.empty:
        raise ValueError("Combined feature table has no rows; cannot determine a date range.")

    return pd.date_range(start=dates.min(), end=dates.max(), freq="D")


def build_phenology_calendar(date_index: pd.DatetimeIndex) -> pd.DataFrame:
    """Assign a mango growth stage to every date in `date_index`."""

    lookup = _stage_lookup_table()

    rows = []
    for current_date in date_index:
        day_of_year = current_date.dayofyear
        stage_row = _assign_stage_for_day_of_year(day_of_year, lookup)
        rows.append(
            {
                "date": current_date,
                "month": current_date.month,
                "day_of_year": day_of_year,
                "mango_stage": stage_row["mango_stage"],
                "stage_description": stage_row["stage_description"],
                "water_sensitivity": stage_row["water_sensitivity"],
                "heat_sensitivity": stage_row["heat_sensitivity"],
                "disease_sensitivity": stage_row["disease_sensitivity"],
                "recommended_monitoring_focus": stage_row["recommended_monitoring_focus"],
            }
        )

    return pd.DataFrame(rows)


def build_mango_phenology_calendar() -> bool:
    """
    Build the standalone mango phenology calendar CSV from the combined
    feature table's date range.

    Returns True on success, False if the input is missing/malformed —
    always with a clear, friendly explanation printed first.
    """

    config = get_config()
    input_path = config.path("combined_feature_table_csv")
    output_path = config.path("mango_phenology_calendar_csv")

    try:
        date_index = _load_date_range_from_combined_feature_table(input_path)
    except (FileNotFoundError, MissingColumnsError, ValueError) as exc:
        print()
        print(str(exc))
        return False

    log.info(
        "Loaded date range %s to %s (%d days) from %s",
        date_index.min().date(),
        date_index.max().date(),
        len(date_index),
        input_path,
    )

    result = build_phenology_calendar(date_index)
    validate_phenology_output(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)

    stage_counts = result["mango_stage"].value_counts().to_dict()

    log.info("Computed mango phenology calendar for %d days.", len(result))
    log.info("Stage breakdown: %s", stage_counts)
    log.info("Wrote mango phenology calendar to %s", output_path)

    print()
    print(f"Date range:    {date_index.min().date()} to {date_index.max().date()}")
    print(f"Output rows:   {len(result)}")
    print("Stage breakdown:")
    for stage_name, count in stage_counts.items():
        print(f"  {stage_name}: {count} days")
    print(f"Saved mango phenology calendar to: {output_path}")
    print()
    print("This is a simplified, regional (Andhra Pradesh / South India) mango")
    print("calendar — not cultivar-specific and not based on field observations.")
    print("It is standalone for now: not wired into main.py, the FAO-56 water")
    print("balance script, or the dashboard. See the module docstring for the")
    print("exact stage date boundaries and the assumptions behind them.")
    return True


def main():
    log.info("Building mango phenology calendar...")
    success = build_mango_phenology_calendar()

    if success:
        log.info("Mango phenology calendar build completed successfully.")
    else:
        log.info("Mango phenology calendar build did not complete. See messages above.")


if __name__ == "__main__":
    main()
