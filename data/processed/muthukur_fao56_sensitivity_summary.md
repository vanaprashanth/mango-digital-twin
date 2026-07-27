# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-07-22
- **Number of days:** 567
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
| Mean ETc | 3.75 mm/day |
| Mean root-zone depletion | 102.1 mm |
| High-stress days | 339 (59.8%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.75 | 68.6 | 350 (61.7%) | +11.00 |
| **1.0** | 126 | 63 | 3.75 | 85.5 | 344 (60.7%) | +5.00 |
| **1.2** | 152 | 76 | 3.75 | 102.1 | 339 (59.8%) | +0.00 |
| **1.5** | 190 | 95 | 3.75 | 126.1 | 331 (58.4%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 102.1 | 354 (62.4%) | +15.00 |
| **0.50** | 76 | 102.1 | 339 (59.8%) | +0.00 |
| **0.60** | 91 | 102.1 | 323 (57.0%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.38 | -0.38 mm/d | 98.7 | 328 (57.9%) | -11.00 |
| **1.00** | 3.75 | +0.00 mm/d | 102.1 | 339 (59.8%) | +0.00 |
| **1.10** | 4.13 | +0.38 mm/d | 105.4 | 354 (62.4%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **369** (65.1%)
- Mean ETc: 4.13 mm/day
- Mean depletion: 70.8 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **306** (54.0%)
- Mean ETc: 3.38 mm/day
- Mean depletion: 122.1 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.38 | 66.6 | 349 | 61.5% | -0.38 | -35.52 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.75 | 68.6 | 359 | 63.3% | +0.00 | -33.50 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.13 | 70.8 | 369 | 65.1% | +0.38 | -31.29 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.38 | 66.6 | 338 | 59.6% | -0.38 | -35.52 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.75 | 68.6 | 350 | 61.7% | +0.00 | -33.50 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.13 | 70.8 | 360 | 63.5% | +0.38 | -31.29 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.38 | 66.6 | 325 | 57.3% | -0.38 | -35.52 | -14.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.75 | 68.6 | 338 | 59.6% | +0.00 | -33.50 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.13 | 70.8 | 350 | 61.7% | +0.38 | -31.29 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.38 | 82.5 | 348 | 61.4% | -0.38 | -19.62 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.75 | 85.5 | 358 | 63.1% | +0.00 | -16.61 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.13 | 88.4 | 369 | 65.1% | +0.38 | -13.68 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.38 | 82.5 | 334 | 58.9% | -0.38 | -19.62 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.75 | 85.5 | 344 | 60.7% | +0.00 | -16.61 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.13 | 88.4 | 354 | 62.4% | +0.38 | -13.68 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.38 | 82.5 | 317 | 55.9% | -0.38 | -19.62 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.75 | 85.5 | 333 | 58.7% | +0.00 | -16.61 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.13 | 88.4 | 343 | 60.5% | +0.38 | -13.68 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.38 | 98.7 | 342 | 60.3% | -0.38 | -3.41 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.75 | 102.1 | 354 | 62.4% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.13 | 105.4 | 362 | 63.8% | +0.38 | +3.33 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.38 | 98.7 | 328 | 57.9% | -0.38 | -3.41 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.75 | 102.1 | 339 | 59.8% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.13 | 105.4 | 354 | 62.4% | +0.38 | +3.33 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.38 | 98.7 | 311 | 54.9% | -0.38 | -3.41 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.75 | 102.1 | 323 | 57.0% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.13 | 105.4 | 337 | 59.4% | +0.38 | +3.33 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.38 | 122.1 | 331 | 58.4% | -0.38 | +19.93 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.75 | 126.1 | 342 | 60.3% | +0.00 | +24.00 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.13 | 130.6 | 352 | 62.1% | +0.38 | +28.48 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.38 | 122.1 | 321 | 56.6% | -0.38 | +19.93 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.75 | 126.1 | 331 | 58.4% | +0.00 | +24.00 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.13 | 130.6 | 340 | 60.0% | +0.38 | +28.48 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.38 | 122.1 | 306 | 54.0% | -0.38 | +19.93 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.75 | 126.1 | 319 | 56.3% | +0.00 | +24.00 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.13 | 130.6 | 331 | 58.4% | +0.38 | +28.48 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._