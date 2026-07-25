# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-07-20
- **Number of days:** 565
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
| Mean ETc | 3.76 mm/day |
| Mean root-zone depletion | 102.0 mm |
| High-stress days | 337 (59.6%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.76 | 68.5 | 348 (61.6%) | +11.00 |
| **1.0** | 126 | 63 | 3.76 | 85.4 | 342 (60.5%) | +5.00 |
| **1.2** | 152 | 76 | 3.76 | 102.0 | 337 (59.6%) | +0.00 |
| **1.5** | 190 | 95 | 3.76 | 125.9 | 329 (58.2%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 102.0 | 352 (62.3%) | +15.00 |
| **0.50** | 76 | 102.0 | 337 (59.6%) | +0.00 |
| **0.60** | 91 | 102.0 | 321 (56.8%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.38 | -0.38 mm/d | 98.5 | 326 (57.7%) | -11.00 |
| **1.00** | 3.76 | +0.00 mm/d | 102.0 | 337 (59.6%) | +0.00 |
| **1.10** | 4.13 | +0.38 mm/d | 105.3 | 352 (62.3%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **367** (65.0%)
- Mean ETc: 4.13 mm/day
- Mean depletion: 70.7 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **304** (53.8%)
- Mean ETc: 3.38 mm/day
- Mean depletion: 121.8 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.38 | 66.5 | 347 | 61.4% | -0.38 | -35.46 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.76 | 68.5 | 357 | 63.2% | +0.00 | -33.44 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.13 | 70.7 | 367 | 65.0% | +0.38 | -31.23 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.38 | 66.5 | 336 | 59.5% | -0.38 | -35.46 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.76 | 68.5 | 348 | 61.6% | +0.00 | -33.44 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.13 | 70.7 | 358 | 63.4% | +0.38 | -31.23 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.38 | 66.5 | 323 | 57.2% | -0.38 | -35.46 | -14.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.76 | 68.5 | 336 | 59.5% | +0.00 | -33.44 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.13 | 70.7 | 348 | 61.6% | +0.38 | -31.23 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.38 | 82.4 | 346 | 61.2% | -0.38 | -19.59 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.76 | 85.4 | 356 | 63.0% | +0.00 | -16.58 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.13 | 88.3 | 367 | 65.0% | +0.38 | -13.64 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.38 | 82.4 | 332 | 58.8% | -0.38 | -19.59 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.76 | 85.4 | 342 | 60.5% | +0.00 | -16.58 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.13 | 88.3 | 352 | 62.3% | +0.38 | -13.64 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.38 | 82.4 | 315 | 55.8% | -0.38 | -19.59 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.76 | 85.4 | 331 | 58.6% | +0.00 | -16.58 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.13 | 88.3 | 341 | 60.4% | +0.38 | -13.64 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.38 | 98.5 | 340 | 60.2% | -0.38 | -3.42 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.76 | 102.0 | 352 | 62.3% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.13 | 105.3 | 360 | 63.7% | +0.38 | +3.33 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.38 | 98.5 | 326 | 57.7% | -0.38 | -3.42 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.76 | 102.0 | 337 | 59.6% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.13 | 105.3 | 352 | 62.3% | +0.38 | +3.33 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.38 | 98.5 | 309 | 54.7% | -0.38 | -3.42 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.76 | 102.0 | 321 | 56.8% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.13 | 105.3 | 335 | 59.3% | +0.38 | +3.33 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.38 | 121.8 | 329 | 58.2% | -0.38 | +19.88 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.76 | 125.9 | 340 | 60.2% | +0.00 | +23.95 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.13 | 130.4 | 350 | 62.0% | +0.38 | +28.44 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.38 | 121.8 | 319 | 56.5% | -0.38 | +19.88 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.76 | 125.9 | 329 | 58.2% | +0.00 | +23.95 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.13 | 130.4 | 338 | 59.8% | +0.38 | +28.44 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.38 | 121.8 | 304 | 53.8% | -0.38 | +19.88 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.76 | 125.9 | 317 | 56.1% | +0.00 | +23.95 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.13 | 130.4 | 329 | 58.2% | +0.38 | +28.44 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._