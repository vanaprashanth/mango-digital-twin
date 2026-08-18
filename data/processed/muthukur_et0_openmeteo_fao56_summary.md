# ET0 Comparison: Open-Meteo vs FAO-56 Penman-Monteith

*Generated: 2026-08-18T03:24:15*

## Summary

| Metric | Value |
|--------|-------|
| Matched days | 2 |
| Date range | 2026-08-11 to 2026-08-12 |
| Open-Meteo date coverage | 2026-08-11 to 2026-08-24 |
| FAO-56 date coverage | 2025-01-01 to 2026-08-12 |
| Mean Open-Meteo ET0 | 5.950 mm/day |
| Mean FAO-56 ET0 | 4.972 mm/day |
| Mean difference (Open-Meteo − FAO-56) | 0.978 mm/day |
| Mean absolute difference | 0.978 mm/day |
| Max absolute difference | 0.990 mm/day |


## Interpretation

A positive mean difference means Open-Meteo estimates higher ET0 than
FAO-56 Penman-Monteith (computed from NASA POWER weather) on average, and
vice versa. Differences < 0.5 mm/day are within normal inter-source
variability.

## Limitations

- **Source-to-source comparison only**: neither ET0 series has been
  validated against on-site lysimeter or eddy-covariance measurements.
- **Different input data**: Open-Meteo uses its own NWP weather model;
  this project's FAO-56 ET0 uses NASA POWER reanalysis weather.
- **Different formulations**: Open-Meteo publishes its own ET0 estimate;
  this project applies the standard FAO-56 Penman-Monteith formula
  independently. Both use the same reference crop definition, but input
  fields and computation details may differ.
- **Limited overlap window**: Open-Meteo data is only fetched for
  recent/forecast dates; NASA POWER data covers the historical period.
  Overlap may be zero or very small depending on when `python main.py`
  was last run.
- Differences < 0.5 mm/day are within normal inter-source variability
  for reference evapotranspiration and do not indicate an error.

