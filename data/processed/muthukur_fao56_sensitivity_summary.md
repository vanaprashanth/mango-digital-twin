# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-08-16
- **Number of days:** 593
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.89 mm/day |
| Mean ETc | 3.71 mm/day |
| Mean root-zone depletion | 103.7 mm |
| High-stress days | 365 (61.5%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.71 | 69.4 | 376 (63.4%) | +11.00 |
| **1.0** | 126 | 63 | 3.71 | 86.7 | 370 (62.4%) | +5.00 |
| **1.2** | 152 | 76 | 3.71 | 103.7 | 365 (61.5%) | +0.00 |
| **1.5** | 190 | 95 | 3.71 | 128.3 | 357 (60.2%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 103.7 | 380 (64.1%) | +15.00 |
| **0.50** | 76 | 103.7 | 365 (61.5%) | +0.00 |
| **0.60** | 91 | 103.7 | 349 (58.9%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.34 | -0.37 mm/d | 100.2 | 354 (59.7%) | -11.00 |
| **1.00** | 3.71 | +0.00 mm/d | 103.7 | 365 (61.5%) | +0.00 |
| **1.10** | 4.08 | +0.37 mm/d | 107.0 | 380 (64.1%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **395** (66.6%)
- Mean ETc: 4.08 mm/day
- Mean depletion: 71.6 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **332** (56.0%)
- Mean ETc: 3.34 mm/day
- Mean depletion: 124.2 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.34 | 67.3 | 375 | 63.2% | -0.37 | -36.38 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.71 | 69.4 | 385 | 64.9% | +0.00 | -34.25 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.08 | 71.6 | 395 | 66.6% | +0.37 | -32.01 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.34 | 67.3 | 356 | 60.0% | -0.37 | -36.38 | -9.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.71 | 69.4 | 376 | 63.4% | +0.00 | -34.25 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.08 | 71.6 | 386 | 65.1% | +0.37 | -32.01 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.34 | 67.3 | 338 | 57.0% | -0.37 | -36.38 | -27.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.71 | 69.4 | 356 | 60.0% | +0.00 | -34.25 | -9.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.08 | 71.6 | 376 | 63.4% | +0.37 | -32.01 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.34 | 83.6 | 374 | 63.1% | -0.37 | -20.07 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.71 | 86.7 | 384 | 64.8% | +0.00 | -16.99 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.08 | 89.6 | 395 | 66.6% | +0.37 | -14.06 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.34 | 83.6 | 360 | 60.7% | -0.37 | -20.07 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.71 | 86.7 | 370 | 62.4% | +0.00 | -16.99 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.08 | 89.6 | 380 | 64.1% | +0.37 | -14.06 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.34 | 83.6 | 335 | 56.5% | -0.37 | -20.07 | -30.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.71 | 86.7 | 359 | 60.5% | +0.00 | -16.99 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.08 | 89.6 | 369 | 62.2% | +0.37 | -14.06 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.34 | 100.2 | 368 | 62.1% | -0.37 | -3.47 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.71 | 103.7 | 380 | 64.1% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.08 | 107.0 | 388 | 65.4% | +0.37 | +3.31 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.34 | 100.2 | 354 | 59.7% | -0.37 | -3.47 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.71 | 103.7 | 365 | 61.5% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.08 | 107.0 | 380 | 64.1% | +0.37 | +3.31 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.34 | 100.2 | 337 | 56.8% | -0.37 | -3.47 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.71 | 103.7 | 349 | 58.9% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.08 | 107.0 | 363 | 61.2% | +0.37 | +3.31 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.34 | 124.2 | 357 | 60.2% | -0.37 | +20.52 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.71 | 128.3 | 368 | 62.1% | +0.00 | +24.61 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.08 | 132.7 | 378 | 63.7% | +0.37 | +29.03 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.34 | 124.2 | 347 | 58.5% | -0.37 | +20.52 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.71 | 128.3 | 357 | 60.2% | +0.00 | +24.61 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.08 | 132.7 | 366 | 61.7% | +0.37 | +29.03 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.34 | 124.2 | 332 | 56.0% | -0.37 | +20.52 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.71 | 128.3 | 345 | 58.2% | +0.00 | +24.61 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.08 | 132.7 | 357 | 60.2% | +0.37 | +29.03 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._