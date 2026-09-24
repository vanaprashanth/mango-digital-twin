# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-09-19
- **Number of days:** 627
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
| Mean ETc | 3.71 mm/day |
| Mean root-zone depletion | 105.9 mm |
| High-stress days | 399 (63.6%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.71 | 70.7 | 410 (65.4%) | +11.00 |
| **1.0** | 126 | 63 | 3.71 | 88.4 | 404 (64.4%) | +5.00 |
| **1.2** | 152 | 76 | 3.71 | 105.9 | 399 (63.6%) | +0.00 |
| **1.5** | 190 | 95 | 3.71 | 131.2 | 391 (62.4%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 105.9 | 414 (66.0%) | +15.00 |
| **0.50** | 76 | 105.9 | 399 (63.6%) | +0.00 |
| **0.60** | 91 | 105.9 | 383 (61.1%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.34 | -0.37 mm/d | 102.3 | 388 (61.9%) | -11.00 |
| **1.00** | 3.71 | +0.00 mm/d | 105.9 | 399 (63.6%) | +0.00 |
| **1.10** | 4.09 | +0.37 mm/d | 109.1 | 414 (66.0%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **429** (68.4%)
- Mean ETc: 4.09 mm/day
- Mean depletion: 72.9 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **366** (58.4%)
- Mean ETc: 3.34 mm/day
- Mean depletion: 127.1 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.34 | 68.4 | 408 | 65.1% | -0.37 | -37.42 | +9.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.71 | 70.7 | 419 | 66.8% | +0.00 | -35.14 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.09 | 72.9 | 429 | 68.4% | +0.37 | -32.92 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.34 | 68.4 | 396 | 63.2% | -0.37 | -37.42 | -3.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.71 | 70.7 | 410 | 65.4% | +0.00 | -35.14 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.09 | 72.9 | 420 | 67.0% | +0.37 | -32.92 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.34 | 68.4 | 372 | 59.3% | -0.37 | -37.42 | -27.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.71 | 70.7 | 397 | 63.3% | +0.00 | -35.14 | -2.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.09 | 72.9 | 409 | 65.2% | +0.37 | -32.92 | +10.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.34 | 85.2 | 408 | 65.1% | -0.37 | -20.62 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.71 | 88.4 | 418 | 66.7% | +0.00 | -17.44 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.09 | 91.3 | 429 | 68.4% | +0.37 | -14.57 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.34 | 85.2 | 393 | 62.7% | -0.37 | -20.62 | -6.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.71 | 88.4 | 404 | 64.4% | +0.00 | -17.44 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.09 | 91.3 | 414 | 66.0% | +0.37 | -14.57 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.34 | 85.2 | 375 | 59.8% | -0.37 | -20.62 | -24.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.71 | 88.4 | 393 | 62.7% | +0.00 | -17.44 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.09 | 91.3 | 403 | 64.3% | +0.37 | -14.57 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.34 | 102.3 | 402 | 64.1% | -0.37 | -3.54 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.71 | 105.9 | 414 | 66.0% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.09 | 109.1 | 422 | 67.3% | +0.37 | +3.22 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.34 | 102.3 | 388 | 61.9% | -0.37 | -3.54 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.71 | 105.9 | 399 | 63.6% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.09 | 109.1 | 414 | 66.0% | +0.37 | +3.22 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.34 | 102.3 | 370 | 59.0% | -0.37 | -3.54 | -29.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.71 | 105.9 | 383 | 61.1% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.09 | 109.1 | 397 | 63.3% | +0.37 | +3.22 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.34 | 127.1 | 391 | 62.4% | -0.37 | +21.19 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.71 | 131.2 | 402 | 64.1% | +0.00 | +25.33 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.09 | 135.5 | 412 | 65.7% | +0.37 | +29.60 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.34 | 127.1 | 381 | 60.8% | -0.37 | +21.19 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.71 | 131.2 | 391 | 62.4% | +0.00 | +25.33 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.09 | 135.5 | 400 | 63.8% | +0.37 | +29.60 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.34 | 127.1 | 366 | 58.4% | -0.37 | +21.19 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.71 | 131.2 | 379 | 60.5% | +0.00 | +25.33 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.09 | 135.5 | 391 | 62.4% | +0.37 | +29.60 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._