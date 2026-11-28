# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-11-23
- **Number of days:** 692
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.94 mm/day |
| Mean ETc | 3.65 mm/day |
| Mean root-zone depletion | 101.7 mm |
| High-stress days | 403 (58.2%) |
| Medium-stress days | 51 |
| Low-stress days | 238 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.65 | 67.2 | 409 (59.1%) | +6.00 |
| **1.0** | 126 | 63 | 3.65 | 84.4 | 403 (58.2%) | +0.00 |
| **1.2** | 152 | 76 | 3.65 | 101.7 | 403 (58.2%) | +0.00 |
| **1.5** | 190 | 95 | 3.65 | 127.9 | 409 (59.1%) | +6.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 101.7 | 429 (62.0%) | +26.00 |
| **0.50** | 76 | 101.7 | 403 (58.2%) | +0.00 |
| **0.60** | 91 | 101.7 | 382 (55.2%) | -21.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.28 | -0.36 mm/d | 98.3 | 388 (56.1%) | -15.00 |
| **1.00** | 3.65 | +0.00 mm/d | 101.7 | 403 (58.2%) | +0.00 |
| **1.10** | 4.01 | +0.36 mm/d | 105.1 | 424 (61.3%) | +21.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.2 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **442** (63.9%)
- Mean ETc: 4.01 mm/day
- Mean depletion: 105.1 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **366** (52.9%)
- Mean ETc: 3.28 mm/day
- Mean depletion: 123.7 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.28 | 65.2 | 408 | 59.0% | -0.36 | -36.42 | +5.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.65 | 67.2 | 418 | 60.4% | +0.00 | -34.47 | +15.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.01 | 69.3 | 431 | 62.3% | +0.36 | -32.33 | +28.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.28 | 65.2 | 397 | 57.4% | -0.36 | -36.42 | -6.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.65 | 67.2 | 409 | 59.1% | +0.00 | -34.47 | +6.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.01 | 69.3 | 419 | 60.5% | +0.36 | -32.33 | +16.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.28 | 65.2 | 383 | 55.4% | -0.36 | -36.42 | -20.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.65 | 67.2 | 396 | 57.2% | +0.00 | -34.47 | -7.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.01 | 69.3 | 409 | 59.1% | +0.36 | -32.33 | +6.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.28 | 81.6 | 408 | 59.0% | -0.36 | -20.05 | +5.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.65 | 84.4 | 422 | 61.0% | +0.00 | -17.23 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.01 | 87.2 | 439 | 63.4% | +0.36 | -14.45 | +36.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.28 | 81.6 | 393 | 56.8% | -0.36 | -20.05 | -10.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.65 | 84.4 | 403 | 58.2% | +0.00 | -17.23 | +0.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.01 | 87.2 | 416 | 60.1% | +0.36 | -14.45 | +13.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.28 | 81.6 | 376 | 54.3% | -0.36 | -20.05 | -27.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.65 | 84.4 | 392 | 56.6% | +0.00 | -17.23 | -11.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.01 | 87.2 | 402 | 58.1% | +0.36 | -14.45 | -1.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.28 | 98.3 | 410 | 59.2% | -0.36 | -3.32 | +7.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.65 | 101.7 | 429 | 62.0% | +0.00 | +0.00 | +26.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.01 | 105.1 | 442 | 63.9% | +0.36 | +3.41 | +39.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.28 | 98.3 | 388 | 56.1% | -0.36 | -3.32 | -15.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.65 | 101.7 | 403 | 58.2% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.01 | 105.1 | 424 | 61.3% | +0.36 | +3.41 | +21.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.28 | 98.3 | 370 | 53.5% | -0.36 | -3.32 | -33.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.65 | 101.7 | 382 | 55.2% | +0.00 | +0.00 | -21.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.01 | 105.1 | 399 | 57.7% | +0.36 | +3.41 | -4.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.28 | 123.7 | 414 | 59.8% | -0.36 | +22.02 | +11.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.65 | 127.9 | 429 | 62.0% | +0.00 | +26.28 | +26.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.01 | 132.5 | 439 | 63.4% | +0.36 | +30.87 | +36.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.28 | 123.7 | 393 | 56.8% | -0.36 | +22.02 | -10.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.65 | 127.9 | 409 | 59.1% | +0.00 | +26.28 | +6.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.01 | 132.5 | 422 | 61.0% | +0.36 | +30.87 | +19.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.28 | 123.7 | 366 | 52.9% | -0.36 | +22.02 | -37.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.65 | 127.9 | 383 | 55.4% | +0.00 | +26.28 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.01 | 132.5 | 401 | 58.0% | +0.36 | +30.87 | -2.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._