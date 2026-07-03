# ET0 Comparison: Open-Meteo vs FAO-56 Penman-Monteith

*Generated: 2026-07-02T22:25:55*

## Result: No overlapping dates

The Open-Meteo ET0 dataset covers **2026-06-21 to 2026-07-03** and the FAO-56 computed
ET0 dataset covers **2025-01-01 to 2026-06-19**. These date ranges do not overlap, so
no day-by-day comparison is possible with current cached data.

**What this means:** Open-Meteo data is fetched for recent and forecast
dates; the FAO-56 water balance is built from NASA POWER historical weather.
After a full `python main.py` run that fetches both sources and they cover
overlapping dates, this comparison will populate automatically.

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

