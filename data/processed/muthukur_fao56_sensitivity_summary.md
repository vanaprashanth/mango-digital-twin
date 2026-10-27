# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-10-19
- **Number of days:** 657
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 5.01 mm/day |
| Mean ETc | 3.72 mm/day |
| Mean root-zone depletion | 105.8 mm |
| High-stress days | 404 (61.5%) |
| Medium-stress days | 48 |
| Low-stress days | 205 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.72 | 70.2 | 409 (62.2%) | +5.00 |
| **1.0** | 126 | 63 | 3.72 | 88.1 | 404 (61.5%) | +0.00 |
| **1.2** | 152 | 76 | 3.72 | 105.8 | 404 (61.5%) | +0.00 |
| **1.5** | 190 | 95 | 3.72 | 131.6 | 411 (62.6%) | +7.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 105.8 | 432 (65.8%) | +28.00 |
| **0.50** | 76 | 105.8 | 404 (61.5%) | +0.00 |
| **0.60** | 91 | 105.8 | 382 (58.1%) | -22.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.35 | -0.37 mm/d | 102.6 | 389 (59.2%) | -15.00 |
| **1.00** | 3.72 | +0.00 mm/d | 105.8 | 404 (61.5%) | +0.00 |
| **1.10** | 4.09 | +0.37 mm/d | 108.9 | 424 (64.5%) | +20.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.2 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **444** (67.6%)
- Mean ETc: 4.09 mm/day
- Mean depletion: 108.9 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **367** (55.9%)
- Mean ETc: 3.35 mm/day
- Mean depletion: 127.8 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.35 | 68.3 | 408 | 62.1% | -0.37 | -37.51 | +4.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.72 | 70.2 | 418 | 63.6% | +0.00 | -35.56 | +14.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.09 | 72.3 | 431 | 65.6% | +0.37 | -33.45 | +27.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.35 | 68.3 | 397 | 60.4% | -0.37 | -37.51 | -7.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.72 | 70.2 | 409 | 62.2% | +0.00 | -35.56 | +5.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.09 | 72.3 | 420 | 63.9% | +0.37 | -33.45 | +16.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.35 | 68.3 | 383 | 58.3% | -0.37 | -37.51 | -21.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.72 | 70.2 | 396 | 60.3% | +0.00 | -35.56 | -8.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.09 | 72.3 | 409 | 62.2% | +0.37 | -33.45 | +5.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.35 | 85.3 | 409 | 62.2% | -0.37 | -20.47 | +5.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.72 | 88.1 | 423 | 64.4% | +0.00 | -17.68 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.09 | 90.9 | 439 | 66.8% | +0.37 | -14.94 | +35.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.35 | 85.3 | 393 | 59.8% | -0.37 | -20.47 | -11.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.72 | 88.1 | 404 | 61.5% | +0.00 | -17.68 | +0.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.09 | 90.9 | 416 | 63.3% | +0.37 | -14.94 | +12.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.35 | 85.3 | 376 | 57.2% | -0.37 | -20.47 | -28.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.72 | 88.1 | 392 | 59.7% | +0.00 | -17.68 | -12.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.09 | 90.9 | 403 | 61.3% | +0.37 | -14.94 | -1.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.35 | 102.6 | 411 | 62.6% | -0.37 | -3.16 | +7.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.72 | 105.8 | 432 | 65.8% | +0.00 | +0.00 | +28.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.09 | 108.9 | 444 | 67.6% | +0.37 | +3.09 | +40.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.35 | 102.6 | 389 | 59.2% | -0.37 | -3.16 | -15.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.72 | 105.8 | 404 | 61.5% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.09 | 108.9 | 424 | 64.5% | +0.37 | +3.09 | +20.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.35 | 102.6 | 370 | 56.3% | -0.37 | -3.16 | -34.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.72 | 105.8 | 382 | 58.1% | +0.00 | +0.00 | -22.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.09 | 108.9 | 399 | 60.7% | +0.37 | +3.09 | -5.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.35 | 127.8 | 415 | 63.2% | -0.37 | +22.06 | +11.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.72 | 131.6 | 427 | 65.0% | +0.00 | +25.83 | +23.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.09 | 135.7 | 438 | 66.7% | +0.37 | +29.95 | +34.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.35 | 127.8 | 394 | 60.0% | -0.37 | +22.06 | -10.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.72 | 131.6 | 411 | 62.6% | +0.00 | +25.83 | +7.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.09 | 135.7 | 422 | 64.2% | +0.37 | +29.95 | +18.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.35 | 127.8 | 367 | 55.9% | -0.37 | +22.06 | -37.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.72 | 131.6 | 384 | 58.5% | +0.00 | +25.83 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.09 | 135.7 | 401 | 61.0% | +0.37 | +29.95 | -3.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._