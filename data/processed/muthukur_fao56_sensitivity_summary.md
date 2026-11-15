# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-11-10
- **Number of days:** 679
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.96 mm/day |
| Mean ETc | 3.67 mm/day |
| Mean root-zone depletion | 102.5 mm |
| High-stress days | 404 (59.5%) |
| Medium-stress days | 48 |
| Low-stress days | 227 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.67 | 68.1 | 409 (60.2%) | +5.00 |
| **1.0** | 126 | 63 | 3.67 | 85.4 | 404 (59.5%) | +0.00 |
| **1.2** | 152 | 76 | 3.67 | 102.5 | 404 (59.5%) | +0.00 |
| **1.5** | 190 | 95 | 3.67 | 127.5 | 411 (60.5%) | +7.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 102.5 | 432 (63.6%) | +28.00 |
| **0.50** | 76 | 102.5 | 404 (59.5%) | +0.00 |
| **0.60** | 91 | 102.5 | 382 (56.3%) | -22.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.30 | -0.37 mm/d | 99.4 | 389 (57.3%) | -15.00 |
| **1.00** | 3.67 | +0.00 mm/d | 102.5 | 404 (59.5%) | +0.00 |
| **1.10** | 4.03 | +0.37 mm/d | 105.5 | 424 (62.4%) | +20.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.2 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **444** (65.4%)
- Mean ETc: 4.03 mm/day
- Mean depletion: 105.5 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **367** (54.0%)
- Mean ETc: 3.30 mm/day
- Mean depletion: 123.8 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.30 | 66.2 | 408 | 60.1% | -0.37 | -36.30 | +4.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.67 | 68.1 | 418 | 61.6% | +0.00 | -34.41 | +14.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.03 | 70.1 | 431 | 63.5% | +0.37 | -32.35 | +27.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.30 | 66.2 | 397 | 58.5% | -0.37 | -36.30 | -7.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.67 | 68.1 | 409 | 60.2% | +0.00 | -34.41 | +5.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.03 | 70.1 | 420 | 61.9% | +0.37 | -32.35 | +16.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.30 | 66.2 | 383 | 56.4% | -0.37 | -36.30 | -21.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.67 | 68.1 | 396 | 58.3% | +0.00 | -34.41 | -8.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.03 | 70.1 | 409 | 60.2% | +0.37 | -32.35 | +5.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.30 | 82.6 | 409 | 60.2% | -0.37 | -19.82 | +5.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.67 | 85.4 | 423 | 62.3% | +0.00 | -17.10 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.03 | 88.0 | 439 | 64.7% | +0.37 | -14.44 | +35.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.30 | 82.6 | 393 | 57.9% | -0.37 | -19.82 | -11.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.67 | 85.4 | 404 | 59.5% | +0.00 | -17.10 | +0.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.03 | 88.0 | 416 | 61.3% | +0.37 | -14.44 | +12.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.30 | 82.6 | 376 | 55.4% | -0.37 | -19.82 | -28.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.67 | 85.4 | 392 | 57.7% | +0.00 | -17.10 | -12.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.03 | 88.0 | 403 | 59.4% | +0.37 | -14.44 | -1.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.30 | 99.4 | 411 | 60.5% | -0.37 | -3.07 | +7.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.67 | 102.5 | 432 | 63.6% | +0.00 | +0.00 | +28.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.03 | 105.5 | 444 | 65.4% | +0.37 | +3.00 | +40.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.30 | 99.4 | 389 | 57.3% | -0.37 | -3.07 | -15.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.67 | 102.5 | 404 | 59.5% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.03 | 105.5 | 424 | 62.4% | +0.37 | +3.00 | +20.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.30 | 99.4 | 370 | 54.5% | -0.37 | -3.07 | -34.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.67 | 102.5 | 382 | 56.3% | +0.00 | +0.00 | -22.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.03 | 105.5 | 399 | 58.8% | +0.37 | +3.00 | -5.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.30 | 123.8 | 415 | 61.1% | -0.37 | +21.33 | +11.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.67 | 127.5 | 427 | 62.9% | +0.00 | +25.01 | +23.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.03 | 131.5 | 438 | 64.5% | +0.37 | +29.05 | +34.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.30 | 123.8 | 394 | 58.0% | -0.37 | +21.33 | -10.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.67 | 127.5 | 411 | 60.5% | +0.00 | +25.01 | +7.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.03 | 131.5 | 422 | 62.1% | +0.37 | +29.05 | +18.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.30 | 123.8 | 367 | 54.0% | -0.37 | +21.33 | -37.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.67 | 127.5 | 384 | 56.5% | +0.00 | +25.01 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.03 | 131.5 | 401 | 59.1% | +0.37 | +29.05 | -3.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._