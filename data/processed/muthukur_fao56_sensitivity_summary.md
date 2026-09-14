# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-09-09
- **Number of days:** 617
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
| Mean root-zone depletion | 105.3 mm |
| High-stress days | 389 (63.0%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.73 | 70.4 | 400 (64.8%) | +11.00 |
| **1.0** | 126 | 63 | 3.73 | 88.0 | 394 (63.9%) | +5.00 |
| **1.2** | 152 | 76 | 3.73 | 105.3 | 389 (63.0%) | +0.00 |
| **1.5** | 190 | 95 | 3.73 | 130.4 | 381 (61.8%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 105.3 | 404 (65.5%) | +15.00 |
| **0.50** | 76 | 105.3 | 389 (63.0%) | +0.00 |
| **0.60** | 91 | 105.3 | 373 (60.5%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.36 | -0.37 mm/d | 101.9 | 378 (61.3%) | -11.00 |
| **1.00** | 3.73 | +0.00 mm/d | 105.3 | 389 (63.0%) | +0.00 |
| **1.10** | 4.10 | +0.37 mm/d | 108.6 | 404 (65.5%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **419** (67.9%)
- Mean ETc: 4.10 mm/day
- Mean depletion: 72.7 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **356** (57.7%)
- Mean ETc: 3.36 mm/day
- Mean depletion: 126.4 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.36 | 68.3 | 399 | 64.7% | -0.37 | -37.04 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.73 | 70.4 | 409 | 66.3% | +0.00 | -34.89 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.10 | 72.7 | 419 | 67.9% | +0.37 | -32.66 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.36 | 68.3 | 388 | 62.9% | -0.37 | -37.04 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.73 | 70.4 | 400 | 64.8% | +0.00 | -34.89 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.10 | 72.7 | 410 | 66.5% | +0.37 | -32.66 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.36 | 68.3 | 365 | 59.2% | -0.37 | -37.04 | -24.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.73 | 70.4 | 388 | 62.9% | +0.00 | -34.89 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.10 | 72.7 | 400 | 64.8% | +0.37 | -32.66 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.36 | 84.9 | 398 | 64.5% | -0.37 | -20.38 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.73 | 88.0 | 408 | 66.1% | +0.00 | -17.32 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.10 | 90.9 | 419 | 67.9% | +0.37 | -14.43 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.36 | 84.9 | 384 | 62.2% | -0.37 | -20.38 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.73 | 88.0 | 394 | 63.9% | +0.00 | -17.32 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.10 | 90.9 | 404 | 65.5% | +0.37 | -14.43 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.36 | 84.9 | 367 | 59.5% | -0.37 | -20.38 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.73 | 88.0 | 383 | 62.1% | +0.00 | -17.32 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.10 | 90.9 | 393 | 63.7% | +0.37 | -14.43 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.36 | 101.9 | 392 | 63.5% | -0.37 | -3.44 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.73 | 105.3 | 404 | 65.5% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.10 | 108.6 | 412 | 66.8% | +0.37 | +3.25 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.36 | 101.9 | 378 | 61.3% | -0.37 | -3.44 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.73 | 105.3 | 389 | 63.0% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.10 | 108.6 | 404 | 65.5% | +0.37 | +3.25 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.36 | 101.9 | 361 | 58.5% | -0.37 | -3.44 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.73 | 105.3 | 373 | 60.5% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.10 | 108.6 | 387 | 62.7% | +0.37 | +3.25 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.36 | 126.4 | 381 | 61.8% | -0.37 | +21.09 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.73 | 130.4 | 392 | 63.5% | +0.00 | +25.13 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.10 | 134.8 | 402 | 65.2% | +0.37 | +29.44 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.36 | 126.4 | 371 | 60.1% | -0.37 | +21.09 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.73 | 130.4 | 381 | 61.8% | +0.00 | +25.13 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.10 | 134.8 | 390 | 63.2% | +0.37 | +29.44 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.36 | 126.4 | 356 | 57.7% | -0.37 | +21.09 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.73 | 130.4 | 369 | 59.8% | +0.00 | +25.13 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.10 | 134.8 | 381 | 61.8% | +0.37 | +29.44 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._