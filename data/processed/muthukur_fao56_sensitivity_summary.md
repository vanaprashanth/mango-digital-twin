# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-09-06
- **Number of days:** 614
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
| Mean root-zone depletion | 105.1 mm |
| High-stress days | 386 (62.9%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.73 | 70.3 | 397 (64.7%) | +11.00 |
| **1.0** | 126 | 63 | 3.73 | 87.8 | 391 (63.7%) | +5.00 |
| **1.2** | 152 | 76 | 3.73 | 105.1 | 386 (62.9%) | +0.00 |
| **1.5** | 190 | 95 | 3.73 | 130.2 | 378 (61.6%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 105.1 | 401 (65.3%) | +15.00 |
| **0.50** | 76 | 105.1 | 386 (62.9%) | +0.00 |
| **0.60** | 91 | 105.1 | 370 (60.3%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.36 | -0.37 mm/d | 101.7 | 375 (61.1%) | -11.00 |
| **1.00** | 3.73 | +0.00 mm/d | 105.1 | 386 (62.9%) | +0.00 |
| **1.10** | 4.11 | +0.37 mm/d | 108.4 | 401 (65.3%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **416** (67.8%)
- Mean ETc: 4.11 mm/day
- Mean depletion: 72.5 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **353** (57.5%)
- Mean ETc: 3.36 mm/day
- Mean depletion: 126.1 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.36 | 68.2 | 396 | 64.5% | -0.37 | -36.94 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.73 | 70.3 | 406 | 66.1% | +0.00 | -34.81 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.11 | 72.5 | 416 | 67.8% | +0.37 | -32.58 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.36 | 68.2 | 385 | 62.7% | -0.37 | -36.94 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.73 | 70.3 | 397 | 64.7% | +0.00 | -34.81 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.11 | 72.5 | 407 | 66.3% | +0.37 | -32.58 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.36 | 68.2 | 362 | 59.0% | -0.37 | -36.94 | -24.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.73 | 70.3 | 385 | 62.7% | +0.00 | -34.81 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.11 | 72.5 | 397 | 64.7% | +0.37 | -32.58 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.36 | 84.8 | 395 | 64.3% | -0.37 | -20.32 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.73 | 87.8 | 405 | 66.0% | +0.00 | -17.28 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.11 | 90.7 | 416 | 67.8% | +0.37 | -14.38 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.36 | 84.8 | 381 | 62.0% | -0.37 | -20.32 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.73 | 87.8 | 391 | 63.7% | +0.00 | -17.28 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.11 | 90.7 | 401 | 65.3% | +0.37 | -14.38 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.36 | 84.8 | 364 | 59.3% | -0.37 | -20.32 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.73 | 87.8 | 380 | 61.9% | +0.00 | -17.28 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.11 | 90.7 | 390 | 63.5% | +0.37 | -14.38 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.36 | 101.7 | 389 | 63.4% | -0.37 | -3.42 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.73 | 105.1 | 401 | 65.3% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.11 | 108.4 | 409 | 66.6% | +0.37 | +3.26 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.36 | 101.7 | 375 | 61.1% | -0.37 | -3.42 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.73 | 105.1 | 386 | 62.9% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.11 | 108.4 | 401 | 65.3% | +0.37 | +3.26 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.36 | 101.7 | 358 | 58.3% | -0.37 | -3.42 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.73 | 105.1 | 370 | 60.3% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.11 | 108.4 | 384 | 62.5% | +0.37 | +3.26 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.36 | 126.1 | 378 | 61.6% | -0.37 | +21.05 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.73 | 130.2 | 389 | 63.4% | +0.00 | +25.07 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.11 | 134.5 | 399 | 65.0% | +0.37 | +29.39 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.36 | 126.1 | 368 | 59.9% | -0.37 | +21.05 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.73 | 130.2 | 378 | 61.6% | +0.00 | +25.07 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.11 | 134.5 | 387 | 63.0% | +0.37 | +29.39 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.36 | 126.1 | 353 | 57.5% | -0.37 | +21.05 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.73 | 130.2 | 366 | 59.6% | +0.00 | +25.07 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.11 | 134.5 | 378 | 61.6% | +0.37 | +29.39 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._