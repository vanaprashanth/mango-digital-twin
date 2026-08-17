# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-08-12
- **Number of days:** 589
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
| Mean ETc | 3.72 mm/day |
| Mean root-zone depletion | 103.5 mm |
| High-stress days | 361 (61.3%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.72 | 69.3 | 372 (63.2%) | +11.00 |
| **1.0** | 126 | 63 | 3.72 | 86.5 | 366 (62.1%) | +5.00 |
| **1.2** | 152 | 76 | 3.72 | 103.5 | 361 (61.3%) | +0.00 |
| **1.5** | 190 | 95 | 3.72 | 128.0 | 353 (59.9%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 103.5 | 376 (63.8%) | +15.00 |
| **0.50** | 76 | 103.5 | 361 (61.3%) | +0.00 |
| **0.60** | 91 | 103.5 | 345 (58.6%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.35 | -0.37 mm/d | 100.0 | 350 (59.4%) | -11.00 |
| **1.00** | 3.72 | +0.00 mm/d | 103.5 | 361 (61.3%) | +0.00 |
| **1.10** | 4.09 | +0.37 mm/d | 106.8 | 376 (63.8%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **391** (66.4%)
- Mean ETc: 4.09 mm/day
- Mean depletion: 71.6 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **328** (55.7%)
- Mean ETc: 3.35 mm/day
- Mean depletion: 123.9 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.35 | 67.2 | 371 | 63.0% | -0.37 | -36.24 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.72 | 69.3 | 381 | 64.7% | +0.00 | -34.14 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.09 | 71.6 | 391 | 66.4% | +0.37 | -31.92 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.35 | 67.2 | 354 | 60.1% | -0.37 | -36.24 | -7.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.72 | 69.3 | 372 | 63.2% | +0.00 | -34.14 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.09 | 71.6 | 382 | 64.9% | +0.37 | -31.92 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.35 | 67.2 | 338 | 57.4% | -0.37 | -36.24 | -23.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.72 | 69.3 | 353 | 59.9% | +0.00 | -34.14 | -8.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.09 | 71.6 | 372 | 63.2% | +0.37 | -31.92 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.35 | 83.5 | 370 | 62.8% | -0.37 | -19.98 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.72 | 86.5 | 380 | 64.5% | +0.00 | -16.94 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.09 | 89.5 | 391 | 66.4% | +0.37 | -14.02 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.35 | 83.5 | 356 | 60.4% | -0.37 | -19.98 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.72 | 86.5 | 366 | 62.1% | +0.00 | -16.94 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.09 | 89.5 | 376 | 63.8% | +0.37 | -14.02 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.35 | 83.5 | 333 | 56.5% | -0.37 | -19.98 | -28.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.72 | 86.5 | 355 | 60.3% | +0.00 | -16.94 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.09 | 89.5 | 365 | 62.0% | +0.37 | -14.02 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.35 | 100.0 | 364 | 61.8% | -0.37 | -3.44 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.72 | 103.5 | 376 | 63.8% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.09 | 106.8 | 384 | 65.2% | +0.37 | +3.29 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.35 | 100.0 | 350 | 59.4% | -0.37 | -3.44 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.72 | 103.5 | 361 | 61.3% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.09 | 106.8 | 376 | 63.8% | +0.37 | +3.29 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.35 | 100.0 | 333 | 56.5% | -0.37 | -3.44 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.72 | 103.5 | 345 | 58.6% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.09 | 106.8 | 359 | 61.0% | +0.37 | +3.29 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.35 | 123.9 | 353 | 59.9% | -0.37 | +20.45 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.72 | 128.0 | 364 | 61.8% | +0.00 | +24.52 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.09 | 132.4 | 374 | 63.5% | +0.37 | +28.93 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.35 | 123.9 | 343 | 58.2% | -0.37 | +20.45 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.72 | 128.0 | 353 | 59.9% | +0.00 | +24.52 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.09 | 132.4 | 362 | 61.5% | +0.37 | +28.93 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.35 | 123.9 | 328 | 55.7% | -0.37 | +20.45 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.72 | 128.0 | 341 | 57.9% | +0.00 | +24.52 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.09 | 132.4 | 353 | 59.9% | +0.37 | +28.93 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._