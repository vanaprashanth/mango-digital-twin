# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-08-06
- **Number of days:** 583
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.89 mm/day |
| Mean ETc | 3.73 mm/day |
| Mean root-zone depletion | 103.2 mm |
| High-stress days | 355 (60.9%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.73 | 69.3 | 366 (62.8%) | +11.00 |
| **1.0** | 126 | 63 | 3.73 | 86.4 | 360 (61.8%) | +5.00 |
| **1.2** | 152 | 76 | 3.73 | 103.2 | 355 (60.9%) | +0.00 |
| **1.5** | 190 | 95 | 3.73 | 127.6 | 347 (59.5%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 103.2 | 370 (63.5%) | +15.00 |
| **0.50** | 76 | 103.2 | 355 (60.9%) | +0.00 |
| **0.60** | 91 | 103.2 | 339 (58.1%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.36 | -0.37 mm/d | 99.8 | 344 (59.0%) | -11.00 |
| **1.00** | 3.73 | +0.00 mm/d | 103.2 | 355 (60.9%) | +0.00 |
| **1.10** | 4.10 | +0.37 mm/d | 106.5 | 370 (63.5%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **385** (66.0%)
- Mean ETc: 4.10 mm/day
- Mean depletion: 71.5 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **322** (55.2%)
- Mean ETc: 3.36 mm/day
- Mean depletion: 123.6 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.36 | 67.2 | 365 | 62.6% | -0.37 | -36.02 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.73 | 69.3 | 375 | 64.3% | +0.00 | -33.97 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.10 | 71.5 | 385 | 66.0% | +0.37 | -31.77 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.36 | 67.2 | 354 | 60.7% | -0.37 | -36.02 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.73 | 69.3 | 366 | 62.8% | +0.00 | -33.97 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.10 | 71.5 | 376 | 64.5% | +0.37 | -31.77 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.36 | 67.2 | 338 | 58.0% | -0.37 | -36.02 | -17.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.73 | 69.3 | 353 | 60.5% | +0.00 | -33.97 | -2.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.10 | 71.5 | 366 | 62.8% | +0.37 | -31.77 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.36 | 83.4 | 364 | 62.4% | -0.37 | -19.86 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.73 | 86.4 | 374 | 64.2% | +0.00 | -16.85 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.10 | 89.3 | 385 | 66.0% | +0.37 | -13.95 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.36 | 83.4 | 350 | 60.0% | -0.37 | -19.86 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.73 | 86.4 | 360 | 61.8% | +0.00 | -16.85 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.10 | 89.3 | 370 | 63.5% | +0.37 | -13.95 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.36 | 83.4 | 333 | 57.1% | -0.37 | -19.86 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.73 | 86.4 | 349 | 59.9% | +0.00 | -16.85 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.10 | 89.3 | 359 | 61.6% | +0.37 | -13.95 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.36 | 99.8 | 358 | 61.4% | -0.37 | -3.41 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.73 | 103.2 | 370 | 63.5% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.10 | 106.5 | 378 | 64.8% | +0.37 | +3.28 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.36 | 99.8 | 344 | 59.0% | -0.37 | -3.41 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.73 | 103.2 | 355 | 60.9% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.10 | 106.5 | 370 | 63.5% | +0.37 | +3.28 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.36 | 99.8 | 327 | 56.1% | -0.37 | -3.41 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.73 | 103.2 | 339 | 58.1% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.10 | 106.5 | 353 | 60.5% | +0.37 | +3.28 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.36 | 123.6 | 347 | 59.5% | -0.37 | +20.34 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.73 | 127.6 | 358 | 61.4% | +0.00 | +24.38 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.10 | 132.0 | 368 | 63.1% | +0.37 | +28.79 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.36 | 123.6 | 337 | 57.8% | -0.37 | +20.34 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.73 | 127.6 | 347 | 59.5% | +0.00 | +24.38 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.10 | 132.0 | 356 | 61.1% | +0.37 | +28.79 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.36 | 123.6 | 322 | 55.2% | -0.37 | +20.34 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.73 | 127.6 | 335 | 57.5% | +0.00 | +24.38 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.10 | 132.0 | 347 | 59.5% | +0.37 | +28.79 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._