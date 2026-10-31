# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-10-25
- **Number of days:** 663
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 5.00 mm/day |
| Mean ETc | 3.70 mm/day |
| Mean root-zone depletion | 104.8 mm |
| High-stress days | 404 (60.9%) |
| Medium-stress days | 48 |
| Low-stress days | 211 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.70 | 69.6 | 409 (61.7%) | +5.00 |
| **1.0** | 126 | 63 | 3.70 | 87.3 | 404 (60.9%) | +0.00 |
| **1.2** | 152 | 76 | 3.70 | 104.8 | 404 (60.9%) | +0.00 |
| **1.5** | 190 | 95 | 3.70 | 130.5 | 411 (62.0%) | +7.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 104.8 | 432 (65.2%) | +28.00 |
| **0.50** | 76 | 104.8 | 404 (60.9%) | +0.00 |
| **0.60** | 91 | 104.8 | 382 (57.6%) | -22.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.33 | -0.37 mm/d | 101.7 | 389 (58.7%) | -15.00 |
| **1.00** | 3.70 | +0.00 mm/d | 104.8 | 404 (60.9%) | +0.00 |
| **1.10** | 4.08 | +0.37 mm/d | 107.9 | 424 (64.0%) | +20.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.2 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **444** (67.0%)
- Mean ETc: 4.08 mm/day
- Mean depletion: 107.9 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **367** (55.4%)
- Mean ETc: 3.33 mm/day
- Mean depletion: 126.7 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.33 | 67.7 | 408 | 61.5% | -0.37 | -37.16 | +4.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.70 | 69.6 | 418 | 63.0% | +0.00 | -35.24 | +14.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.08 | 71.7 | 431 | 65.0% | +0.37 | -33.15 | +27.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.33 | 67.7 | 397 | 59.9% | -0.37 | -37.16 | -7.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.70 | 69.6 | 409 | 61.7% | +0.00 | -35.24 | +5.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.08 | 71.7 | 420 | 63.4% | +0.37 | -33.15 | +16.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.33 | 67.7 | 383 | 57.8% | -0.37 | -37.16 | -21.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.70 | 69.6 | 396 | 59.7% | +0.00 | -35.24 | -8.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.08 | 71.7 | 409 | 61.7% | +0.37 | -33.15 | +5.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.33 | 84.6 | 409 | 61.7% | -0.37 | -20.29 | +5.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.70 | 87.3 | 423 | 63.8% | +0.00 | -17.52 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.08 | 90.0 | 439 | 66.2% | +0.37 | -14.80 | +35.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.33 | 84.6 | 393 | 59.3% | -0.37 | -20.29 | -11.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.70 | 87.3 | 404 | 60.9% | +0.00 | -17.52 | +0.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.08 | 90.0 | 416 | 62.8% | +0.37 | -14.80 | +12.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.33 | 84.6 | 376 | 56.7% | -0.37 | -20.29 | -28.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.70 | 87.3 | 392 | 59.1% | +0.00 | -17.52 | -12.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.08 | 90.0 | 403 | 60.8% | +0.37 | -14.80 | -1.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.33 | 101.7 | 411 | 62.0% | -0.37 | -3.13 | +7.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.70 | 104.8 | 432 | 65.2% | +0.00 | +0.00 | +28.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.08 | 107.9 | 444 | 67.0% | +0.37 | +3.06 | +40.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.33 | 101.7 | 389 | 58.7% | -0.37 | -3.13 | -15.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.70 | 104.8 | 404 | 60.9% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.08 | 107.9 | 424 | 64.0% | +0.37 | +3.06 | +20.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.33 | 101.7 | 370 | 55.8% | -0.37 | -3.13 | -34.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.70 | 104.8 | 382 | 57.6% | +0.00 | +0.00 | -22.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.08 | 107.9 | 399 | 60.2% | +0.37 | +3.06 | -5.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.33 | 126.7 | 415 | 62.6% | -0.37 | +21.86 | +11.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.70 | 130.5 | 427 | 64.4% | +0.00 | +25.61 | +23.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.08 | 134.6 | 438 | 66.1% | +0.37 | +29.73 | +34.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.33 | 126.7 | 394 | 59.4% | -0.37 | +21.86 | -10.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.70 | 130.5 | 411 | 62.0% | +0.00 | +25.61 | +7.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.08 | 134.6 | 422 | 63.6% | +0.37 | +29.73 | +18.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.33 | 126.7 | 367 | 55.4% | -0.37 | +21.86 | -37.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.70 | 130.5 | 384 | 57.9% | +0.00 | +25.61 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.08 | 134.6 | 401 | 60.5% | +0.37 | +29.73 | -3.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._