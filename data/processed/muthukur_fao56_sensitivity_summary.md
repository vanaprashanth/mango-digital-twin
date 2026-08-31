# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-08-26
- **Number of days:** 603
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
| Mean ETc | 3.74 mm/day |
| Mean root-zone depletion | 104.3 mm |
| High-stress days | 375 (62.2%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.74 | 69.8 | 386 (64.0%) | +11.00 |
| **1.0** | 126 | 63 | 3.74 | 87.2 | 380 (63.0%) | +5.00 |
| **1.2** | 152 | 76 | 3.74 | 104.3 | 375 (62.2%) | +0.00 |
| **1.5** | 190 | 95 | 3.74 | 129.2 | 367 (60.9%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 104.3 | 390 (64.7%) | +15.00 |
| **0.50** | 76 | 104.3 | 375 (62.2%) | +0.00 |
| **0.60** | 91 | 104.3 | 359 (59.5%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.37 | -0.37 mm/d | 101.0 | 364 (60.4%) | -11.00 |
| **1.00** | 3.74 | +0.00 mm/d | 104.3 | 375 (62.2%) | +0.00 |
| **1.10** | 4.12 | +0.37 mm/d | 107.6 | 390 (64.7%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **405** (67.2%)
- Mean ETc: 4.12 mm/day
- Mean depletion: 72.0 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **342** (56.7%)
- Mean ETc: 3.37 mm/day
- Mean depletion: 125.2 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.37 | 67.8 | 385 | 63.9% | -0.37 | -36.55 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.74 | 69.8 | 395 | 65.5% | +0.00 | -34.52 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.12 | 72.0 | 405 | 67.2% | +0.37 | -32.30 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.37 | 67.8 | 374 | 62.0% | -0.37 | -36.55 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.74 | 69.8 | 386 | 64.0% | +0.00 | -34.52 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.12 | 72.0 | 396 | 65.7% | +0.37 | -32.30 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.37 | 67.8 | 351 | 58.2% | -0.37 | -36.55 | -24.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.74 | 69.8 | 374 | 62.0% | +0.00 | -34.52 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.12 | 72.0 | 386 | 64.0% | +0.37 | -32.30 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.37 | 84.2 | 384 | 63.7% | -0.37 | -20.09 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.74 | 87.2 | 394 | 65.3% | +0.00 | -17.13 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.12 | 90.1 | 405 | 67.2% | +0.37 | -14.23 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.37 | 84.2 | 370 | 61.4% | -0.37 | -20.09 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.74 | 87.2 | 380 | 63.0% | +0.00 | -17.13 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.12 | 90.1 | 390 | 64.7% | +0.37 | -14.23 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.37 | 84.2 | 353 | 58.5% | -0.37 | -20.09 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.74 | 87.2 | 369 | 61.2% | +0.00 | -17.13 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.12 | 90.1 | 379 | 62.9% | +0.37 | -14.23 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.37 | 101.0 | 378 | 62.7% | -0.37 | -3.34 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.74 | 104.3 | 390 | 64.7% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.12 | 107.6 | 398 | 66.0% | +0.37 | +3.27 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.37 | 101.0 | 364 | 60.4% | -0.37 | -3.34 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.74 | 104.3 | 375 | 62.2% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.12 | 107.6 | 390 | 64.7% | +0.37 | +3.27 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.37 | 101.0 | 347 | 57.5% | -0.37 | -3.34 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.74 | 104.3 | 359 | 59.5% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.12 | 107.6 | 373 | 61.9% | +0.37 | +3.27 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.37 | 125.2 | 367 | 60.9% | -0.37 | +20.87 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.74 | 129.2 | 378 | 62.7% | +0.00 | +24.83 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.12 | 133.5 | 388 | 64.3% | +0.37 | +29.18 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.37 | 125.2 | 357 | 59.2% | -0.37 | +20.87 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.74 | 129.2 | 367 | 60.9% | +0.00 | +24.83 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.12 | 133.5 | 376 | 62.4% | +0.37 | +29.18 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.37 | 125.2 | 342 | 56.7% | -0.37 | +20.87 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.74 | 129.2 | 355 | 58.9% | +0.00 | +24.83 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.12 | 133.5 | 367 | 60.9% | +0.37 | +29.18 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._