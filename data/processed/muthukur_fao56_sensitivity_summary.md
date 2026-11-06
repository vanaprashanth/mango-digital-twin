# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-11-01
- **Number of days:** 670
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
| Mean ETc | 3.69 mm/day |
| Mean root-zone depletion | 103.8 mm |
| High-stress days | 404 (60.3%) |
| Medium-stress days | 48 |
| Low-stress days | 218 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.69 | 69.0 | 409 (61.0%) | +5.00 |
| **1.0** | 126 | 63 | 3.69 | 86.5 | 404 (60.3%) | +0.00 |
| **1.2** | 152 | 76 | 3.69 | 103.8 | 404 (60.3%) | +0.00 |
| **1.5** | 190 | 95 | 3.69 | 129.2 | 411 (61.3%) | +7.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 103.8 | 432 (64.5%) | +28.00 |
| **0.50** | 76 | 103.8 | 404 (60.3%) | +0.00 |
| **0.60** | 91 | 103.8 | 382 (57.0%) | -22.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.32 | -0.37 mm/d | 100.7 | 389 (58.1%) | -15.00 |
| **1.00** | 3.69 | +0.00 mm/d | 103.8 | 404 (60.3%) | +0.00 |
| **1.10** | 4.06 | +0.37 mm/d | 106.9 | 424 (63.3%) | +20.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.2 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **444** (66.3%)
- Mean ETc: 4.06 mm/day
- Mean depletion: 106.9 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **367** (54.8%)
- Mean ETc: 3.32 mm/day
- Mean depletion: 125.5 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.32 | 67.0 | 408 | 60.9% | -0.37 | -36.79 | +4.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.69 | 69.0 | 418 | 62.4% | +0.00 | -34.87 | +14.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.06 | 71.0 | 431 | 64.3% | +0.37 | -32.79 | +27.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.32 | 67.0 | 397 | 59.2% | -0.37 | -36.79 | -7.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.69 | 69.0 | 409 | 61.0% | +0.00 | -34.87 | +5.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.06 | 71.0 | 420 | 62.7% | +0.37 | -32.79 | +16.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.32 | 67.0 | 383 | 57.2% | -0.37 | -36.79 | -21.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.69 | 69.0 | 396 | 59.1% | +0.00 | -34.87 | -8.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.06 | 71.0 | 409 | 61.0% | +0.37 | -32.79 | +5.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.32 | 83.7 | 409 | 61.0% | -0.37 | -20.08 | +5.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.69 | 86.5 | 423 | 63.1% | +0.00 | -17.33 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.06 | 89.2 | 439 | 65.5% | +0.37 | -14.64 | +35.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.32 | 83.7 | 393 | 58.7% | -0.37 | -20.08 | -11.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.69 | 86.5 | 404 | 60.3% | +0.00 | -17.33 | +0.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.06 | 89.2 | 416 | 62.1% | +0.37 | -14.64 | +12.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.32 | 83.7 | 376 | 56.1% | -0.37 | -20.08 | -28.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.69 | 86.5 | 392 | 58.5% | +0.00 | -17.33 | -12.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.06 | 89.2 | 403 | 60.1% | +0.37 | -14.64 | -1.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.32 | 100.7 | 411 | 61.3% | -0.37 | -3.11 | +7.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.69 | 103.8 | 432 | 64.5% | +0.00 | +0.00 | +28.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.06 | 106.9 | 444 | 66.3% | +0.37 | +3.04 | +40.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.32 | 100.7 | 389 | 58.1% | -0.37 | -3.11 | -15.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.69 | 103.8 | 404 | 60.3% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.06 | 106.9 | 424 | 63.3% | +0.37 | +3.04 | +20.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.32 | 100.7 | 370 | 55.2% | -0.37 | -3.11 | -34.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.69 | 103.8 | 382 | 57.0% | +0.00 | +0.00 | -22.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.06 | 106.9 | 399 | 59.5% | +0.37 | +3.04 | -5.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.32 | 125.5 | 415 | 61.9% | -0.37 | +21.63 | +11.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.69 | 129.2 | 427 | 63.7% | +0.00 | +25.35 | +23.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.06 | 133.3 | 438 | 65.4% | +0.37 | +29.43 | +34.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.32 | 125.5 | 394 | 58.8% | -0.37 | +21.63 | -10.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.69 | 129.2 | 411 | 61.3% | +0.00 | +25.35 | +7.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.06 | 133.3 | 422 | 63.0% | +0.37 | +29.43 | +18.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.32 | 125.5 | 367 | 54.8% | -0.37 | +21.63 | -37.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.69 | 129.2 | 384 | 57.3% | +0.00 | +25.35 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.06 | 133.3 | 401 | 59.9% | +0.37 | +29.43 | -3.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._