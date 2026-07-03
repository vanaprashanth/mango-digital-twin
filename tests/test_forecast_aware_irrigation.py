"""
tests/test_forecast_aware_irrigation.py

Deterministic unit tests for the irrigation advisory decision function.

The function under test is _decide_advisory() in
src/advisory/forecast_aware_irrigation.py.

It is a pure function (no I/O, no external API calls):

    _decide_advisory(
        stress_level: str,
        mango_stage: str,
        ks: float,
        rain_next_24h: float | None,
        forecast_available: bool,
    ) -> tuple[str, str, str]  # (action, priority, reason)

All tests use small in-memory values and are fully deterministic.
"""

from __future__ import annotations

import pytest

# Import the private decision function directly.  It is pure and has no
# side effects so importing it here does not trigger any I/O or logging.
from src.advisory.forecast_aware_irrigation import _decide_advisory, CRITICAL_STAGES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _call(
    stress_level: str,
    rain_next_24h: float | None = 0.0,
    forecast_available: bool = True,
    mango_stage: str = "Rest / vegetative phase",
    ks: float = 0.8,
) -> tuple[str, str, str]:
    """Thin wrapper so tests only need to supply the arguments they care about."""
    return _decide_advisory(
        stress_level=stress_level,
        mango_stage=mango_stage,
        ks=ks,
        rain_next_24h=rain_next_24h,
        forecast_available=forecast_available,
    )


# ---------------------------------------------------------------------------
# 1. Low water stress — any forecast rain amount
# ---------------------------------------------------------------------------

class TestLowStress:
    def test_no_irrigation_needed_when_stress_low_and_rain_heavy(self):
        action, priority, reason = _call("Low", rain_next_24h=12.0)
        assert "No irrigation" in action
        assert priority == "Low"

    def test_no_irrigation_needed_when_stress_low_and_no_rain(self):
        action, priority, reason = _call("Low", rain_next_24h=0.0)
        assert "No irrigation" in action
        assert priority == "Low"

    def test_reason_mentions_stress_or_no_irrigation(self):
        _, _, reason = _call("Low", rain_next_24h=3.0)
        # reason should explain water stress is low
        assert "stress" in reason.lower() or "no irrigation" in reason.lower()


# ---------------------------------------------------------------------------
# 2. High stress + rain >= 5 mm → delay irrigation (priority NOT low)
# ---------------------------------------------------------------------------

class TestHighStressHeavyRain:
    def test_delay_irrigation_when_rain_at_threshold(self):
        action, priority, reason = _call("High", rain_next_24h=5.0)
        assert "Delay" in action or "delay" in action.lower()
        assert priority != "Low"

    def test_delay_irrigation_when_rain_well_above_threshold(self):
        action, priority, reason = _call("High", rain_next_24h=20.0)
        assert "Delay" in action or "delay" in action.lower()
        assert priority != "Low"

    def test_reason_mentions_rain(self):
        _, _, reason = _call("High", rain_next_24h=8.0)
        assert "rain" in reason.lower() or "rainfall" in reason.lower()


# ---------------------------------------------------------------------------
# 3. High stress + rain < 2 mm → irrigate now, high priority
# ---------------------------------------------------------------------------

class TestHighStressNoRain:
    def test_irrigate_now_when_rain_zero(self):
        action, priority, reason = _call("High", rain_next_24h=0.0)
        assert "Irrigate now" in action or "partial irrigation" in action.lower()
        assert priority == "High"

    def test_irrigate_now_when_rain_just_below_partial_threshold(self):
        action, priority, reason = _call("High", rain_next_24h=1.9)
        assert "Irrigate now" in action or "partial irrigation" in action.lower()
        assert priority == "High"

    def test_reason_mentions_low_forecast_rain(self):
        _, _, reason = _call("High", rain_next_24h=0.5)
        assert "rain" in reason.lower()


# ---------------------------------------------------------------------------
# 4. High stress + rain 2–5 mm during sensitive (critical) stage
# ---------------------------------------------------------------------------

CRITICAL_STAGE_SAMPLES = sorted(CRITICAL_STAGES)  # deterministic order


class TestHighStressPartialRainCriticalStage:
    @pytest.mark.parametrize("stage", CRITICAL_STAGE_SAMPLES)
    def test_partial_irrigation_on_critical_stage(self, stage: str):
        action, priority, reason = _call(
            "High", rain_next_24h=3.0, mango_stage=stage
        )
        # Action should indicate partial irrigation or recheck
        assert (
            "partial irrigation" in action.lower()
            or "recheck" in action.lower()
        )
        # Priority should be high or medium (never low during critical stage)
        assert priority in ("High", "Medium")

    @pytest.mark.parametrize("stage", CRITICAL_STAGE_SAMPLES)
    def test_reason_mentions_critical_stage(self, stage: str):
        _, _, reason = _call("High", rain_next_24h=3.5, mango_stage=stage)
        assert stage in reason or "critical" in reason.lower()

    @pytest.mark.parametrize("rain", [2.0, 3.0, 4.9])
    def test_partial_rain_range_boundary_critical_stage(self, rain: float):
        stage = CRITICAL_STAGE_SAMPLES[0]
        action, priority, _ = _call("High", rain_next_24h=rain, mango_stage=stage)
        assert priority in ("High", "Medium")


# ---------------------------------------------------------------------------
# 5. High stress + rain 2–5 mm during NON-critical stage → delay, not high
# ---------------------------------------------------------------------------

class TestHighStressPartialRainNonCriticalStage:
    def test_delay_irrigation_non_critical_stage(self):
        action, priority, reason = _call(
            "High", rain_next_24h=3.0, mango_stage="Rest / vegetative phase"
        )
        assert "Delay" in action or "delay" in action.lower()

    def test_priority_not_highest_for_non_critical_stage(self):
        # Non-critical stage with moderate rain should be Medium, not High
        _, priority, _ = _call(
            "High", rain_next_24h=3.0, mango_stage="Rest / vegetative phase"
        )
        assert priority == "Medium"

    def test_non_critical_stage_with_boundary_rain(self):
        action, _, _ = _call(
            "High", rain_next_24h=2.0, mango_stage="Flowering"
        )
        assert "Delay" in action or "delay" in action.lower()


# ---------------------------------------------------------------------------
# 6. Medium stress + rain >= 2 mm → wait and monitor
# ---------------------------------------------------------------------------

class TestMediumStressSufficientRain:
    def test_wait_and_monitor_at_partial_threshold(self):
        action, priority, reason = _call("Medium", rain_next_24h=2.0)
        assert "Wait" in action or "monitor" in action.lower()

    def test_wait_and_monitor_above_threshold(self):
        action, _, _ = _call("Medium", rain_next_24h=7.0)
        assert "Wait" in action or "monitor" in action.lower()

    def test_priority_is_low_when_medium_stress_and_good_rain(self):
        _, priority, _ = _call("Medium", rain_next_24h=3.0)
        assert priority == "Low"

    def test_reason_mentions_rain_or_monitor(self):
        _, _, reason = _call("Medium", rain_next_24h=4.0)
        assert "rain" in reason.lower() or "monitor" in reason.lower()


# ---------------------------------------------------------------------------
# 7. Medium stress + rain < 2 mm → monitor closely / consider irrigation
# ---------------------------------------------------------------------------

class TestMediumStressLowRain:
    def test_monitor_closely_when_rain_zero(self):
        action, priority, reason = _call("Medium", rain_next_24h=0.0)
        assert "monitor" in action.lower() or "irrigation" in action.lower()

    def test_monitor_closely_just_below_threshold(self):
        action, priority, _ = _call("Medium", rain_next_24h=1.9)
        assert "monitor" in action.lower() or "irrigation" in action.lower()
        assert priority == "Medium"

    def test_reason_mentions_low_rain_or_depletion(self):
        _, _, reason = _call("Medium", rain_next_24h=1.0)
        assert "rain" in reason.lower() or "depletion" in reason.lower() or "stress" in reason.lower()


# ---------------------------------------------------------------------------
# 8. Forecast unavailable → FAO-56 advisory only, no crash
# ---------------------------------------------------------------------------

class TestForecastUnavailable:
    def test_high_stress_no_forecast_no_crash(self):
        action, priority, reason = _call(
            "High", forecast_available=False, rain_next_24h=None
        )
        assert action  # non-empty
        assert priority in ("High", "Medium", "Low")
        # Should recommend irrigation or note forecast unavailable
        assert (
            "FAO-56" in reason
            or "unavailable" in reason.lower()
            or "irrigate" in action.lower()
        )

    def test_medium_stress_no_forecast_no_crash(self):
        action, priority, reason = _call(
            "Medium", forecast_available=False, rain_next_24h=None
        )
        assert action
        assert priority in ("High", "Medium", "Low")
        assert "unavailable" in reason.lower() or "forecast" in reason.lower()

    def test_low_stress_no_forecast_no_crash(self):
        action, priority, reason = _call(
            "Low", forecast_available=False, rain_next_24h=None
        )
        assert "No irrigation" in action
        assert priority == "Low"

    def test_high_stress_no_forecast_priority_is_high(self):
        _, priority, _ = _call(
            "High", forecast_available=False, rain_next_24h=None
        )
        assert priority == "High"


# ---------------------------------------------------------------------------
# 9. Missing / None rainfall values → no crash, safe advisory output
# ---------------------------------------------------------------------------

class TestNoneRainfall:
    def test_none_rain_high_stress_does_not_crash(self):
        action, priority, reason = _call(
            "High", rain_next_24h=None, forecast_available=True
        )
        # None is treated as 0.0 rain → irrigate now
        assert action
        assert priority == "High"

    def test_none_rain_medium_stress_does_not_crash(self):
        action, priority, reason = _call(
            "Medium", rain_next_24h=None, forecast_available=True
        )
        assert action
        assert priority in ("High", "Medium", "Low")

    def test_none_rain_low_stress_does_not_crash(self):
        action, priority, reason = _call(
            "Low", rain_next_24h=None, forecast_available=True
        )
        assert "No irrigation" in action
        assert priority == "Low"

    def test_none_rain_and_forecast_unavailable_does_not_crash(self):
        action, priority, reason = _call(
            "High", rain_next_24h=None, forecast_available=False
        )
        assert action
        assert reason


# ---------------------------------------------------------------------------
# 10. Unknown / unexpected water stress level → no crash, conservative output
# ---------------------------------------------------------------------------

class TestUnknownStressLevel:
    """
    _decide_advisory checks explicitly for "Low" and "Medium".
    Anything else falls through to the High-stress branch, which is the
    conservative / safe default — it never silently ignores risk.
    """

    def test_unknown_stress_level_does_not_crash(self):
        action, priority, reason = _call("Unknown", rain_next_24h=0.0)
        assert action
        assert priority in ("High", "Medium", "Low")

    def test_unrecognised_stress_level_falls_back_conservatively(self):
        # Falls through to High-stress path → should recommend action, not ignore
        action, _, _ = _call("CRITICAL_EXTRA_LEVEL", rain_next_24h=0.0)
        assert action  # must produce a non-empty advisory

    def test_empty_string_stress_level_does_not_crash(self):
        action, priority, reason = _call("", rain_next_24h=0.0)
        assert action
        assert reason
