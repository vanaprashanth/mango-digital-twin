"""
Standalone FAO-56 soil-water balance script.

WHAT THIS FILE DOES (and does NOT do):
  - Reads the existing combined weather + soil + vegetation feature table
    (data/processed/muthukur_combined_feature_table.csv).
  - Computes daily reference evapotranspiration (ET0) using the FAO-56
    Penman-Monteith equation, then a daily root-zone soil-water balance
    (depletion, total/readily available water, and a water-stress
    coefficient Ks).
  - Writes one new CSV:
    data/processed/muthukur_fao56_water_balance.csv
  - It does NOT call any external API, does NOT touch main.py, does NOT
    change the Streamlit dashboard, and does NOT replace the existing
    irrigation_risk_score. It only reads one CSV that an earlier standalone
    script already produced, and writes one new CSV.

WHY THE COMBINED FEATURE TABLE AS INPUT
  That table already has everything FAO-56 needs in one place: daily
  temperature (avg/max/min), humidity, rainfall, solar radiation, wind
  speed (all from the historical weather/risk pipeline), plus the SoilGrids
  sand/clay/organic-carbon percentages (from build_feature_table.py). Using
  it as the single input avoids re-reading three separate files.

REFERENCE
  Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). "Crop
  Evapotranspiration - Guidelines for computing crop water requirements."
  FAO Irrigation and Drainage Paper No. 56. Equation numbers referenced
  below (eq N) are from that document, Chapters 3, 4, and 8.

  Saxton, K.E. and Rawls, W.J. (1986). "Estimating generalized soil-water
  characteristics from texture." Soil Science Society of America Journal,
  50(4), 1031-1036. Used here as a pedotransfer function to estimate field
  capacity and wilting point from SoilGrids sand/clay/organic-matter
  percentages, since SoilGrids does not provide those directly.

STEP 1 — REFERENCE EVAPOTRANSPIRATION (ET0), FAO-56 PENMAN-MONTEITH (eq 6)

    ET0 = [0.408*Delta*(Rn-G) + gamma*(900/(T+273))*u2*(es-ea)]
          / [Delta + gamma*(1 + 0.34*u2)]

  Where Delta = slope of the saturation vapor pressure curve (eq 13),
  gamma = psychrometric constant from elevation-derived atmospheric
  pressure (eq 7-8), T = mean daily air temperature, u2 = wind speed at 2m
  (NASA POWER's WS2M, which is already a 2m measurement), es/ea =
  saturation/actual vapor pressure (eq 11-19), Rn = net radiation (eq
  38-39, using measured solar radiation, extraterrestrial radiation from
  latitude + day-of-year, and clear-sky radiation), G = soil heat flux,
  assumed 0 for daily timesteps (FAO-56 recommendation).

  SIMPLIFICATION: actual vapor pressure (ea) is derived from mean relative
  humidity only (FAO-56 eq 19: ea = es * RHmean/100), because the input
  data has one daily RH value, not separate RHmax/RHmin. FAO-56 notes this
  is an acceptable substitute when only mean RH is available.

STEP 2 — CROP EVAPOTRANSPIRATION (ETc)

    ETc = ET0 * Kc

  Kc here is a SINGLE CONSTANT for the whole date range
  (configs/config.yaml -> fao56.kc_constant), not yet phenology-aware. Real
  mango Kc varies by growth stage (FAO-56 Table 12 lists ~0.5 post-harvest
  up to ~0.85 during peak vegetative growth). A growth-stage-aware Kc is
  planned for ROADMAP.md Phase 5 (ineligible until a phenology model
  exists) — this script intentionally does NOT attempt that yet.

STEP 3 — ROOT-ZONE SOIL-WATER BALANCE (FAO-56 Chapter 8, eq 82-85)

    TAW = 1000 * (theta_FC - theta_WP) * Zr        (eq 82)
    RAW = p * TAW                                   (eq 83)
    Dr,i = Dr,i-1 - rainfall_i + ETc,i               (simplified eq 85)
    Ks = (TAW - Dr) / (TAW - RAW)  if Dr > RAW, else 1   (eq 84)

  theta_FC (field capacity) and theta_WP (wilting point) are estimated from
  SoilGrids sand/clay/organic-carbon using the Saxton & Rawls (1986)
  pedotransfer equations (see _field_capacity_and_wilting_point below).
  Zr (root depth) and p (no-stress depletion fraction) come from
  configs/config.yaml -> fao56.

  IMPORTANT SIMPLIFICATIONS, STATED PLAINLY:
    - No irrigation events are tracked. This project has no field
      irrigation log, so the depletion balance assumes rainfed conditions
      only — it shows how much soil water would be depleted *if no
      supplemental irrigation were applied*, which is consistent with this
      project's existing "irrigation risk" framing (estimating need, not
      logging actual practice).
    - No runoff or deep-percolation model: if a rain event pushes the
      balance below zero depletion (wetter than field capacity), the
      excess is assumed to drain away and depletion is clamped to 0,
      matching FAO-56's own treatment of excess water (eq 88 simplified).
    - Depletion is also clamped at TAW (cannot become more depleted than
      "all available water gone") as a sanity bound for the risk
      indicator, not because the real soil-water content cannot, in
      principle, drop further.
    - The very first day's depletion is initialized to 0 (assumes the soil
      starts at field capacity) since there is no observed starting soil
      moisture. This means the first several days of output are less
      reliable than later days, once the running balance has had time to
      respond to real rainfall/ET0 patterns.

INPUT
  data/processed/muthukur_combined_feature_table.csv

OUTPUT
  data/processed/muthukur_fao56_water_balance.csv

HOW TO USE THIS FILE
  Run after the combined feature table has been built at least once:

      python src/water_balance/fao56_water_balance.py

  This is a standalone script only — it is not wired into main.py or the
  dashboard. Nothing downstream depends on it yet.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validation import MissingColumnsError, validate_fao56_input

log = get_logger(__name__)

# FAO-56 constants (Chapter 3-4).
GSC_MJ_M2_MIN = 0.0820  # solar constant
STEFAN_BOLTZMANN = 4.903e-9  # MJ K^-4 m^-2 day^-1
REFERENCE_ALBEDO_DEFAULT = 0.23

# Beginner-friendly water-stress labels, based on the FAO-56 transpiration
# reduction coefficient Ks (1.0 = no stress, lower = more stress). These
# bucket boundaries are a simple, documented choice for this project, not
# an official FAO-56 standard.
KS_LOW_STRESS_MIN = 0.90
KS_MEDIUM_STRESS_MIN = 0.60


def _water_stress_label(ks: float) -> str:
    if ks >= KS_LOW_STRESS_MIN:
        return "Low"
    if ks >= KS_MEDIUM_STRESS_MIN:
        return "Medium"
    return "High"


def _saturation_vapor_pressure_kpa(temp_c: pd.Series) -> pd.Series:
    """FAO-56 eq 11: e°(T) = 0.6108 * exp(17.27*T / (T+237.3))"""
    return 0.6108 * np.exp((17.27 * temp_c) / (temp_c + 237.3))


def _slope_vapor_pressure_curve(temp_mean_c: pd.Series, es_mean: pd.Series) -> pd.Series:
    """FAO-56 eq 13: Delta = 4098 * e°(T) / (T+237.3)^2"""
    return (4098 * es_mean) / (temp_mean_c + 237.3) ** 2


def _atmospheric_pressure_kpa(elevation_m: float) -> float:
    """FAO-56 eq 7: P = 101.3 * ((293 - 0.0065*z) / 293)^5.26"""
    return 101.3 * ((293 - 0.0065 * elevation_m) / 293) ** 5.26


def _psychrometric_constant(pressure_kpa: float) -> float:
    """FAO-56 eq 8: gamma = 0.000665 * P"""
    return 0.000665 * pressure_kpa


def _extraterrestrial_radiation_mj_m2(day_of_year: pd.Series, latitude_deg: float) -> pd.Series:
    """FAO-56 eq 21-25: Ra from latitude and day of year."""
    lat_rad = np.radians(latitude_deg)
    dr = 1 + 0.033 * np.cos(2 * np.pi * day_of_year / 365)  # eq 23
    delta = 0.409 * np.sin(2 * np.pi * day_of_year / 365 - 1.39)  # eq 24
    sunset_angle_arg = np.clip(-np.tan(lat_rad) * np.tan(delta), -1.0, 1.0)
    omega_s = np.arccos(sunset_angle_arg)  # eq 25
    ra = (
        (24 * 60 / np.pi)
        * GSC_MJ_M2_MIN
        * dr
        * (
            omega_s * np.sin(lat_rad) * np.sin(delta)
            + np.cos(lat_rad) * np.cos(delta) * np.sin(omega_s)
        )
    )  # eq 21
    return ra


def _field_capacity_and_wilting_point(
    sand_percent: float, clay_percent: float, organic_carbon_g_kg: float
) -> tuple[float, float]:
    """
    Saxton & Rawls (1986) pedotransfer equations: estimate volumetric water
    content at field capacity (-33 kPa) and permanent wilting point
    (-1500 kPa) from soil texture and organic matter, since SoilGrids only
    provides texture/carbon, not field capacity/wilting point directly.

    sand_percent, clay_percent: 0-100 SoilGrids percentages.
    organic_carbon_g_kg: SoilGrids organic carbon, g/kg.

    Returns (theta_fc, theta_wp) as volumetric fractions (cm3/cm3).
    """
    sand_fraction = sand_percent / 100.0
    clay_fraction = clay_percent / 100.0
    # Van Bemmelen factor (1.724) converts organic carbon % to organic
    # matter %. organic_carbon_g_kg / 10 converts g/kg to percent.
    organic_matter_percent = (organic_carbon_g_kg / 10.0) * 1.724

    s, c, om = sand_fraction, clay_fraction, organic_matter_percent

    theta_1500_t = (
        -0.024 * s
        + 0.487 * c
        + 0.006 * om
        + 0.005 * (s * om)
        - 0.013 * (c * om)
        + 0.068 * (s * c)
        + 0.031
    )
    theta_wp = theta_1500_t + (0.14 * theta_1500_t - 0.02)

    theta_33_t = (
        -0.251 * s
        + 0.195 * c
        + 0.011 * om
        + 0.006 * (s * om)
        - 0.027 * (c * om)
        + 0.452 * (s * c)
        + 0.299
    )
    theta_fc = theta_33_t + (1.283 * theta_33_t**2 - 0.374 * theta_33_t - 0.015)

    return theta_fc, theta_wp


def _load_combined_feature_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Combined feature table not found: {path}\n"
            "Run python src/features/build_feature_table.py first to create it."
        )
    df = pd.read_csv(path)
    validate_fao56_input(df)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


def compute_et0(df: pd.DataFrame, latitude_deg: float, elevation_m: float, albedo: float) -> pd.Series:
    """Compute daily ET0 (mm/day) via FAO-56 Penman-Monteith, eq 6."""

    temp_mean = df["temperature_avg_c"]
    temp_max = df["temperature_max_c"]
    temp_min = df["temperature_min_c"]
    rh_mean = df["relative_humidity_percent"]
    rs = df["solar_radiation_mj_m2"]
    u2 = df["wind_speed_m_s"]

    es_tmax = _saturation_vapor_pressure_kpa(temp_max)
    es_tmin = _saturation_vapor_pressure_kpa(temp_min)
    es = (es_tmax + es_tmin) / 2  # eq 12
    es_tmean = _saturation_vapor_pressure_kpa(temp_mean)

    # eq 19: actual vapor pressure from mean RH only (no RHmax/RHmin here).
    ea = es * (rh_mean / 100.0)

    delta = _slope_vapor_pressure_curve(temp_mean, es_tmean)

    pressure = _atmospheric_pressure_kpa(elevation_m)
    gamma = _psychrometric_constant(pressure)

    day_of_year = df["date"].dt.dayofyear
    ra = _extraterrestrial_radiation_mj_m2(day_of_year, latitude_deg)
    rso = (0.75 + 2e-5 * elevation_m) * ra  # eq 37

    rns = (1 - albedo) * rs  # eq 38

    rs_rso_ratio = np.clip(rs / rso.replace(0, np.nan), 0.0, 1.0)
    tmax_k = temp_max + 273.16
    tmin_k = temp_min + 273.16
    rnl = (
        STEFAN_BOLTZMANN
        * ((tmax_k**4 + tmin_k**4) / 2)
        * (0.34 - 0.14 * np.sqrt(ea.clip(lower=0)))
        * (1.35 * rs_rso_ratio - 0.35)
    )  # eq 39
    rn = rns - rnl

    soil_heat_flux_g = 0.0  # FAO-56: assumed 0 for daily computations

    numerator = 0.408 * delta * (rn - soil_heat_flux_g) + gamma * (900 / (temp_mean + 273)) * u2 * (
        es - ea
    )
    denominator = delta + gamma * (1 + 0.34 * u2)

    et0 = numerator / denominator
    return et0.clip(lower=0)


def compute_water_balance(
    df: pd.DataFrame,
    et0: pd.Series,
    kc_constant: float,
    root_depth_m: float,
    depletion_fraction_p: float,
) -> pd.DataFrame:
    """Compute ETc and the daily root-zone soil-water balance (eq 82-85)."""

    etc = et0 * kc_constant

    theta_fc, theta_wp = _field_capacity_and_wilting_point(
        sand_percent=df["sand_percent"].iloc[0],
        clay_percent=df["clay_percent"].iloc[0],
        organic_carbon_g_kg=df["organic_carbon_g_kg"].iloc[0],
    )

    taw_mm = 1000 * (theta_fc - theta_wp) * root_depth_m  # eq 82
    raw_mm = depletion_fraction_p * taw_mm  # eq 83

    rainfall = df["rainfall_mm"].fillna(0).to_numpy()
    etc_values = etc.to_numpy()

    depletion = np.zeros(len(df))
    previous_depletion = 0.0  # assume the soil starts at field capacity
    for i in range(len(df)):
        current_depletion = previous_depletion - rainfall[i] + etc_values[i]
        current_depletion = max(0.0, min(current_depletion, taw_mm))
        depletion[i] = current_depletion
        previous_depletion = current_depletion

    ks = np.where(
        depletion > raw_mm,
        (taw_mm - depletion) / max(taw_mm - raw_mm, 1e-9),
        1.0,
    )
    ks = np.clip(ks, 0.0, 1.0)

    out = pd.DataFrame(
        {
            "date": df["date"],
            "et0_mm": et0.to_numpy(),
            "etc_mm": etc_values,
            "rainfall_mm": rainfall,
            "root_zone_depletion_mm": depletion,
            "taw_mm": taw_mm,
            "raw_mm": raw_mm,
            "water_stress_coefficient_ks": ks,
        }
    )
    out["water_stress_level"] = out["water_stress_coefficient_ks"].apply(_water_stress_label)
    return out


def build_fao56_water_balance() -> bool:
    """
    Build the daily FAO-56 reference ET0, crop ETc, and root-zone soil-water
    balance from the combined feature table.

    Returns True on success, False if the input is missing/malformed —
    always with a clear, friendly explanation printed first.
    """

    config = get_config()
    input_path = config.path("combined_feature_table_csv")
    output_path = config.path("fao56_water_balance_csv")

    try:
        df = _load_combined_feature_table(input_path)
    except (FileNotFoundError, MissingColumnsError) as exc:
        print()
        print(str(exc))
        return False

    log.info("Loaded %d combined feature table rows from %s", len(df), input_path)

    fao56_settings = config._raw.get("fao56", {})
    elevation_m = fao56_settings.get("elevation_m", 150)
    root_depth_m = fao56_settings.get("root_depth_m", 1.2)
    depletion_fraction_p = fao56_settings.get("depletion_fraction_p", 0.50)
    kc_constant = fao56_settings.get("kc_constant", 0.75)
    albedo = fao56_settings.get("albedo", REFERENCE_ALBEDO_DEFAULT)

    et0 = compute_et0(df, latitude_deg=config.latitude, elevation_m=elevation_m, albedo=albedo)

    result = compute_water_balance(
        df,
        et0=et0,
        kc_constant=kc_constant,
        root_depth_m=root_depth_m,
        depletion_fraction_p=depletion_fraction_p,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)

    stress_counts = result["water_stress_level"].value_counts().to_dict()

    log.info("Computed FAO-56 water balance for %d days.", len(result))
    log.info(
        "TAW=%.1f mm, RAW=%.1f mm (root depth=%.2f m, depletion fraction p=%.2f)",
        result["taw_mm"].iloc[0],
        result["raw_mm"].iloc[0],
        root_depth_m,
        depletion_fraction_p,
    )
    log.info("Water stress level breakdown: %s", stress_counts)
    log.info("Wrote FAO-56 water balance table to %s", output_path)

    print()
    print(f"Input rows:                  {len(df)}")
    print(f"Output rows:                 {len(result)}")
    print(f"Mean ET0 (mm/day):           {result['et0_mm'].mean():.2f}")
    print(f"Mean ETc (mm/day):           {result['etc_mm'].mean():.2f}")
    print(f"TAW (total available water): {result['taw_mm'].iloc[0]:.1f} mm")
    print(f"RAW (readily available):     {result['raw_mm'].iloc[0]:.1f} mm")
    print(f"Water stress level breakdown: {stress_counts}")
    print(f"Saved FAO-56 water balance table to: {output_path}")
    print()
    print("This is still a standalone file — not yet wired into main.py")
    print("or the dashboard. Crop coefficient (Kc) is a constant for now,")
    print("not yet phenology-aware (see ROADMAP.md Phase 5).")
    return True


def main():
    log.info("Building FAO-56 soil-water balance...")
    success = build_fao56_water_balance()

    if success:
        log.info("FAO-56 water balance build completed successfully.")
    else:
        log.info("FAO-56 water balance build did not complete. See messages above.")


if __name__ == "__main__":
    main()
