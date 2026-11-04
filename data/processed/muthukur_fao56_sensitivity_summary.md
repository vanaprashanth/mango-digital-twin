# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-10-30
- **Number of days:** 668
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
| Mean root-zone depletion | 104.1 mm |
| High-stress days | 404 (60.5%) |
| Medium-stress days | 48 |
| Low-stress days | 216 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.70 | 69.1 | 409 (61.2%) | +5.00 |
| **1.0** | 126 | 63 | 3.70 | 86.7 | 404 (60.5%) | +0.00 |
| **1.2** | 152 | 76 | 3.70 | 104.1 | 404 (60.5%) | +0.00 |
| **1.5** | 190 | 95 | 3.70 | 129.5 | 411 (61.5%) | +7.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 104.1 | 432 (64.7%) | +28.00 |
| **0.50** | 76 | 104.1 | 404 (60.5%) | +0.00 |
| **0.60** | 91 | 104.1 | 382 (57.2%) | -22.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.33 | -0.37 mm/d | 101.0 | 389 (58.2%) | -15.00 |
| **1.00** | 3.70 | +0.00 mm/d | 104.1 | 404 (60.5%) | +0.00 |
| **1.10** | 4.07 | +0.37 mm/d | 107.1 | 424 (63.5%) | +20.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.2 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **444** (66.5%)
- Mean ETc: 4.07 mm/day
- Mean depletion: 107.1 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **367** (54.9%)
- Mean ETc: 3.33 mm/day
- Mean depletion: 125.8 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.33 | 67.2 | 408 | 61.1% | -0.37 | -36.89 | +4.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.70 | 69.1 | 418 | 62.6% | +0.00 | -34.98 | +14.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.07 | 71.2 | 431 | 64.5% | +0.37 | -32.90 | +27.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.33 | 67.2 | 397 | 59.4% | -0.37 | -36.89 | -7.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.70 | 69.1 | 409 | 61.2% | +0.00 | -34.98 | +5.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.07 | 71.2 | 420 | 62.9% | +0.37 | -32.90 | +16.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.33 | 67.2 | 383 | 57.3% | -0.37 | -36.89 | -21.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.70 | 69.1 | 396 | 59.3% | +0.00 | -34.98 | -8.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.07 | 71.2 | 409 | 61.2% | +0.37 | -32.90 | +5.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.33 | 84.0 | 409 | 61.2% | -0.37 | -20.14 | +5.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.70 | 86.7 | 423 | 63.3% | +0.00 | -17.39 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.07 | 89.4 | 439 | 65.7% | +0.37 | -14.69 | +35.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.33 | 84.0 | 393 | 58.8% | -0.37 | -20.14 | -11.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.70 | 86.7 | 404 | 60.5% | +0.00 | -17.39 | +0.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.07 | 89.4 | 416 | 62.3% | +0.37 | -14.69 | +12.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.33 | 84.0 | 376 | 56.3% | -0.37 | -20.14 | -28.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.70 | 86.7 | 392 | 58.7% | +0.00 | -17.39 | -12.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.07 | 89.4 | 403 | 60.3% | +0.37 | -14.69 | -1.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.33 | 101.0 | 411 | 61.5% | -0.37 | -3.11 | +7.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.70 | 104.1 | 432 | 64.7% | +0.00 | +0.00 | +28.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.07 | 107.1 | 444 | 66.5% | +0.37 | +3.04 | +40.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.33 | 101.0 | 389 | 58.2% | -0.37 | -3.11 | -15.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.70 | 104.1 | 404 | 60.5% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.07 | 107.1 | 424 | 63.5% | +0.37 | +3.04 | +20.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.33 | 101.0 | 370 | 55.4% | -0.37 | -3.11 | -34.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.70 | 104.1 | 382 | 57.2% | +0.00 | +0.00 | -22.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.07 | 107.1 | 399 | 59.7% | +0.37 | +3.04 | -5.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.33 | 125.8 | 415 | 62.1% | -0.37 | +21.70 | +11.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.70 | 129.5 | 427 | 63.9% | +0.00 | +25.42 | +23.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.07 | 133.6 | 438 | 65.6% | +0.37 | +29.51 | +34.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.33 | 125.8 | 394 | 59.0% | -0.37 | +21.70 | -10.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.70 | 129.5 | 411 | 61.5% | +0.00 | +25.42 | +7.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.07 | 133.6 | 422 | 63.2% | +0.37 | +29.51 | +18.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.33 | 125.8 | 367 | 54.9% | -0.37 | +21.70 | -37.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.70 | 129.5 | 384 | 57.5% | +0.00 | +25.42 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.07 | 133.6 | 401 | 60.0% | +0.37 | +29.51 | -3.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._