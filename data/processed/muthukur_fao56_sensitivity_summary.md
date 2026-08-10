# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-08-05
- **Number of days:** 582
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.90 mm/day |
| Mean ETc | 3.73 mm/day |
| Mean root-zone depletion | 103.2 mm |
| High-stress days | 354 (60.8%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.73 | 69.3 | 365 (62.7%) | +11.00 |
| **1.0** | 126 | 63 | 3.73 | 86.4 | 359 (61.7%) | +5.00 |
| **1.2** | 152 | 76 | 3.73 | 103.2 | 354 (60.8%) | +0.00 |
| **1.5** | 190 | 95 | 3.73 | 127.6 | 346 (59.5%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 103.2 | 369 (63.4%) | +15.00 |
| **0.50** | 76 | 103.2 | 354 (60.8%) | +0.00 |
| **0.60** | 91 | 103.2 | 338 (58.1%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.36 | -0.37 mm/d | 99.8 | 343 (58.9%) | -11.00 |
| **1.00** | 3.73 | +0.00 mm/d | 103.2 | 354 (60.8%) | +0.00 |
| **1.10** | 4.11 | +0.37 mm/d | 106.5 | 369 (63.4%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **384** (66.0%)
- Mean ETc: 4.11 mm/day
- Mean depletion: 71.5 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **321** (55.1%)
- Mean ETc: 3.36 mm/day
- Mean depletion: 123.5 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.36 | 67.2 | 364 | 62.5% | -0.37 | -35.99 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.73 | 69.3 | 374 | 64.3% | +0.00 | -33.94 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.11 | 71.5 | 384 | 66.0% | +0.37 | -31.75 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.36 | 67.2 | 353 | 60.6% | -0.37 | -35.99 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.73 | 69.3 | 365 | 62.7% | +0.00 | -33.94 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.11 | 71.5 | 375 | 64.4% | +0.37 | -31.75 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.36 | 67.2 | 338 | 58.1% | -0.37 | -35.99 | -16.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.73 | 69.3 | 352 | 60.5% | +0.00 | -33.94 | -2.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.11 | 71.5 | 365 | 62.7% | +0.37 | -31.75 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.36 | 83.4 | 363 | 62.4% | -0.37 | -19.84 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.73 | 86.4 | 373 | 64.1% | +0.00 | -16.84 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.11 | 89.3 | 384 | 66.0% | +0.37 | -13.94 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.36 | 83.4 | 349 | 60.0% | -0.37 | -19.84 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.73 | 86.4 | 359 | 61.7% | +0.00 | -16.84 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.11 | 89.3 | 369 | 63.4% | +0.37 | -13.94 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.36 | 83.4 | 332 | 57.0% | -0.37 | -19.84 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.73 | 86.4 | 348 | 59.8% | +0.00 | -16.84 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.11 | 89.3 | 358 | 61.5% | +0.37 | -13.94 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.36 | 99.8 | 357 | 61.3% | -0.37 | -3.40 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.73 | 103.2 | 369 | 63.4% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.11 | 106.5 | 377 | 64.8% | +0.37 | +3.28 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.36 | 99.8 | 343 | 58.9% | -0.37 | -3.40 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.73 | 103.2 | 354 | 60.8% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.11 | 106.5 | 369 | 63.4% | +0.37 | +3.28 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.36 | 99.8 | 326 | 56.0% | -0.37 | -3.40 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.73 | 103.2 | 338 | 58.1% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.11 | 106.5 | 352 | 60.5% | +0.37 | +3.28 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.36 | 123.5 | 346 | 59.5% | -0.37 | +20.32 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.73 | 127.6 | 357 | 61.3% | +0.00 | +24.36 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.11 | 132.0 | 367 | 63.1% | +0.37 | +28.77 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.36 | 123.5 | 336 | 57.7% | -0.37 | +20.32 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.73 | 127.6 | 346 | 59.5% | +0.00 | +24.36 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.11 | 132.0 | 355 | 61.0% | +0.37 | +28.77 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.36 | 123.5 | 321 | 55.1% | -0.37 | +20.32 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.73 | 127.6 | 334 | 57.4% | +0.00 | +24.36 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.11 | 132.0 | 346 | 59.5% | +0.37 | +28.77 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._