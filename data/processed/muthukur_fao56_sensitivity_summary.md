# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-11-21
- **Number of days:** 690
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.95 mm/day |
| Mean ETc | 3.65 mm/day |
| Mean root-zone depletion | 101.9 mm |
| High-stress days | 403 (58.4%) |
| Medium-stress days | 51 |
| Low-stress days | 236 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.65 | 67.3 | 409 (59.3%) | +6.00 |
| **1.0** | 126 | 63 | 3.65 | 84.6 | 403 (58.4%) | +0.00 |
| **1.2** | 152 | 76 | 3.65 | 101.9 | 403 (58.4%) | +0.00 |
| **1.5** | 190 | 95 | 3.65 | 128.2 | 409 (59.3%) | +6.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 101.9 | 429 (62.2%) | +26.00 |
| **0.50** | 76 | 101.9 | 403 (58.4%) | +0.00 |
| **0.60** | 91 | 101.9 | 382 (55.4%) | -21.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.29 | -0.37 mm/d | 98.6 | 388 (56.2%) | -15.00 |
| **1.00** | 3.65 | +0.00 mm/d | 101.9 | 403 (58.4%) | +0.00 |
| **1.10** | 4.02 | +0.37 mm/d | 105.3 | 424 (61.5%) | +21.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.2 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **442** (64.1%)
- Mean ETc: 4.02 mm/day
- Mean depletion: 105.3 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **366** (53.0%)
- Mean ETc: 3.29 mm/day
- Mean depletion: 123.9 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.29 | 65.4 | 408 | 59.1% | -0.37 | -36.52 | +5.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.65 | 67.3 | 418 | 60.6% | +0.00 | -34.57 | +15.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.02 | 69.5 | 431 | 62.5% | +0.37 | -32.43 | +28.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.29 | 65.4 | 397 | 57.5% | -0.37 | -36.52 | -6.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.65 | 67.3 | 409 | 59.3% | +0.00 | -34.57 | +6.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.02 | 69.5 | 419 | 60.7% | +0.37 | -32.43 | +16.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.29 | 65.4 | 383 | 55.5% | -0.37 | -36.52 | -20.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.65 | 67.3 | 396 | 57.4% | +0.00 | -34.57 | -7.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.02 | 69.5 | 409 | 59.3% | +0.37 | -32.43 | +6.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.29 | 81.8 | 408 | 59.1% | -0.37 | -20.10 | +5.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.65 | 84.6 | 422 | 61.2% | +0.00 | -17.28 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.02 | 87.4 | 439 | 63.6% | +0.37 | -14.50 | +36.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.29 | 81.8 | 393 | 57.0% | -0.37 | -20.10 | -10.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.65 | 84.6 | 403 | 58.4% | +0.00 | -17.28 | +0.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.02 | 87.4 | 416 | 60.3% | +0.37 | -14.50 | +13.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.29 | 81.8 | 376 | 54.5% | -0.37 | -20.10 | -27.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.65 | 84.6 | 392 | 56.8% | +0.00 | -17.28 | -11.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.02 | 87.4 | 402 | 58.3% | +0.37 | -14.50 | -1.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.29 | 98.6 | 410 | 59.4% | -0.37 | -3.32 | +7.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.65 | 101.9 | 429 | 62.2% | +0.00 | +0.00 | +26.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.02 | 105.3 | 442 | 64.1% | +0.37 | +3.39 | +39.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.29 | 98.6 | 388 | 56.2% | -0.37 | -3.32 | -15.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.65 | 101.9 | 403 | 58.4% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.02 | 105.3 | 424 | 61.5% | +0.37 | +3.39 | +21.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.29 | 98.6 | 370 | 53.6% | -0.37 | -3.32 | -33.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.65 | 101.9 | 382 | 55.4% | +0.00 | +0.00 | -21.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.02 | 105.3 | 399 | 57.8% | +0.37 | +3.39 | -4.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.29 | 123.9 | 414 | 60.0% | -0.37 | +22.05 | +11.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.65 | 128.2 | 429 | 62.2% | +0.00 | +26.27 | +26.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.02 | 132.7 | 439 | 63.6% | +0.37 | +30.83 | +36.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.29 | 123.9 | 393 | 57.0% | -0.37 | +22.05 | -10.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.65 | 128.2 | 409 | 59.3% | +0.00 | +26.27 | +6.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.02 | 132.7 | 422 | 61.2% | +0.37 | +30.83 | +19.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.29 | 123.9 | 366 | 53.0% | -0.37 | +22.05 | -37.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.65 | 128.2 | 383 | 55.5% | +0.00 | +26.27 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.02 | 132.7 | 401 | 58.1% | +0.37 | +30.83 | -2.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._