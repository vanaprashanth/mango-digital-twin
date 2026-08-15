# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-08-10
- **Number of days:** 587
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
| Mean ETc | 3.72 mm/day |
| Mean root-zone depletion | 103.4 mm |
| High-stress days | 359 (61.2%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.72 | 69.3 | 370 (63.0%) | +11.00 |
| **1.0** | 126 | 63 | 3.72 | 86.5 | 364 (62.0%) | +5.00 |
| **1.2** | 152 | 76 | 3.72 | 103.4 | 359 (61.2%) | +0.00 |
| **1.5** | 190 | 95 | 3.72 | 127.9 | 351 (59.8%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 103.4 | 374 (63.7%) | +15.00 |
| **0.50** | 76 | 103.4 | 359 (61.2%) | +0.00 |
| **0.60** | 91 | 103.4 | 343 (58.4%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.35 | -0.37 mm/d | 100.0 | 348 (59.3%) | -11.00 |
| **1.00** | 3.72 | +0.00 mm/d | 103.4 | 359 (61.2%) | +0.00 |
| **1.10** | 4.09 | +0.37 mm/d | 106.7 | 374 (63.7%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **389** (66.3%)
- Mean ETc: 4.09 mm/day
- Mean depletion: 71.5 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **326** (55.5%)
- Mean ETc: 3.35 mm/day
- Mean depletion: 123.8 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.35 | 67.2 | 369 | 62.9% | -0.37 | -36.16 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.72 | 69.3 | 379 | 64.6% | +0.00 | -34.08 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.09 | 71.5 | 389 | 66.3% | +0.37 | -31.87 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.35 | 67.2 | 354 | 60.3% | -0.37 | -36.16 | -5.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.72 | 69.3 | 370 | 63.0% | +0.00 | -34.08 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.09 | 71.5 | 380 | 64.7% | +0.37 | -31.87 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.35 | 67.2 | 338 | 57.6% | -0.37 | -36.16 | -21.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.72 | 69.3 | 353 | 60.1% | +0.00 | -34.08 | -6.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.09 | 71.5 | 370 | 63.0% | +0.37 | -31.87 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.35 | 83.5 | 368 | 62.7% | -0.37 | -19.94 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.72 | 86.5 | 378 | 64.4% | +0.00 | -16.91 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.09 | 89.4 | 389 | 66.3% | +0.37 | -14.00 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.35 | 83.5 | 354 | 60.3% | -0.37 | -19.94 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.72 | 86.5 | 364 | 62.0% | +0.00 | -16.91 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.09 | 89.4 | 374 | 63.7% | +0.37 | -14.00 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.35 | 83.5 | 333 | 56.7% | -0.37 | -19.94 | -26.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.72 | 86.5 | 353 | 60.1% | +0.00 | -16.91 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.09 | 89.4 | 363 | 61.8% | +0.37 | -14.00 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.35 | 100.0 | 362 | 61.7% | -0.37 | -3.43 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.72 | 103.4 | 374 | 63.7% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.09 | 106.7 | 382 | 65.1% | +0.37 | +3.29 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.35 | 100.0 | 348 | 59.3% | -0.37 | -3.43 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.72 | 103.4 | 359 | 61.2% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.09 | 106.7 | 374 | 63.7% | +0.37 | +3.29 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.35 | 100.0 | 331 | 56.4% | -0.37 | -3.43 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.72 | 103.4 | 343 | 58.4% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.09 | 106.7 | 357 | 60.8% | +0.37 | +3.29 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.35 | 123.8 | 351 | 59.8% | -0.37 | +20.42 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.72 | 127.9 | 362 | 61.7% | +0.00 | +24.48 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.09 | 132.3 | 372 | 63.4% | +0.37 | +28.88 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.35 | 123.8 | 341 | 58.1% | -0.37 | +20.42 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.72 | 127.9 | 351 | 59.8% | +0.00 | +24.48 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.09 | 132.3 | 360 | 61.3% | +0.37 | +28.88 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.35 | 123.8 | 326 | 55.5% | -0.37 | +20.42 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.72 | 127.9 | 339 | 57.8% | +0.00 | +24.48 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.09 | 132.3 | 351 | 59.8% | +0.37 | +28.88 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._