# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-07-19
- **Number of days:** 564
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.91 mm/day |
| Mean ETc | 3.76 mm/day |
| Mean root-zone depletion | 101.9 mm |
| High-stress days | 336 (59.6%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.76 | 68.5 | 347 (61.5%) | +11.00 |
| **1.0** | 126 | 63 | 3.76 | 85.3 | 341 (60.5%) | +5.00 |
| **1.2** | 152 | 76 | 3.76 | 101.9 | 336 (59.6%) | +0.00 |
| **1.5** | 190 | 95 | 3.76 | 125.8 | 328 (58.2%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 101.9 | 351 (62.2%) | +15.00 |
| **0.50** | 76 | 101.9 | 336 (59.6%) | +0.00 |
| **0.60** | 91 | 101.9 | 320 (56.7%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.38 | -0.38 mm/d | 98.5 | 325 (57.6%) | -11.00 |
| **1.00** | 3.76 | +0.00 mm/d | 101.9 | 336 (59.6%) | +0.00 |
| **1.10** | 4.14 | +0.38 mm/d | 105.2 | 351 (62.2%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **366** (64.9%)
- Mean ETc: 4.14 mm/day
- Mean depletion: 70.7 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **303** (53.7%)
- Mean ETc: 3.38 mm/day
- Mean depletion: 121.7 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.38 | 66.5 | 346 | 61.4% | -0.38 | -35.43 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.76 | 68.5 | 356 | 63.1% | +0.00 | -33.41 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.14 | 70.7 | 366 | 64.9% | +0.38 | -31.20 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.38 | 66.5 | 335 | 59.4% | -0.38 | -35.43 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.76 | 68.5 | 347 | 61.5% | +0.00 | -33.41 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.14 | 70.7 | 357 | 63.3% | +0.38 | -31.20 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.38 | 66.5 | 322 | 57.1% | -0.38 | -35.43 | -14.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.76 | 68.5 | 335 | 59.4% | +0.00 | -33.41 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.14 | 70.7 | 347 | 61.5% | +0.38 | -31.20 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.38 | 82.3 | 345 | 61.2% | -0.38 | -19.58 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.76 | 85.3 | 355 | 62.9% | +0.00 | -16.57 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.14 | 88.3 | 366 | 64.9% | +0.38 | -13.62 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.38 | 82.3 | 331 | 58.7% | -0.38 | -19.58 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.76 | 85.3 | 341 | 60.5% | +0.00 | -16.57 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.14 | 88.3 | 351 | 62.2% | +0.38 | -13.62 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.38 | 82.3 | 314 | 55.7% | -0.38 | -19.58 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.76 | 85.3 | 330 | 58.5% | +0.00 | -16.57 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.14 | 88.3 | 340 | 60.3% | +0.38 | -13.62 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.38 | 98.5 | 339 | 60.1% | -0.38 | -3.42 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.76 | 101.9 | 351 | 62.2% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.14 | 105.2 | 359 | 63.6% | +0.38 | +3.34 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.38 | 98.5 | 325 | 57.6% | -0.38 | -3.42 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.76 | 101.9 | 336 | 59.6% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.14 | 105.2 | 351 | 62.2% | +0.38 | +3.34 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.38 | 98.5 | 308 | 54.6% | -0.38 | -3.42 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.76 | 101.9 | 320 | 56.7% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.14 | 105.2 | 334 | 59.2% | +0.38 | +3.34 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.38 | 121.7 | 328 | 58.2% | -0.38 | +19.85 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.76 | 125.8 | 339 | 60.1% | +0.00 | +23.93 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.14 | 130.3 | 349 | 61.9% | +0.38 | +28.43 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.38 | 121.7 | 318 | 56.4% | -0.38 | +19.85 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.76 | 125.8 | 328 | 58.2% | +0.00 | +23.93 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.14 | 130.3 | 337 | 59.8% | +0.38 | +28.43 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.38 | 121.7 | 303 | 53.7% | -0.38 | +19.85 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.76 | 125.8 | 316 | 56.0% | +0.00 | +23.93 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.14 | 130.3 | 328 | 58.2% | +0.38 | +28.43 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._