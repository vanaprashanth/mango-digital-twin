# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-09-13
- **Number of days:** 621
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.97 mm/day |
| Mean ETc | 3.73 mm/day |
| Mean root-zone depletion | 105.6 mm |
| High-stress days | 393 (63.3%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.73 | 70.6 | 404 (65.1%) | +11.00 |
| **1.0** | 126 | 63 | 3.73 | 88.2 | 398 (64.1%) | +5.00 |
| **1.2** | 152 | 76 | 3.73 | 105.6 | 393 (63.3%) | +0.00 |
| **1.5** | 190 | 95 | 3.73 | 130.8 | 385 (62.0%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 105.6 | 408 (65.7%) | +15.00 |
| **0.50** | 76 | 105.6 | 393 (63.3%) | +0.00 |
| **0.60** | 91 | 105.6 | 377 (60.7%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.35 | -0.37 mm/d | 102.1 | 382 (61.5%) | -11.00 |
| **1.00** | 3.73 | +0.00 mm/d | 105.6 | 393 (63.3%) | +0.00 |
| **1.10** | 4.10 | +0.37 mm/d | 108.8 | 408 (65.7%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **423** (68.1%)
- Mean ETc: 4.10 mm/day
- Mean depletion: 72.8 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **360** (58.0%)
- Mean ETc: 3.35 mm/day
- Mean depletion: 126.7 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.35 | 68.4 | 403 | 64.9% | -0.37 | -37.19 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.73 | 70.6 | 413 | 66.5% | +0.00 | -34.99 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.10 | 72.8 | 423 | 68.1% | +0.37 | -32.77 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.35 | 68.4 | 392 | 63.1% | -0.37 | -37.19 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.73 | 70.6 | 404 | 65.1% | +0.00 | -34.99 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.10 | 72.8 | 414 | 66.7% | +0.37 | -32.77 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.35 | 68.4 | 369 | 59.4% | -0.37 | -37.19 | -24.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.73 | 70.6 | 392 | 63.1% | +0.00 | -34.99 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.10 | 72.8 | 404 | 65.1% | +0.37 | -32.77 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.35 | 85.1 | 402 | 64.7% | -0.37 | -20.47 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.73 | 88.2 | 412 | 66.3% | +0.00 | -17.37 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.10 | 91.1 | 423 | 68.1% | +0.37 | -14.49 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.35 | 85.1 | 388 | 62.5% | -0.37 | -20.47 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.73 | 88.2 | 398 | 64.1% | +0.00 | -17.37 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.10 | 91.1 | 408 | 65.7% | +0.37 | -14.49 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.35 | 85.1 | 371 | 59.7% | -0.37 | -20.47 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.73 | 88.2 | 387 | 62.3% | +0.00 | -17.37 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.10 | 91.1 | 397 | 63.9% | +0.37 | -14.49 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.35 | 102.1 | 396 | 63.8% | -0.37 | -3.48 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.73 | 105.6 | 408 | 65.7% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.10 | 108.8 | 416 | 67.0% | +0.37 | +3.23 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.35 | 102.1 | 382 | 61.5% | -0.37 | -3.48 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.73 | 105.6 | 393 | 63.3% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.10 | 108.8 | 408 | 65.7% | +0.37 | +3.23 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.35 | 102.1 | 365 | 58.8% | -0.37 | -3.48 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.73 | 105.6 | 377 | 60.7% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.10 | 108.8 | 391 | 63.0% | +0.37 | +3.23 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.35 | 126.7 | 385 | 62.0% | -0.37 | +21.14 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.73 | 130.8 | 396 | 63.8% | +0.00 | +25.21 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.10 | 135.1 | 406 | 65.4% | +0.37 | +29.50 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.35 | 126.7 | 375 | 60.4% | -0.37 | +21.14 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.73 | 130.8 | 385 | 62.0% | +0.00 | +25.21 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.10 | 135.1 | 394 | 63.5% | +0.37 | +29.50 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.35 | 126.7 | 360 | 58.0% | -0.37 | +21.14 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.73 | 130.8 | 373 | 60.1% | +0.00 | +25.21 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.10 | 135.1 | 385 | 62.0% | +0.37 | +29.50 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._