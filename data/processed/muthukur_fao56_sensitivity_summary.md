# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-10-28
- **Number of days:** 666
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.99 mm/day |
| Mean ETc | 3.70 mm/day |
| Mean root-zone depletion | 104.4 mm |
| High-stress days | 404 (60.7%) |
| Medium-stress days | 48 |
| Low-stress days | 214 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.70 | 69.3 | 409 (61.4%) | +5.00 |
| **1.0** | 126 | 63 | 3.70 | 86.9 | 404 (60.7%) | +0.00 |
| **1.2** | 152 | 76 | 3.70 | 104.4 | 404 (60.7%) | +0.00 |
| **1.5** | 190 | 95 | 3.70 | 129.9 | 411 (61.7%) | +7.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 104.4 | 432 (64.9%) | +28.00 |
| **0.50** | 76 | 104.4 | 404 (60.7%) | +0.00 |
| **0.60** | 91 | 104.4 | 382 (57.4%) | -22.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.33 | -0.37 mm/d | 101.3 | 389 (58.4%) | -15.00 |
| **1.00** | 3.70 | +0.00 mm/d | 104.4 | 404 (60.7%) | +0.00 |
| **1.10** | 4.07 | +0.37 mm/d | 107.4 | 424 (63.7%) | +20.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.2 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **444** (66.7%)
- Mean ETc: 4.07 mm/day
- Mean depletion: 107.4 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **367** (55.1%)
- Mean ETc: 3.33 mm/day
- Mean depletion: 126.1 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.33 | 67.4 | 408 | 61.3% | -0.37 | -37.00 | +4.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.70 | 69.3 | 418 | 62.8% | +0.00 | -35.08 | +14.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.07 | 71.4 | 431 | 64.7% | +0.37 | -33.00 | +27.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.33 | 67.4 | 397 | 59.6% | -0.37 | -37.00 | -7.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.70 | 69.3 | 409 | 61.4% | +0.00 | -35.08 | +5.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.07 | 71.4 | 420 | 63.1% | +0.37 | -33.00 | +16.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.33 | 67.4 | 383 | 57.5% | -0.37 | -37.00 | -21.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.70 | 69.3 | 396 | 59.5% | +0.00 | -35.08 | -8.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.07 | 71.4 | 409 | 61.4% | +0.37 | -33.00 | +5.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.33 | 84.2 | 409 | 61.4% | -0.37 | -20.20 | +5.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.70 | 86.9 | 423 | 63.5% | +0.00 | -17.44 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.07 | 89.6 | 439 | 65.9% | +0.37 | -14.73 | +35.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.33 | 84.2 | 393 | 59.0% | -0.37 | -20.20 | -11.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.70 | 86.9 | 404 | 60.7% | +0.00 | -17.44 | +0.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.07 | 89.6 | 416 | 62.5% | +0.37 | -14.73 | +12.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.33 | 84.2 | 376 | 56.5% | -0.37 | -20.20 | -28.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.70 | 86.9 | 392 | 58.9% | +0.00 | -17.44 | -12.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.07 | 89.6 | 403 | 60.5% | +0.37 | -14.73 | -1.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.33 | 101.3 | 411 | 61.7% | -0.37 | -3.12 | +7.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.70 | 104.4 | 432 | 64.9% | +0.00 | +0.00 | +28.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.07 | 107.4 | 444 | 66.7% | +0.37 | +3.05 | +40.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.33 | 101.3 | 389 | 58.4% | -0.37 | -3.12 | -15.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.70 | 104.4 | 404 | 60.7% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.07 | 107.4 | 424 | 63.7% | +0.37 | +3.05 | +20.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.33 | 101.3 | 370 | 55.6% | -0.37 | -3.12 | -34.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.70 | 104.4 | 382 | 57.4% | +0.00 | +0.00 | -22.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.07 | 107.4 | 399 | 59.9% | +0.37 | +3.05 | -5.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.33 | 126.1 | 415 | 62.3% | -0.37 | +21.76 | +11.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.70 | 129.9 | 427 | 64.1% | +0.00 | +25.50 | +23.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.07 | 134.0 | 438 | 65.8% | +0.37 | +29.60 | +34.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.33 | 126.1 | 394 | 59.2% | -0.37 | +21.76 | -10.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.70 | 129.9 | 411 | 61.7% | +0.00 | +25.50 | +7.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.07 | 134.0 | 422 | 63.4% | +0.37 | +29.60 | +18.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.33 | 126.1 | 367 | 55.1% | -0.37 | +21.76 | -37.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.70 | 129.9 | 384 | 57.7% | +0.00 | +25.50 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.07 | 134.0 | 401 | 60.2% | +0.37 | +29.60 | -3.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._