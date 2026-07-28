# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-07-23
- **Number of days:** 568
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
| Mean root-zone depletion | 102.2 mm |
| High-stress days | 340 (59.9%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.75 | 68.7 | 351 (61.8%) | +11.00 |
| **1.0** | 126 | 63 | 3.75 | 85.6 | 345 (60.7%) | +5.00 |
| **1.2** | 152 | 76 | 3.75 | 102.2 | 340 (59.9%) | +0.00 |
| **1.5** | 190 | 95 | 3.75 | 126.2 | 332 (58.5%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 102.2 | 355 (62.5%) | +15.00 |
| **0.50** | 76 | 102.2 | 340 (59.9%) | +0.00 |
| **0.60** | 91 | 102.2 | 324 (57.0%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.38 | -0.38 mm/d | 98.8 | 329 (57.9%) | -11.00 |
| **1.00** | 3.75 | +0.00 mm/d | 102.2 | 340 (59.9%) | +0.00 |
| **1.10** | 4.13 | +0.38 mm/d | 105.5 | 355 (62.5%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **370** (65.1%)
- Mean ETc: 4.13 mm/day
- Mean depletion: 70.9 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **307** (54.0%)
- Mean ETc: 3.38 mm/day
- Mean depletion: 122.2 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.38 | 66.7 | 350 | 61.6% | -0.38 | -35.55 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.75 | 68.7 | 360 | 63.4% | +0.00 | -33.53 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.13 | 70.9 | 370 | 65.1% | +0.38 | -31.32 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.38 | 66.7 | 339 | 59.7% | -0.38 | -35.55 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.75 | 68.7 | 351 | 61.8% | +0.00 | -33.53 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.13 | 70.9 | 361 | 63.6% | +0.38 | -31.32 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.38 | 66.7 | 326 | 57.4% | -0.38 | -35.55 | -14.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.75 | 68.7 | 339 | 59.7% | +0.00 | -33.53 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.13 | 70.9 | 351 | 61.8% | +0.38 | -31.32 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.38 | 82.6 | 349 | 61.4% | -0.38 | -19.63 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.75 | 85.6 | 359 | 63.2% | +0.00 | -16.63 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.13 | 88.5 | 370 | 65.1% | +0.38 | -13.70 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.38 | 82.6 | 335 | 59.0% | -0.38 | -19.63 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.75 | 85.6 | 345 | 60.7% | +0.00 | -16.63 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.13 | 88.5 | 355 | 62.5% | +0.38 | -13.70 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.38 | 82.6 | 318 | 56.0% | -0.38 | -19.63 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.75 | 85.6 | 334 | 58.8% | +0.00 | -16.63 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.13 | 88.5 | 344 | 60.6% | +0.38 | -13.70 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.38 | 98.8 | 343 | 60.4% | -0.38 | -3.41 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.75 | 102.2 | 355 | 62.5% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.13 | 105.5 | 363 | 63.9% | +0.38 | +3.32 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.38 | 98.8 | 329 | 57.9% | -0.38 | -3.41 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.75 | 102.2 | 340 | 59.9% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.13 | 105.5 | 355 | 62.5% | +0.38 | +3.32 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.38 | 98.8 | 312 | 54.9% | -0.38 | -3.41 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.75 | 102.2 | 324 | 57.0% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.13 | 105.5 | 338 | 59.5% | +0.38 | +3.32 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.38 | 122.2 | 332 | 58.5% | -0.38 | +19.96 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.75 | 126.2 | 343 | 60.4% | +0.00 | +24.03 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.13 | 130.7 | 353 | 62.1% | +0.38 | +28.50 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.38 | 122.2 | 322 | 56.7% | -0.38 | +19.96 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.75 | 126.2 | 332 | 58.5% | +0.00 | +24.03 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.13 | 130.7 | 341 | 60.0% | +0.38 | +28.50 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.38 | 122.2 | 307 | 54.0% | -0.38 | +19.96 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.75 | 126.2 | 320 | 56.3% | +0.00 | +24.03 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.13 | 130.7 | 332 | 58.5% | +0.38 | +28.50 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._