# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-08-17
- **Number of days:** 594
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
| Mean ETc | 3.71 mm/day |
| Mean root-zone depletion | 103.7 mm |
| High-stress days | 366 (61.6%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.71 | 69.4 | 377 (63.5%) | +11.00 |
| **1.0** | 126 | 63 | 3.71 | 86.7 | 371 (62.5%) | +5.00 |
| **1.2** | 152 | 76 | 3.71 | 103.7 | 366 (61.6%) | +0.00 |
| **1.5** | 190 | 95 | 3.71 | 128.3 | 358 (60.3%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 103.7 | 381 (64.1%) | +15.00 |
| **0.50** | 76 | 103.7 | 366 (61.6%) | +0.00 |
| **0.60** | 91 | 103.7 | 350 (58.9%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.34 | -0.37 mm/d | 100.2 | 355 (59.8%) | -11.00 |
| **1.00** | 3.71 | +0.00 mm/d | 103.7 | 366 (61.6%) | +0.00 |
| **1.10** | 4.08 | +0.37 mm/d | 107.0 | 381 (64.1%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **396** (66.7%)
- Mean ETc: 4.08 mm/day
- Mean depletion: 71.7 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **333** (56.1%)
- Mean ETc: 3.34 mm/day
- Mean depletion: 124.2 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.34 | 67.3 | 376 | 63.3% | -0.37 | -36.42 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.71 | 69.4 | 386 | 65.0% | +0.00 | -34.28 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.08 | 71.7 | 396 | 66.7% | +0.37 | -32.03 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.34 | 67.3 | 357 | 60.1% | -0.37 | -36.42 | -9.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.71 | 69.4 | 377 | 63.5% | +0.00 | -34.28 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.08 | 71.7 | 387 | 65.2% | +0.37 | -32.03 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.34 | 67.3 | 338 | 56.9% | -0.37 | -36.42 | -28.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.71 | 69.4 | 357 | 60.1% | +0.00 | -34.28 | -9.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.08 | 71.7 | 377 | 63.5% | +0.37 | -32.03 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.34 | 83.6 | 375 | 63.1% | -0.37 | -20.09 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.71 | 86.7 | 385 | 64.8% | +0.00 | -17.01 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.08 | 89.6 | 396 | 66.7% | +0.37 | -14.07 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.34 | 83.6 | 361 | 60.8% | -0.37 | -20.09 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.71 | 86.7 | 371 | 62.5% | +0.00 | -17.01 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.08 | 89.6 | 381 | 64.1% | +0.37 | -14.07 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.34 | 83.6 | 336 | 56.6% | -0.37 | -20.09 | -30.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.71 | 86.7 | 360 | 60.6% | +0.00 | -17.01 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.08 | 89.6 | 370 | 62.3% | +0.37 | -14.07 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.34 | 100.2 | 369 | 62.1% | -0.37 | -3.48 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.71 | 103.7 | 381 | 64.1% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.08 | 107.0 | 389 | 65.5% | +0.37 | +3.32 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.34 | 100.2 | 355 | 59.8% | -0.37 | -3.48 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.71 | 103.7 | 366 | 61.6% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.08 | 107.0 | 381 | 64.1% | +0.37 | +3.32 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.34 | 100.2 | 338 | 56.9% | -0.37 | -3.48 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.71 | 103.7 | 350 | 58.9% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.08 | 107.0 | 364 | 61.3% | +0.37 | +3.32 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.34 | 124.2 | 358 | 60.3% | -0.37 | +20.53 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.71 | 128.3 | 369 | 62.1% | +0.00 | +24.64 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.08 | 132.8 | 379 | 63.8% | +0.37 | +29.05 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.34 | 124.2 | 348 | 58.6% | -0.37 | +20.53 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.71 | 128.3 | 358 | 60.3% | +0.00 | +24.64 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.08 | 132.8 | 367 | 61.8% | +0.37 | +29.05 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.34 | 124.2 | 333 | 56.1% | -0.37 | +20.53 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.71 | 128.3 | 346 | 58.2% | +0.00 | +24.64 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.08 | 132.8 | 358 | 60.3% | +0.37 | +29.05 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._