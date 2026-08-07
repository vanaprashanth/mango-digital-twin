# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-08-02
- **Number of days:** 579
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
| Mean ETc | 3.74 mm/day |
| Mean root-zone depletion | 103.1 mm |
| High-stress days | 351 (60.6%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.74 | 69.2 | 362 (62.5%) | +11.00 |
| **1.0** | 126 | 63 | 3.74 | 86.3 | 356 (61.5%) | +5.00 |
| **1.2** | 152 | 76 | 3.74 | 103.1 | 351 (60.6%) | +0.00 |
| **1.5** | 190 | 95 | 3.74 | 127.4 | 343 (59.2%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 103.1 | 366 (63.2%) | +15.00 |
| **0.50** | 76 | 103.1 | 351 (60.6%) | +0.00 |
| **0.60** | 91 | 103.1 | 335 (57.9%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.36 | -0.37 mm/d | 99.7 | 340 (58.7%) | -11.00 |
| **1.00** | 3.74 | +0.00 mm/d | 103.1 | 351 (60.6%) | +0.00 |
| **1.10** | 4.11 | +0.37 mm/d | 106.4 | 366 (63.2%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **381** (65.8%)
- Mean ETc: 4.11 mm/day
- Mean depletion: 71.4 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **318** (54.9%)
- Mean ETc: 3.36 mm/day
- Mean depletion: 123.3 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.36 | 67.2 | 361 | 62.4% | -0.37 | -35.89 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.74 | 69.2 | 371 | 64.1% | +0.00 | -33.86 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.11 | 71.4 | 381 | 65.8% | +0.37 | -31.66 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.36 | 67.2 | 350 | 60.5% | -0.37 | -35.89 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.74 | 69.2 | 362 | 62.5% | +0.00 | -33.86 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.11 | 71.4 | 372 | 64.2% | +0.37 | -31.66 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.36 | 67.2 | 337 | 58.2% | -0.37 | -35.89 | -14.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.74 | 69.2 | 350 | 60.5% | +0.00 | -33.86 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.11 | 71.4 | 362 | 62.5% | +0.37 | -31.66 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.36 | 83.3 | 360 | 62.2% | -0.37 | -19.79 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.74 | 86.3 | 370 | 63.9% | +0.00 | -16.79 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.11 | 89.2 | 381 | 65.8% | +0.37 | -13.89 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.36 | 83.3 | 346 | 59.8% | -0.37 | -19.79 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.74 | 86.3 | 356 | 61.5% | +0.00 | -16.79 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.11 | 89.2 | 366 | 63.2% | +0.37 | -13.89 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.36 | 83.3 | 329 | 56.8% | -0.37 | -19.79 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.74 | 86.3 | 345 | 59.6% | +0.00 | -16.79 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.11 | 89.2 | 355 | 61.3% | +0.37 | -13.89 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.36 | 99.7 | 354 | 61.1% | -0.37 | -3.40 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.74 | 103.1 | 366 | 63.2% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.11 | 106.4 | 374 | 64.6% | +0.37 | +3.29 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.36 | 99.7 | 340 | 58.7% | -0.37 | -3.40 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.74 | 103.1 | 351 | 60.6% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.11 | 106.4 | 366 | 63.2% | +0.37 | +3.29 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.36 | 99.7 | 323 | 55.8% | -0.37 | -3.40 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.74 | 103.1 | 335 | 57.9% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.11 | 106.4 | 349 | 60.3% | +0.37 | +3.29 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.36 | 123.3 | 343 | 59.2% | -0.37 | +20.25 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.74 | 127.4 | 354 | 61.1% | +0.00 | +24.29 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.11 | 131.8 | 364 | 62.9% | +0.37 | +28.71 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.36 | 123.3 | 333 | 57.5% | -0.37 | +20.25 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.74 | 127.4 | 343 | 59.2% | +0.00 | +24.29 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.11 | 131.8 | 352 | 60.8% | +0.37 | +28.71 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.36 | 123.3 | 318 | 54.9% | -0.37 | +20.25 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.74 | 127.4 | 331 | 57.2% | +0.00 | +24.29 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.11 | 131.8 | 343 | 59.2% | +0.37 | +28.71 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._