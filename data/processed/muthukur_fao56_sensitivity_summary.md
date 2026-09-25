# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-09-20
- **Number of days:** 628
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 5.02 mm/day |
| Mean ETc | 3.75 mm/day |
| Mean root-zone depletion | 106.7 mm |
| High-stress days | 400 (63.7%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.75 | 71.5 | 410 (65.3%) | +10.00 |
| **1.0** | 126 | 63 | 3.75 | 89.2 | 405 (64.5%) | +5.00 |
| **1.2** | 152 | 76 | 3.75 | 106.7 | 400 (63.7%) | +0.00 |
| **1.5** | 190 | 95 | 3.75 | 132.0 | 392 (62.4%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 106.7 | 415 (66.1%) | +15.00 |
| **0.50** | 76 | 106.7 | 400 (63.7%) | +0.00 |
| **0.60** | 91 | 106.7 | 383 (61.0%) | -17.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.37 | -0.37 mm/d | 103.5 | 389 (61.9%) | -11.00 |
| **1.00** | 3.75 | +0.00 mm/d | 106.7 | 400 (63.7%) | +0.00 |
| **1.10** | 4.12 | +0.37 mm/d | 109.7 | 415 (66.1%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **430** (68.5%)
- Mean ETc: 4.12 mm/day
- Mean depletion: 73.5 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **367** (58.4%)
- Mean ETc: 3.37 mm/day
- Mean depletion: 128.3 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.37 | 69.6 | 409 | 65.1% | -0.37 | -37.05 | +9.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.75 | 71.5 | 419 | 66.7% | +0.00 | -35.16 | +19.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.12 | 73.5 | 430 | 68.5% | +0.37 | -33.13 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.37 | 69.6 | 397 | 63.2% | -0.37 | -37.05 | -3.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.75 | 71.5 | 410 | 65.3% | +0.00 | -35.16 | +10.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.12 | 73.5 | 420 | 66.9% | +0.37 | -33.13 | +20.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.37 | 69.6 | 383 | 61.0% | -0.37 | -37.05 | -17.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.75 | 71.5 | 397 | 63.2% | +0.00 | -35.16 | -3.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.12 | 73.5 | 409 | 65.1% | +0.37 | -33.13 | +9.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.37 | 86.4 | 409 | 65.1% | -0.37 | -20.24 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.75 | 89.2 | 419 | 66.7% | +0.00 | -17.46 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.12 | 91.9 | 430 | 68.5% | +0.37 | -14.77 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.37 | 86.4 | 394 | 62.7% | -0.37 | -20.24 | -6.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.75 | 89.2 | 405 | 64.5% | +0.00 | -17.46 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.12 | 91.9 | 415 | 66.1% | +0.37 | -14.77 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.37 | 86.4 | 376 | 59.9% | -0.37 | -20.24 | -24.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.75 | 89.2 | 393 | 62.6% | +0.00 | -17.46 | -7.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.12 | 91.9 | 403 | 64.2% | +0.37 | -14.77 | +3.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.37 | 103.5 | 403 | 64.2% | -0.37 | -3.15 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.75 | 106.7 | 415 | 66.1% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.12 | 109.7 | 423 | 67.4% | +0.37 | +3.04 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.37 | 103.5 | 389 | 61.9% | -0.37 | -3.15 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.75 | 106.7 | 400 | 63.7% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.12 | 109.7 | 415 | 66.1% | +0.37 | +3.04 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.37 | 103.5 | 371 | 59.1% | -0.37 | -3.15 | -29.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.75 | 106.7 | 383 | 61.0% | +0.00 | +0.00 | -17.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.12 | 109.7 | 398 | 63.4% | +0.37 | +3.04 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.37 | 128.3 | 392 | 62.4% | -0.37 | +21.61 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.75 | 132.0 | 403 | 64.2% | +0.00 | +25.35 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.12 | 136.1 | 413 | 65.8% | +0.37 | +29.44 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.37 | 128.3 | 382 | 60.8% | -0.37 | +21.61 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.75 | 132.0 | 392 | 62.4% | +0.00 | +25.35 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.12 | 136.1 | 401 | 63.9% | +0.37 | +29.44 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.37 | 128.3 | 367 | 58.4% | -0.37 | +21.61 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.75 | 132.0 | 380 | 60.5% | +0.00 | +25.35 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.12 | 136.1 | 392 | 62.4% | +0.37 | +29.44 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._