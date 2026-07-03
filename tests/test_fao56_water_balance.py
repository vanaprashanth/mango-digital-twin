"""
tests/test_fao56_water_balance.py

Deterministic unit tests for the FAO-56 water-balance pipeline.

Functions under test (all pure / no I/O):
  src/water_balance/fao56_water_balance.py
    compute_et0()
    compute_water_balance()
    _water_stress_label()
    _field_capacity_and_wilting_point()

  src/water_balance/fao56_phenology_water_balance.py
    compute_phenology_water_balance()
    _kc_lookup_series()

  src/water_balance/fao56_interpolated_kc_water_balance.py
    compute_interpolated_kc_water_balance()
    _compute_interpolated_kc()

All tests use small in-memory DataFrames.  No CSV files, no external APIs.
Typical inputs are representative of Chittoor / southern Andhra Pradesh
(latitude ~13.3 N, elevation ~150 m, tropical semi-arid climate).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.water_balance.fao56_water_balance import (
    _field_capacity_and_wilting_point,
    _water_stress_label,
    compute_et0,
    compute_water_balance,
    KS_LOW_STRESS_MIN,
    KS_MEDIUM_STRESS_MIN,
)
from src.water_balance.fao56_phenology_water_balance import (
    _kc_lookup_series,
    compute_phenology_water_balance,
)
from src.water_balance.fao56_interpolated_kc_water_balance import (
    _compute_interpolated_kc,
    compute_interpolated_kc_water_balance,
)


# ---------------------------------------------------------------------------
# Shared test constants (representative Chittoor / AP values)
# ---------------------------------------------------------------------------

LATITUDE_DEG = 13.294
ELEVATION_M = 150.0
ALBEDO = 0.23
ROOT_DEPTH_M = 1.2
DEPLETION_FRACTION_P = 0.50
KC_CONSTANT = 0.75

# Typical AP summer weather: hot, moderate humidity, good solar radiation
TYPICAL_WEATHER = {
    "temperature_avg_c": 30.0,
    "temperature_max_c": 37.0,
    "temperature_min_c": 24.0,
    "relative_humidity_percent": 60.0,
    "solar_radiation_mj_m2": 20.0,
    "wind_speed_m_s": 2.0,
}

# Typical SoilGrids values for the study area
TYPICAL_SOIL = {
    "sand_percent": 40.0,
    "clay_percent": 25.0,
    "organic_carbon_g_kg": 15.0,
}

# Known phenology Kc stage mapping (mirrors configs/config.yaml)
PHENOLOGY_KC_STAGES = {
    "Flower induction / pre-flowering": 0.65,
    "Flowering": 0.75,
    "Fruit set": 0.85,
    "Fruit development": 0.90,
    "Maturity / harvest": 0.80,
    "Rest / vegetative phase": 0.60,
    "Rest": 0.60,
}

VALID_STRESS_LEVELS = {"Low", "Medium", "High"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_weather_df(n_days: int = 30, **overrides) -> pd.DataFrame:
    """
    Build a minimal weather DataFrame with `n_days` identical rows using
    TYPICAL_WEATHER values (or any overrides supplied as keyword args).

    Includes the soil columns compute_water_balance() needs so the same
    DataFrame can be passed to both compute_et0() and compute_water_balance().
    """
    row = {**TYPICAL_WEATHER, **TYPICAL_SOIL}
    row.update(overrides)
    df = pd.DataFrame([row] * n_days)
    df["date"] = pd.date_range("2024-01-01", periods=n_days, freq="D")
    df["rainfall_mm"] = 0.0
    return df


def _make_joined_df(stages: list[str], n_days_each: int = 10) -> pd.DataFrame:
    """
    Build a joined feature+phenology DataFrame cycling through `stages`,
    with `n_days_each` days per stage.
    """
    total = len(stages) * n_days_each
    stage_col = []
    for s in stages:
        stage_col.extend([s] * n_days_each)
    df = _make_weather_df(n_days=total)
    df["mango_stage"] = stage_col
    return df


# ---------------------------------------------------------------------------
# 1. Pedotransfer function: field capacity and wilting point
# ---------------------------------------------------------------------------

class TestFieldCapacityAndWiltingPoint:
    def test_returns_two_positive_fractions(self):
        fc, wp = _field_capacity_and_wilting_point(40.0, 25.0, 15.0)
        assert fc > 0.0
        assert wp > 0.0

    def test_field_capacity_greater_than_wilting_point(self):
        fc, wp = _field_capacity_and_wilting_point(40.0, 25.0, 15.0)
        assert fc > wp, "FC must exceed WP — otherwise TAW would be zero or negative"

    def test_fc_and_wp_are_volumetric_fractions(self):
        # Both should be in the realistic 0.05–0.60 range (m3/m3) for mineral soils
        fc, wp = _field_capacity_and_wilting_point(40.0, 25.0, 15.0)
        assert 0.05 < fc < 0.60
        assert 0.05 < wp < 0.60

    def test_sandy_soil_lower_fc_than_clayey(self):
        fc_sandy, _ = _field_capacity_and_wilting_point(80.0, 5.0, 5.0)
        fc_clay, _ = _field_capacity_and_wilting_point(10.0, 55.0, 15.0)
        # Clayey soils hold more water at field capacity
        assert fc_clay > fc_sandy

    def test_high_organic_matter_raises_fc(self):
        fc_low, _ = _field_capacity_and_wilting_point(40.0, 25.0, 5.0)
        fc_high, _ = _field_capacity_and_wilting_point(40.0, 25.0, 50.0)
        assert fc_high >= fc_low  # more OM should raise or maintain FC


# ---------------------------------------------------------------------------
# 2. Water-stress label thresholds
# ---------------------------------------------------------------------------

class TestWaterStressLabel:
    def test_ks_1_is_low(self):
        assert _water_stress_label(1.0) == "Low"

    def test_ks_at_low_threshold_is_low(self):
        assert _water_stress_label(KS_LOW_STRESS_MIN) == "Low"

    def test_ks_just_below_low_threshold_is_medium(self):
        assert _water_stress_label(KS_LOW_STRESS_MIN - 0.001) == "Medium"

    def test_ks_at_medium_threshold_is_medium(self):
        assert _water_stress_label(KS_MEDIUM_STRESS_MIN) == "Medium"

    def test_ks_just_below_medium_threshold_is_high(self):
        assert _water_stress_label(KS_MEDIUM_STRESS_MIN - 0.001) == "High"

    def test_ks_0_is_high(self):
        assert _water_stress_label(0.0) == "High"

    @pytest.mark.parametrize("ks", [0.0, 0.3, 0.59, 0.60, 0.75, 0.89, 0.90, 1.0])
    def test_label_always_valid(self, ks: float):
        assert _water_stress_label(ks) in VALID_STRESS_LEVELS


# ---------------------------------------------------------------------------
# 3. ET0 computation
# ---------------------------------------------------------------------------

class TestComputeET0:
    def test_et0_is_non_negative(self):
        df = _make_weather_df(30)
        et0 = compute_et0(df, LATITUDE_DEG, ELEVATION_M, ALBEDO)
        assert (et0 >= 0).all(), "ET0 must never be negative (clipped at 0)"

    def test_et0_is_plausible_for_tropical_inputs(self):
        # Typical tropical semi-arid daily ET0: 3–9 mm/day
        df = _make_weather_df(30)
        et0 = compute_et0(df, LATITUDE_DEG, ELEVATION_M, ALBEDO)
        mean_et0 = et0.mean()
        assert 2.0 < mean_et0 < 12.0, f"Unexpected mean ET0={mean_et0:.2f} mm/day for typical AP inputs"

    def test_et0_length_matches_input(self):
        df = _make_weather_df(15)
        et0 = compute_et0(df, LATITUDE_DEG, ELEVATION_M, ALBEDO)
        assert len(et0) == 15

    def test_higher_temperature_raises_et0(self):
        df_cool = _make_weather_df(10, temperature_avg_c=20.0, temperature_max_c=27.0, temperature_min_c=14.0)
        df_hot = _make_weather_df(10, temperature_avg_c=38.0, temperature_max_c=44.0, temperature_min_c=32.0)
        et0_cool = compute_et0(df_cool, LATITUDE_DEG, ELEVATION_M, ALBEDO).mean()
        et0_hot = compute_et0(df_hot, LATITUDE_DEG, ELEVATION_M, ALBEDO).mean()
        assert et0_hot > et0_cool

    def test_higher_solar_radiation_raises_et0(self):
        df_low = _make_weather_df(10, solar_radiation_mj_m2=8.0)
        df_high = _make_weather_df(10, solar_radiation_mj_m2=25.0)
        et0_low = compute_et0(df_low, LATITUDE_DEG, ELEVATION_M, ALBEDO).mean()
        et0_high = compute_et0(df_high, LATITUDE_DEG, ELEVATION_M, ALBEDO).mean()
        assert et0_high > et0_low

    def test_et0_returns_series(self):
        df = _make_weather_df(5)
        et0 = compute_et0(df, LATITUDE_DEG, ELEVATION_M, ALBEDO)
        assert isinstance(et0, pd.Series)


# ---------------------------------------------------------------------------
# 4. Water balance (constant Kc)
# ---------------------------------------------------------------------------

class TestComputeWaterBalance:
    """Tests for compute_water_balance() using a constant Kc."""

    def _run(self, n_days: int = 30, rainfall_mm: float = 0.0, **weather_overrides):
        df = _make_weather_df(n_days, **weather_overrides)
        df["rainfall_mm"] = rainfall_mm
        et0 = compute_et0(df, LATITUDE_DEG, ELEVATION_M, ALBEDO)
        return compute_water_balance(df, et0, KC_CONSTANT, ROOT_DEPTH_M, DEPLETION_FRACTION_P)

    def test_taw_is_positive(self):
        result = self._run()
        assert (result["taw_mm"] > 0).all(), "TAW must be positive"

    def test_raw_is_positive(self):
        result = self._run()
        assert (result["raw_mm"] > 0).all(), "RAW must be positive"

    def test_raw_does_not_exceed_taw(self):
        result = self._run()
        assert (result["raw_mm"] <= result["taw_mm"]).all(), "RAW must never exceed TAW"

    def test_ks_between_zero_and_one(self):
        result = self._run()
        ks = result["water_stress_coefficient_ks"]
        assert (ks >= 0.0).all(), "Ks must be >= 0"
        assert (ks <= 1.0).all(), "Ks must be <= 1"

    def test_depletion_never_negative(self):
        result = self._run()
        assert (result["root_zone_depletion_mm"] >= 0).all(), "Depletion must be >= 0"

    def test_depletion_never_exceeds_taw(self):
        result = self._run()
        excess = result["root_zone_depletion_mm"] > result["taw_mm"] + 1e-6
        assert not excess.any(), "Depletion must not exceed TAW"

    def test_etc_non_negative(self):
        result = self._run()
        assert (result["etc_mm"] >= 0).all()

    def test_et0_non_negative(self):
        result = self._run()
        assert (result["et0_mm"] >= 0).all()

    def test_stress_levels_are_valid_strings(self):
        result = self._run()
        bad = ~result["water_stress_level"].isin(VALID_STRESS_LEVELS)
        assert not bad.any(), f"Unexpected stress levels: {result['water_stress_level'][bad].unique()}"

    def test_length_matches_input(self):
        result = self._run(n_days=20)
        assert len(result) == 20

    def test_heavy_rainfall_keeps_depletion_low(self):
        # 30 mm/day rainfall should keep depletion near zero
        result = self._run(n_days=30, rainfall_mm=30.0)
        assert result["root_zone_depletion_mm"].mean() < result["taw_mm"].iloc[0] * 0.2

    def test_zero_rainfall_increases_depletion_over_time(self):
        # With no rain, depletion should grow (or at least not shrink monotonically)
        result = self._run(n_days=60, rainfall_mm=0.0)
        # Depletion on day 30 should exceed depletion on day 1
        assert result["root_zone_depletion_mm"].iloc[29] >= result["root_zone_depletion_mm"].iloc[0]

    def test_ks_is_one_when_soil_is_wet(self):
        # Sufficient rain keeps depletion <= RAW, so Ks should be 1.0 for all rows
        result = self._run(n_days=10, rainfall_mm=50.0)
        assert (result["water_stress_coefficient_ks"] == 1.0).all()

    def test_output_has_required_columns(self):
        result = self._run()
        required = {
            "date", "et0_mm", "etc_mm", "rainfall_mm",
            "root_zone_depletion_mm", "taw_mm", "raw_mm",
            "water_stress_coefficient_ks", "water_stress_level",
        }
        missing = required - set(result.columns)
        assert not missing, f"Missing output columns: {missing}"


# ---------------------------------------------------------------------------
# 5. Phenology Kc lookup
# ---------------------------------------------------------------------------

class TestKcLookupSeries:
    def test_known_stages_return_correct_kc(self):
        stages = pd.Series(["Flowering", "Fruit set", "Fruit development"])
        kc = _kc_lookup_series(stages, PHENOLOGY_KC_STAGES)
        assert kc.iloc[0] == pytest.approx(0.75)
        assert kc.iloc[1] == pytest.approx(0.85)
        assert kc.iloc[2] == pytest.approx(0.90)

    def test_all_configured_stages_map_without_error(self):
        stages = pd.Series(list(PHENOLOGY_KC_STAGES.keys()))
        kc = _kc_lookup_series(stages, PHENOLOGY_KC_STAGES)
        assert len(kc) == len(PHENOLOGY_KC_STAGES)
        assert (kc > 0).all()

    def test_kc_values_in_plausible_mango_range(self):
        stages = pd.Series(list(PHENOLOGY_KC_STAGES.keys()))
        kc = _kc_lookup_series(stages, PHENOLOGY_KC_STAGES)
        # FAO-56 Table 12 lists mango Kc roughly 0.5–0.85+
        assert (kc >= 0.5).all()
        assert (kc <= 1.1).all()

    def test_unknown_stage_raises_error(self):
        stages = pd.Series(["Unknown mythical stage"])
        with pytest.raises(Exception):
            _kc_lookup_series(stages, PHENOLOGY_KC_STAGES)

    def test_rest_alias_maps_same_as_full_rest_name(self):
        kc_alias = _kc_lookup_series(pd.Series(["Rest"]), PHENOLOGY_KC_STAGES).iloc[0]
        kc_full = _kc_lookup_series(pd.Series(["Rest / vegetative phase"]), PHENOLOGY_KC_STAGES).iloc[0]
        assert kc_alias == pytest.approx(kc_full)


# ---------------------------------------------------------------------------
# 6. Phenology-aware water balance (per-day Kc)
# ---------------------------------------------------------------------------

class TestComputePhenologyWaterBalance:
    """Tests for compute_phenology_water_balance() with a per-day Kc Series."""

    STAGES = ["Flowering", "Fruit set", "Fruit development", "Maturity / harvest"]

    def _run(self, n_days_each: int = 10, rainfall_mm: float = 0.0):
        joined = _make_joined_df(self.STAGES, n_days_each)
        joined["rainfall_mm"] = rainfall_mm
        et0 = compute_et0(joined, LATITUDE_DEG, ELEVATION_M, ALBEDO)
        kc = _kc_lookup_series(joined["mango_stage"], PHENOLOGY_KC_STAGES)
        return compute_phenology_water_balance(joined, et0, kc, ROOT_DEPTH_M, DEPLETION_FRACTION_P)

    def test_taw_positive(self):
        result = self._run()
        assert (result["taw_mm"] > 0).all()

    def test_raw_positive_and_lte_taw(self):
        result = self._run()
        assert (result["raw_mm"] > 0).all()
        assert (result["raw_mm"] <= result["taw_mm"]).all()

    def test_ks_between_zero_and_one(self):
        result = self._run()
        assert (result["ks"] >= 0.0).all()
        assert (result["ks"] <= 1.0).all()

    def test_depletion_non_negative(self):
        result = self._run()
        assert (result["root_zone_depletion_mm"] >= 0).all()

    def test_depletion_does_not_exceed_taw(self):
        result = self._run()
        assert (result["root_zone_depletion_mm"] <= result["taw_mm"] + 1e-6).all()

    def test_etc_non_negative(self):
        result = self._run()
        assert (result["etc_mm_day"] >= 0).all()

    def test_stress_levels_valid(self):
        result = self._run()
        assert result["water_stress_level"].isin(VALID_STRESS_LEVELS).all()

    def test_kc_matches_stage(self):
        result = self._run()
        for stage, expected_kc in PHENOLOGY_KC_STAGES.items():
            mask = result["mango_stage"] == stage
            if mask.any():
                actual_kc = result.loc[mask, "kc"].unique()
                assert len(actual_kc) == 1
                assert actual_kc[0] == pytest.approx(expected_kc)

    def test_higher_kc_stage_produces_higher_etc(self):
        # Fruit development (Kc=0.90) should have higher ETc than
        # Rest/vegetative (Kc=0.60) for identical weather
        stages_high = _make_joined_df(["Fruit development"], n_days_each=10)
        stages_low = _make_joined_df(["Rest / vegetative phase"], n_days_each=10)

        et0_high = compute_et0(stages_high, LATITUDE_DEG, ELEVATION_M, ALBEDO)
        kc_high = _kc_lookup_series(stages_high["mango_stage"], PHENOLOGY_KC_STAGES)
        result_high = compute_phenology_water_balance(stages_high, et0_high, kc_high, ROOT_DEPTH_M, DEPLETION_FRACTION_P)

        et0_low = compute_et0(stages_low, LATITUDE_DEG, ELEVATION_M, ALBEDO)
        kc_low = _kc_lookup_series(stages_low["mango_stage"], PHENOLOGY_KC_STAGES)
        result_low = compute_phenology_water_balance(stages_low, et0_low, kc_low, ROOT_DEPTH_M, DEPLETION_FRACTION_P)

        assert result_high["etc_mm_day"].mean() > result_low["etc_mm_day"].mean()

    def test_output_has_required_columns(self):
        result = self._run()
        required = {
            "date", "mango_stage", "kc", "et0_mm_day", "etc_mm_day",
            "rainfall_mm", "root_zone_depletion_mm", "taw_mm", "raw_mm",
            "ks", "water_stress_level",
        }
        missing = required - set(result.columns)
        assert not missing, f"Missing columns: {missing}"


# ---------------------------------------------------------------------------
# 7. Interpolated-Kc: interpolation function
# ---------------------------------------------------------------------------

class TestComputeInterpolatedKc:
    def test_interpolated_kc_length_matches_input(self):
        stage_kc = np.array([0.65, 0.65, 0.75, 0.75, 0.85, 0.85])
        interpolated, labels = _compute_interpolated_kc(stage_kc)
        assert len(interpolated) == len(stage_kc)
        assert len(labels) == len(stage_kc)

    def test_interpolated_values_are_non_nan(self):
        stage_kc = np.array([0.65, 0.65, 0.75, 0.75, 0.85, 0.85])
        interpolated, _ = _compute_interpolated_kc(stage_kc)
        assert not np.any(np.isnan(interpolated))

    def test_interpolated_kc_stays_within_input_range(self):
        stage_kc = np.array([0.60, 0.60, 0.75, 0.75, 0.90, 0.90, 0.65, 0.65])
        lo, hi = stage_kc.min(), stage_kc.max()
        interpolated, _ = _compute_interpolated_kc(stage_kc)
        assert interpolated.min() >= lo - 1e-9
        assert interpolated.max() <= hi + 1e-9

    def test_constant_kc_produces_constant_interpolated(self):
        stage_kc = np.array([0.75] * 10)
        interpolated, _ = _compute_interpolated_kc(stage_kc)
        assert np.allclose(interpolated, 0.75)

    def test_labels_are_valid_strings(self):
        stage_kc = np.array([0.65, 0.65, 0.75, 0.75])
        _, labels = _compute_interpolated_kc(stage_kc)
        valid = {"stage_anchor", "linear_midpoint"}
        assert all(lbl in valid for lbl in labels), f"Unexpected label(s): {set(labels) - valid}"

    def test_single_stage_does_not_crash(self):
        # Edge case: entire run is one stage
        stage_kc = np.array([0.80] * 20)
        interpolated, labels = _compute_interpolated_kc(stage_kc)
        assert len(interpolated) == 20

    def test_two_stages_transition_smoothly(self):
        # First half low Kc, second half high Kc — values in between should be
        # strictly between the two endpoint Kc values (no extrapolation)
        stage_kc = np.array([0.60] * 10 + [0.90] * 10)
        interpolated, _ = _compute_interpolated_kc(stage_kc)
        # The midpoint of the transition should be between 0.60 and 0.90
        mid_val = interpolated[10]  # first day of the second stage
        assert 0.60 <= mid_val <= 0.90


# ---------------------------------------------------------------------------
# 8. Interpolated-Kc water balance
# ---------------------------------------------------------------------------

class TestComputeInterpolatedKcWaterBalance:
    STAGES = ["Flower induction / pre-flowering", "Flowering", "Fruit set",
              "Fruit development", "Maturity / harvest", "Rest / vegetative phase"]

    def _run(self, n_days_each: int = 10, rainfall_mm: float = 0.0):
        joined = _make_joined_df(self.STAGES, n_days_each)
        joined["rainfall_mm"] = rainfall_mm

        et0 = compute_et0(joined, LATITUDE_DEG, ELEVATION_M, ALBEDO)

        stage_kc_values = np.array(
            [PHENOLOGY_KC_STAGES[s] for s in joined["mango_stage"]], dtype=float
        )
        interpolated_kc, method_labels = _compute_interpolated_kc(stage_kc_values)

        return compute_interpolated_kc_water_balance(
            joined_df=joined,
            et0=et0,
            stage_kc=stage_kc_values,
            interpolated_kc=interpolated_kc,
            method_labels=method_labels,
            root_depth_m=ROOT_DEPTH_M,
            depletion_fraction_p=DEPLETION_FRACTION_P,
        )

    def test_taw_positive(self):
        result = self._run()
        assert (result["taw_mm"] > 0).all()

    def test_raw_positive_and_lte_taw(self):
        result = self._run()
        assert (result["raw_mm"] > 0).all()
        assert (result["raw_mm"] <= result["taw_mm"]).all()

    def test_ks_between_zero_and_one(self):
        result = self._run()
        assert (result["ks"] >= 0.0).all()
        assert (result["ks"] <= 1.0).all()

    def test_depletion_non_negative(self):
        result = self._run()
        assert (result["root_zone_depletion_mm"] >= 0).all()

    def test_depletion_does_not_exceed_taw(self):
        # 1 mm tolerance: this output rounds depletion to 3 d.p., so a
        # clamped value (e.g. 164.4605) can round to 164.461, exceeding the
        # unrounded taw_mm (164.460505) by ~0.0005 mm. A real clamping
        # failure would be off by a multi-mm or larger amount.
        result = self._run()
        assert (result["root_zone_depletion_mm"] <= result["taw_mm"] + 1.0).all()

    def test_etc_non_negative(self):
        result = self._run()
        assert (result["etc_mm_day"] >= 0).all()

    def test_stress_levels_valid(self):
        result = self._run()
        assert result["water_stress_level"].isin(VALID_STRESS_LEVELS).all()

    def test_interpolated_kc_column_in_range(self):
        result = self._run()
        kc_min = min(PHENOLOGY_KC_STAGES.values())
        kc_max = max(PHENOLOGY_KC_STAGES.values())
        assert result["interpolated_kc"].min() >= kc_min - 1e-6
        assert result["interpolated_kc"].max() <= kc_max + 1e-6

    def test_output_has_required_columns(self):
        result = self._run()
        required = {
            "date", "mango_stage", "stage_kc", "interpolated_kc",
            "et0_mm_day", "etc_mm_day", "root_zone_depletion_mm",
            "taw_mm", "raw_mm", "ks", "water_stress_level", "interpolation_method",
        }
        missing = required - set(result.columns)
        assert not missing, f"Missing columns: {missing}"

    def test_interpolation_method_labels_valid(self):
        result = self._run()
        valid = {"stage_anchor", "linear_midpoint"}
        bad = ~result["interpolation_method"].isin(valid)
        assert not bad.any()
