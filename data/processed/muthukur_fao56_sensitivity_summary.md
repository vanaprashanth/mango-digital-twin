# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-11-03
- **Number of days:** 672
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.98 mm/day |
| Mean ETc | 3.69 mm/day |
| Mean root-zone depletion | 103.5 mm |
| High-stress days | 404 (60.1%) |
| Medium-stress days | 48 |
| Low-stress days | 220 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.69 | 68.8 | 409 (60.9%) | +5.00 |
| **1.0** | 126 | 63 | 3.69 | 86.2 | 404 (60.1%) | +0.00 |
| **1.2** | 152 | 76 | 3.69 | 103.5 | 404 (60.1%) | +0.00 |
| **1.5** | 190 | 95 | 3.69 | 128.8 | 411 (61.2%) | +7.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 103.5 | 432 (64.3%) | +28.00 |
| **0.50** | 76 | 103.5 | 404 (60.1%) | +0.00 |
| **0.60** | 91 | 103.5 | 382 (56.9%) | -22.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.32 | -0.37 mm/d | 100.4 | 389 (57.9%) | -15.00 |
| **1.00** | 3.69 | +0.00 mm/d | 103.5 | 404 (60.1%) | +0.00 |
| **1.10** | 4.05 | +0.37 mm/d | 106.6 | 424 (63.1%) | +20.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.2 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **444** (66.1%)
- Mean ETc: 4.05 mm/day
- Mean depletion: 106.6 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **367** (54.6%)
- Mean ETc: 3.32 mm/day
- Mean depletion: 125.1 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.32 | 66.8 | 408 | 60.7% | -0.37 | -36.68 | +4.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.69 | 68.8 | 418 | 62.2% | +0.00 | -34.77 | +14.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.05 | 70.8 | 431 | 64.1% | +0.37 | -32.69 | +27.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.32 | 66.8 | 397 | 59.1% | -0.37 | -36.68 | -7.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.69 | 68.8 | 409 | 60.9% | +0.00 | -34.77 | +5.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.05 | 70.8 | 420 | 62.5% | +0.37 | -32.69 | +16.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.32 | 66.8 | 383 | 57.0% | -0.37 | -36.68 | -21.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.69 | 68.8 | 396 | 58.9% | +0.00 | -34.77 | -8.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.05 | 70.8 | 409 | 60.9% | +0.37 | -32.69 | +5.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.32 | 83.5 | 409 | 60.9% | -0.37 | -20.03 | +5.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.69 | 86.2 | 423 | 63.0% | +0.00 | -17.28 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.05 | 88.9 | 439 | 65.3% | +0.37 | -14.59 | +35.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.32 | 83.5 | 393 | 58.5% | -0.37 | -20.03 | -11.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.69 | 86.2 | 404 | 60.1% | +0.00 | -17.28 | +0.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.05 | 88.9 | 416 | 61.9% | +0.37 | -14.59 | +12.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.32 | 83.5 | 376 | 56.0% | -0.37 | -20.03 | -28.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.69 | 86.2 | 392 | 58.3% | +0.00 | -17.28 | -12.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.05 | 88.9 | 403 | 60.0% | +0.37 | -14.59 | -1.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.32 | 100.4 | 411 | 61.2% | -0.37 | -3.10 | +7.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.69 | 103.5 | 432 | 64.3% | +0.00 | +0.00 | +28.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.05 | 106.6 | 444 | 66.1% | +0.37 | +3.03 | +40.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.32 | 100.4 | 389 | 57.9% | -0.37 | -3.10 | -15.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.69 | 103.5 | 404 | 60.1% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.05 | 106.6 | 424 | 63.1% | +0.37 | +3.03 | +20.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.32 | 100.4 | 370 | 55.1% | -0.37 | -3.10 | -34.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.69 | 103.5 | 382 | 56.9% | +0.00 | +0.00 | -22.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.05 | 106.6 | 399 | 59.4% | +0.37 | +3.03 | -5.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.32 | 125.1 | 415 | 61.8% | -0.37 | +21.56 | +11.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.69 | 128.8 | 427 | 63.5% | +0.00 | +25.27 | +23.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.05 | 132.9 | 438 | 65.2% | +0.37 | +29.35 | +34.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.32 | 125.1 | 394 | 58.6% | -0.37 | +21.56 | -10.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.69 | 128.8 | 411 | 61.2% | +0.00 | +25.27 | +7.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.05 | 132.9 | 422 | 62.8% | +0.37 | +29.35 | +18.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.32 | 125.1 | 367 | 54.6% | -0.37 | +21.56 | -37.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.69 | 128.8 | 384 | 57.1% | +0.00 | +25.27 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.05 | 132.9 | 401 | 59.7% | +0.37 | +29.35 | -3.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._