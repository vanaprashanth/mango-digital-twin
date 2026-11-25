# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-11-18
- **Number of days:** 687
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
| Mean root-zone depletion | 101.4 mm |
| High-stress days | 404 (58.8%) |
| Medium-stress days | 48 |
| Low-stress days | 235 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.65 | 67.4 | 409 (59.5%) | +5.00 |
| **1.0** | 126 | 63 | 3.65 | 84.5 | 404 (58.8%) | +0.00 |
| **1.2** | 152 | 76 | 3.65 | 101.4 | 404 (58.8%) | +0.00 |
| **1.5** | 190 | 95 | 3.65 | 126.1 | 411 (59.8%) | +7.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 101.4 | 432 (62.9%) | +28.00 |
| **0.50** | 76 | 101.4 | 404 (58.8%) | +0.00 |
| **0.60** | 91 | 101.4 | 382 (55.6%) | -22.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.29 | -0.37 mm/d | 98.4 | 389 (56.6%) | -15.00 |
| **1.00** | 3.65 | +0.00 mm/d | 101.4 | 404 (58.8%) | +0.00 |
| **1.10** | 4.02 | +0.37 mm/d | 104.4 | 424 (61.7%) | +20.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.2 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **444** (64.6%)
- Mean ETc: 4.02 mm/day
- Mean depletion: 104.4 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **367** (53.4%)
- Mean ETc: 3.29 mm/day
- Mean depletion: 122.5 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.29 | 65.5 | 408 | 59.4% | -0.37 | -35.90 | +4.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.65 | 67.4 | 418 | 60.8% | +0.00 | -34.01 | +14.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.02 | 69.5 | 431 | 62.7% | +0.37 | -31.95 | +27.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.29 | 65.5 | 397 | 57.8% | -0.37 | -35.90 | -7.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.65 | 67.4 | 409 | 59.5% | +0.00 | -34.01 | +5.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.02 | 69.5 | 420 | 61.1% | +0.37 | -31.95 | +16.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.29 | 65.5 | 383 | 55.8% | -0.37 | -35.90 | -21.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.65 | 67.4 | 396 | 57.6% | +0.00 | -34.01 | -8.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.02 | 69.5 | 409 | 59.5% | +0.37 | -31.95 | +5.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.29 | 81.8 | 409 | 59.5% | -0.37 | -19.61 | +5.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.65 | 84.5 | 423 | 61.6% | +0.00 | -16.90 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.02 | 87.2 | 439 | 63.9% | +0.37 | -14.25 | +35.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.29 | 81.8 | 393 | 57.2% | -0.37 | -19.61 | -11.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.65 | 84.5 | 404 | 58.8% | +0.00 | -16.90 | +0.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.02 | 87.2 | 416 | 60.5% | +0.37 | -14.25 | +12.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.29 | 81.8 | 376 | 54.7% | -0.37 | -19.61 | -28.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.65 | 84.5 | 392 | 57.1% | +0.00 | -16.90 | -12.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.02 | 87.2 | 403 | 58.7% | +0.37 | -14.25 | -1.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.29 | 98.4 | 411 | 59.8% | -0.37 | -3.05 | +7.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.65 | 101.4 | 432 | 62.9% | +0.00 | +0.00 | +28.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.02 | 104.4 | 444 | 64.6% | +0.37 | +2.99 | +40.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.29 | 98.4 | 389 | 56.6% | -0.37 | -3.05 | -15.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.65 | 101.4 | 404 | 58.8% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.02 | 104.4 | 424 | 61.7% | +0.37 | +2.99 | +20.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.29 | 98.4 | 370 | 53.9% | -0.37 | -3.05 | -34.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.65 | 101.4 | 382 | 55.6% | +0.00 | +0.00 | -22.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.02 | 104.4 | 399 | 58.1% | +0.37 | +2.99 | -5.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.29 | 122.5 | 415 | 60.4% | -0.37 | +21.07 | +11.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.65 | 126.1 | 427 | 62.1% | +0.00 | +24.72 | +23.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.02 | 130.1 | 438 | 63.8% | +0.37 | +28.73 | +34.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.29 | 122.5 | 394 | 57.4% | -0.37 | +21.07 | -10.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.65 | 126.1 | 411 | 59.8% | +0.00 | +24.72 | +7.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.02 | 130.1 | 422 | 61.4% | +0.37 | +28.73 | +18.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.29 | 122.5 | 367 | 53.4% | -0.37 | +21.07 | -37.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.65 | 126.1 | 384 | 55.9% | +0.00 | +24.72 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.02 | 130.1 | 401 | 58.4% | +0.37 | +28.73 | -3.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._