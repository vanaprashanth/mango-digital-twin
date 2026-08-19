# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-08-14
- **Number of days:** 591
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
| Mean root-zone depletion | 103.6 mm |
| High-stress days | 363 (61.4%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.72 | 69.4 | 374 (63.3%) | +11.00 |
| **1.0** | 126 | 63 | 3.72 | 86.6 | 368 (62.3%) | +5.00 |
| **1.2** | 152 | 76 | 3.72 | 103.6 | 363 (61.4%) | +0.00 |
| **1.5** | 190 | 95 | 3.72 | 128.1 | 355 (60.1%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 103.6 | 378 (64.0%) | +15.00 |
| **0.50** | 76 | 103.6 | 363 (61.4%) | +0.00 |
| **0.60** | 91 | 103.6 | 347 (58.7%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.34 | -0.37 mm/d | 100.1 | 352 (59.6%) | -11.00 |
| **1.00** | 3.72 | +0.00 mm/d | 103.6 | 363 (61.4%) | +0.00 |
| **1.10** | 4.09 | +0.37 mm/d | 106.9 | 378 (64.0%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **393** (66.5%)
- Mean ETc: 4.09 mm/day
- Mean depletion: 71.6 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **330** (55.8%)
- Mean ETc: 3.34 mm/day
- Mean depletion: 124.0 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.34 | 67.3 | 373 | 63.1% | -0.37 | -36.31 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.72 | 69.4 | 383 | 64.8% | +0.00 | -34.20 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.09 | 71.6 | 393 | 66.5% | +0.37 | -31.97 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.34 | 67.3 | 354 | 59.9% | -0.37 | -36.31 | -9.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.72 | 69.4 | 374 | 63.3% | +0.00 | -34.20 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.09 | 71.6 | 384 | 65.0% | +0.37 | -31.97 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.34 | 67.3 | 338 | 57.2% | -0.37 | -36.31 | -25.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.72 | 69.4 | 354 | 59.9% | +0.00 | -34.20 | -9.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.09 | 71.6 | 374 | 63.3% | +0.37 | -31.97 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.34 | 83.5 | 372 | 62.9% | -0.37 | -20.03 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.72 | 86.6 | 382 | 64.6% | +0.00 | -16.97 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.09 | 89.5 | 393 | 66.5% | +0.37 | -14.04 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.34 | 83.5 | 358 | 60.6% | -0.37 | -20.03 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.72 | 86.6 | 368 | 62.3% | +0.00 | -16.97 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.09 | 89.5 | 378 | 64.0% | +0.37 | -14.04 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.34 | 83.5 | 333 | 56.4% | -0.37 | -20.03 | -30.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.72 | 86.6 | 357 | 60.4% | +0.00 | -16.97 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.09 | 89.5 | 367 | 62.1% | +0.37 | -14.04 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.34 | 100.1 | 366 | 61.9% | -0.37 | -3.45 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.72 | 103.6 | 378 | 64.0% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.09 | 106.9 | 386 | 65.3% | +0.37 | +3.30 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.34 | 100.1 | 352 | 59.6% | -0.37 | -3.45 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.72 | 103.6 | 363 | 61.4% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.09 | 106.9 | 378 | 64.0% | +0.37 | +3.30 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.34 | 100.1 | 335 | 56.7% | -0.37 | -3.45 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.72 | 103.6 | 347 | 58.7% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.09 | 106.9 | 361 | 61.1% | +0.37 | +3.30 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.34 | 124.0 | 355 | 60.1% | -0.37 | +20.48 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.72 | 128.1 | 366 | 61.9% | +0.00 | +24.57 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.09 | 132.5 | 376 | 63.6% | +0.37 | +28.98 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.34 | 124.0 | 345 | 58.4% | -0.37 | +20.48 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.72 | 128.1 | 355 | 60.1% | +0.00 | +24.57 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.09 | 132.5 | 364 | 61.6% | +0.37 | +28.98 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.34 | 124.0 | 330 | 55.8% | -0.37 | +20.48 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.72 | 128.1 | 343 | 58.0% | +0.00 | +24.57 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.09 | 132.5 | 355 | 60.1% | +0.37 | +28.98 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._