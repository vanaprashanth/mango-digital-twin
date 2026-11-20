# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-11-15
- **Number of days:** 684
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
| Mean ETc | 3.66 mm/day |
| Mean root-zone depletion | 101.8 mm |
| High-stress days | 404 (59.1%) |
| Medium-stress days | 48 |
| Low-stress days | 232 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.66 | 67.6 | 409 (59.8%) | +5.00 |
| **1.0** | 126 | 63 | 3.66 | 84.8 | 404 (59.1%) | +0.00 |
| **1.2** | 152 | 76 | 3.66 | 101.8 | 404 (59.1%) | +0.00 |
| **1.5** | 190 | 95 | 3.66 | 126.6 | 411 (60.1%) | +7.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 101.8 | 432 (63.2%) | +28.00 |
| **0.50** | 76 | 101.8 | 404 (59.1%) | +0.00 |
| **0.60** | 91 | 101.8 | 382 (55.9%) | -22.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.29 | -0.37 mm/d | 98.7 | 389 (56.9%) | -15.00 |
| **1.00** | 3.66 | +0.00 mm/d | 101.8 | 404 (59.1%) | +0.00 |
| **1.10** | 4.02 | +0.37 mm/d | 104.8 | 424 (62.0%) | +20.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.2 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **444** (64.9%)
- Mean ETc: 4.02 mm/day
- Mean depletion: 104.8 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **367** (53.6%)
- Mean ETc: 3.29 mm/day
- Mean depletion: 123.0 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.29 | 65.7 | 408 | 59.6% | -0.37 | -36.05 | +4.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.66 | 67.6 | 418 | 61.1% | +0.00 | -34.16 | +14.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.02 | 69.7 | 431 | 63.0% | +0.37 | -32.10 | +27.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.29 | 65.7 | 397 | 58.0% | -0.37 | -36.05 | -7.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.66 | 67.6 | 409 | 59.8% | +0.00 | -34.16 | +5.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.02 | 69.7 | 420 | 61.4% | +0.37 | -32.10 | +16.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.29 | 65.7 | 383 | 56.0% | -0.37 | -36.05 | -21.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.66 | 67.6 | 396 | 57.9% | +0.00 | -34.16 | -8.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.02 | 69.7 | 409 | 59.8% | +0.37 | -32.10 | +5.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.29 | 82.1 | 409 | 59.8% | -0.37 | -19.69 | +5.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.66 | 84.8 | 423 | 61.8% | +0.00 | -16.98 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.02 | 87.5 | 439 | 64.2% | +0.37 | -14.32 | +35.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.29 | 82.1 | 393 | 57.5% | -0.37 | -19.69 | -11.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.66 | 84.8 | 404 | 59.1% | +0.00 | -16.98 | +0.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.02 | 87.5 | 416 | 60.8% | +0.37 | -14.32 | +12.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.29 | 82.1 | 376 | 55.0% | -0.37 | -19.69 | -28.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.66 | 84.8 | 392 | 57.3% | +0.00 | -16.98 | -12.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.02 | 87.5 | 403 | 58.9% | +0.37 | -14.32 | -1.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.29 | 98.7 | 411 | 60.1% | -0.37 | -3.06 | +7.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.66 | 101.8 | 432 | 63.2% | +0.00 | +0.00 | +28.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.02 | 104.8 | 444 | 64.9% | +0.37 | +2.99 | +40.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.29 | 98.7 | 389 | 56.9% | -0.37 | -3.06 | -15.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.66 | 101.8 | 404 | 59.1% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.02 | 104.8 | 424 | 62.0% | +0.37 | +2.99 | +20.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.29 | 98.7 | 370 | 54.1% | -0.37 | -3.06 | -34.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.66 | 101.8 | 382 | 55.9% | +0.00 | +0.00 | -22.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.02 | 104.8 | 399 | 58.3% | +0.37 | +2.99 | -5.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.29 | 123.0 | 415 | 60.7% | -0.37 | +21.17 | +11.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.66 | 126.6 | 427 | 62.4% | +0.00 | +24.83 | +23.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.02 | 130.6 | 438 | 64.0% | +0.37 | +28.84 | +34.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.29 | 123.0 | 394 | 57.6% | -0.37 | +21.17 | -10.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.66 | 126.6 | 411 | 60.1% | +0.00 | +24.83 | +7.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.02 | 130.6 | 422 | 61.7% | +0.37 | +28.84 | +18.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.29 | 123.0 | 367 | 53.6% | -0.37 | +21.17 | -37.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.66 | 126.6 | 384 | 56.1% | +0.00 | +24.83 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.02 | 130.6 | 401 | 58.6% | +0.37 | +28.84 | -3.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._