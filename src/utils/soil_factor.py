"""
Shared soil-adjusted irrigation factor utility.

This is the single source of truth for the soil water-retention adjustment
factor. Both risk engines (src/risk/historical_risk_engine.py and
src/risk/open_meteo_risk_engine.py) and the Streamlit dashboard
(app/streamlit_app.py) import these two functions from here, so the same
soil values always produce the same factor everywhere in the project.

Before this module existed, the dashboard had its own copy of
soil_factor_label() — same logic, but a second copy that could drift out
of sync. Consolidating here removes that risk.
"""


def calculate_soil_irrigation_factor(soil_lookup: dict[str, float]) -> float:
    """
    Estimate a soil water-retention adjustment factor for irrigation risk.

    Higher clay and organic carbon content increase water-holding capacity
    and push the factor below 1.0 (reduces irrigation risk). Higher sand
    content drains faster and pushes the factor above 1.0 (increases
    irrigation risk). The factor is clipped to a plausible [0.7, 1.3] band
    so a single soil property cannot dominate the result.

    This is a simple, transparent heuristic — see ROADMAP.md item 11
    (physics-informed irrigation stress model) for a more rigorous
    successor based on FAO-56 soil-water balance and field capacity /
    wilting point estimates.
    """

    clay_pct = soil_lookup.get("clay", 25.0)
    sand_pct = soil_lookup.get("sand", 40.0)
    soc_gkg = soil_lookup.get("soc", 10.0)

    factor = 1.0
    factor -= 0.004 * (clay_pct - 20.0)
    factor -= 0.010 * (soc_gkg - 10.0)
    factor += 0.004 * (sand_pct - 40.0)

    return max(0.7, min(factor, 1.3))


def soil_factor_label(factor: float) -> str:
    """Human-readable explanation of a soil irrigation factor value."""
    if factor < 0.95:
        return "Reduces irrigation risk"
    elif factor > 1.05:
        return "Increases irrigation risk"
    return "Neutral soil effect"
