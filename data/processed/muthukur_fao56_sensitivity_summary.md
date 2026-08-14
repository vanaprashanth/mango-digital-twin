# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-08-09
- **Number of days:** 586
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
| Mean root-zone depletion | 103.4 mm |
| High-stress days | 358 (61.1%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.72 | 69.3 | 369 (63.0%) | +11.00 |
| **1.0** | 126 | 63 | 3.72 | 86.5 | 363 (62.0%) | +5.00 |
| **1.2** | 152 | 76 | 3.72 | 103.4 | 358 (61.1%) | +0.00 |
| **1.5** | 190 | 95 | 3.72 | 127.8 | 350 (59.7%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 103.4 | 373 (63.6%) | +15.00 |
| **0.50** | 76 | 103.4 | 358 (61.1%) | +0.00 |
| **0.60** | 91 | 103.4 | 342 (58.4%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.35 | -0.37 mm/d | 99.9 | 347 (59.2%) | -11.00 |
| **1.00** | 3.72 | +0.00 mm/d | 103.4 | 358 (61.1%) | +0.00 |
| **1.10** | 4.10 | +0.37 mm/d | 106.7 | 373 (63.6%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **388** (66.2%)
- Mean ETc: 4.10 mm/day
- Mean depletion: 71.5 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **325** (55.5%)
- Mean ETc: 3.35 mm/day
- Mean depletion: 123.8 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.35 | 67.2 | 368 | 62.8% | -0.37 | -36.13 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.72 | 69.3 | 378 | 64.5% | +0.00 | -34.06 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.10 | 71.5 | 388 | 66.2% | +0.37 | -31.85 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.35 | 67.2 | 354 | 60.4% | -0.37 | -36.13 | -4.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.72 | 69.3 | 369 | 63.0% | +0.00 | -34.06 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.10 | 71.5 | 379 | 64.7% | +0.37 | -31.85 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.35 | 67.2 | 338 | 57.7% | -0.37 | -36.13 | -20.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.72 | 69.3 | 353 | 60.2% | +0.00 | -34.06 | -5.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.10 | 71.5 | 369 | 63.0% | +0.37 | -31.85 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.35 | 83.4 | 367 | 62.6% | -0.37 | -19.92 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.72 | 86.5 | 377 | 64.3% | +0.00 | -16.89 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.10 | 89.4 | 388 | 66.2% | +0.37 | -13.99 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.35 | 83.4 | 353 | 60.2% | -0.37 | -19.92 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.72 | 86.5 | 363 | 62.0% | +0.00 | -16.89 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.10 | 89.4 | 373 | 63.6% | +0.37 | -13.99 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.35 | 83.4 | 333 | 56.8% | -0.37 | -19.92 | -25.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.72 | 86.5 | 352 | 60.1% | +0.00 | -16.89 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.10 | 89.4 | 362 | 61.8% | +0.37 | -13.99 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.35 | 99.9 | 361 | 61.6% | -0.37 | -3.42 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.72 | 103.4 | 373 | 63.6% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.10 | 106.7 | 381 | 65.0% | +0.37 | +3.29 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.35 | 99.9 | 347 | 59.2% | -0.37 | -3.42 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.72 | 103.4 | 358 | 61.1% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.10 | 106.7 | 373 | 63.6% | +0.37 | +3.29 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.35 | 99.9 | 330 | 56.3% | -0.37 | -3.42 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.72 | 103.4 | 342 | 58.4% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.10 | 106.7 | 356 | 60.8% | +0.37 | +3.29 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.35 | 123.8 | 350 | 59.7% | -0.37 | +20.40 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.72 | 127.8 | 361 | 61.6% | +0.00 | +24.45 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.10 | 132.2 | 371 | 63.3% | +0.37 | +28.86 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.35 | 123.8 | 340 | 58.0% | -0.37 | +20.40 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.72 | 127.8 | 350 | 59.7% | +0.00 | +24.45 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.10 | 132.2 | 359 | 61.3% | +0.37 | +28.86 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.35 | 123.8 | 325 | 55.5% | -0.37 | +20.40 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.72 | 127.8 | 338 | 57.7% | +0.00 | +24.45 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.10 | 132.2 | 350 | 59.7% | +0.37 | +28.86 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._