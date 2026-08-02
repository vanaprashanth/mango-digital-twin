# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-07-28
- **Number of days:** 574
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.90 mm/day |
| Mean ETc | 3.75 mm/day |
| Mean root-zone depletion | 102.7 mm |
| High-stress days | 346 (60.3%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.75 | 69.0 | 357 (62.2%) | +11.00 |
| **1.0** | 126 | 63 | 3.75 | 86.0 | 351 (61.1%) | +5.00 |
| **1.2** | 152 | 76 | 3.75 | 102.7 | 346 (60.3%) | +0.00 |
| **1.5** | 190 | 95 | 3.75 | 126.9 | 338 (58.9%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 102.7 | 361 (62.9%) | +15.00 |
| **0.50** | 76 | 102.7 | 346 (60.3%) | +0.00 |
| **0.60** | 91 | 102.7 | 330 (57.5%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.37 | -0.37 mm/d | 99.3 | 335 (58.4%) | -11.00 |
| **1.00** | 3.75 | +0.00 mm/d | 102.7 | 346 (60.3%) | +0.00 |
| **1.10** | 4.12 | +0.37 mm/d | 106.0 | 361 (62.9%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **376** (65.5%)
- Mean ETc: 4.12 mm/day
- Mean depletion: 71.2 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **313** (54.5%)
- Mean ETc: 3.37 mm/day
- Mean depletion: 122.8 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.37 | 67.0 | 356 | 62.0% | -0.37 | -35.72 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.75 | 69.0 | 366 | 63.8% | +0.00 | -33.71 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.12 | 71.2 | 376 | 65.5% | +0.37 | -31.52 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.37 | 67.0 | 345 | 60.1% | -0.37 | -35.72 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.75 | 69.0 | 357 | 62.2% | +0.00 | -33.71 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.12 | 71.2 | 367 | 63.9% | +0.37 | -31.52 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.37 | 67.0 | 332 | 57.8% | -0.37 | -35.72 | -14.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.75 | 69.0 | 345 | 60.1% | +0.00 | -33.71 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.12 | 71.2 | 357 | 62.2% | +0.37 | -31.52 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.37 | 83.0 | 355 | 61.9% | -0.37 | -19.71 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.75 | 86.0 | 365 | 63.6% | +0.00 | -16.72 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.12 | 88.9 | 376 | 65.5% | +0.37 | -13.81 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.37 | 83.0 | 341 | 59.4% | -0.37 | -19.71 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.75 | 86.0 | 351 | 61.1% | +0.00 | -16.72 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.12 | 88.9 | 361 | 62.9% | +0.37 | -13.81 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.37 | 83.0 | 324 | 56.5% | -0.37 | -19.71 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.75 | 86.0 | 340 | 59.2% | +0.00 | -16.72 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.12 | 88.9 | 350 | 61.0% | +0.37 | -13.81 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.37 | 99.3 | 349 | 60.8% | -0.37 | -3.39 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.75 | 102.7 | 361 | 62.9% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.12 | 106.0 | 369 | 64.3% | +0.37 | +3.30 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.37 | 99.3 | 335 | 58.4% | -0.37 | -3.39 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.75 | 102.7 | 346 | 60.3% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.12 | 106.0 | 361 | 62.9% | +0.37 | +3.30 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.37 | 99.3 | 318 | 55.4% | -0.37 | -3.39 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.75 | 102.7 | 330 | 57.5% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.12 | 106.0 | 344 | 59.9% | +0.37 | +3.30 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.37 | 122.8 | 338 | 58.9% | -0.37 | +20.13 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.75 | 126.9 | 349 | 60.8% | +0.00 | +24.17 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.12 | 131.3 | 359 | 62.5% | +0.37 | +28.61 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.37 | 122.8 | 328 | 57.1% | -0.37 | +20.13 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.75 | 126.9 | 338 | 58.9% | +0.00 | +24.17 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.12 | 131.3 | 347 | 60.5% | +0.37 | +28.61 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.37 | 122.8 | 313 | 54.5% | -0.37 | +20.13 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.75 | 126.9 | 326 | 56.8% | +0.00 | +24.17 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.12 | 131.3 | 338 | 58.9% | +0.37 | +28.61 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._