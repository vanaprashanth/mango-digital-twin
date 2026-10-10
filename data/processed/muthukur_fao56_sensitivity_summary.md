# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-10-05
- **Number of days:** 643
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 5.00 mm/day |
| Mean ETc | 3.72 mm/day |
| Mean root-zone depletion | 106.8 mm |
| High-stress days | 415 (64.5%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.72 | 71.3 | 412 (64.1%) | -3.00 |
| **1.0** | 126 | 63 | 3.72 | 89.2 | 413 (64.2%) | -2.00 |
| **1.2** | 152 | 76 | 3.72 | 106.8 | 415 (64.5%) | +0.00 |
| **1.5** | 190 | 95 | 3.72 | 132.5 | 407 (63.3%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 106.8 | 430 (66.9%) | +15.00 |
| **0.50** | 76 | 106.8 | 415 (64.5%) | +0.00 |
| **0.60** | 91 | 106.8 | 387 (60.2%) | -28.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.35 | -0.37 mm/d | 103.6 | 398 (61.9%) | -17.00 |
| **1.00** | 3.72 | +0.00 mm/d | 106.8 | 415 (64.5%) | +0.00 |
| **1.10** | 4.10 | +0.37 mm/d | 109.9 | 430 (66.9%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.0 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **445** (69.2%)
- Mean ETc: 4.10 mm/day
- Mean depletion: 91.9 mm

### Best case (fewest High-stress days)

- Root depth: 1.2 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **371** (57.7%)
- Mean ETc: 3.35 mm/day
- Mean depletion: 103.6 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.35 | 69.3 | 409 | 63.6% | -0.37 | -37.53 | -6.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.72 | 71.3 | 423 | 65.8% | +0.00 | -35.52 | +8.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.10 | 73.4 | 440 | 68.4% | +0.37 | -33.41 | +25.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.35 | 69.3 | 397 | 61.7% | -0.37 | -37.53 | -18.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.72 | 71.3 | 412 | 64.1% | +0.00 | -35.52 | -3.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.10 | 73.4 | 425 | 66.1% | +0.37 | -33.41 | +10.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.35 | 69.3 | 383 | 59.6% | -0.37 | -37.53 | -32.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.72 | 71.3 | 397 | 61.7% | +0.00 | -35.52 | -18.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.10 | 73.4 | 411 | 63.9% | +0.37 | -33.41 | -4.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.35 | 86.3 | 418 | 65.0% | -0.37 | -20.52 | +3.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.72 | 89.2 | 434 | 67.5% | +0.00 | -17.64 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.10 | 91.9 | 445 | 69.2% | +0.37 | -14.89 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.35 | 86.3 | 396 | 61.6% | -0.37 | -20.52 | -19.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.72 | 89.2 | 413 | 64.2% | +0.00 | -17.64 | -2.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.10 | 91.9 | 425 | 66.1% | +0.37 | -14.89 | +10.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.35 | 86.3 | 376 | 58.5% | -0.37 | -20.52 | -39.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.72 | 89.2 | 395 | 61.4% | +0.00 | -17.64 | -20.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.10 | 91.9 | 408 | 63.5% | +0.37 | -14.89 | -7.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.35 | 103.6 | 418 | 65.0% | -0.37 | -3.24 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.72 | 106.8 | 430 | 66.9% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.10 | 109.9 | 438 | 68.1% | +0.37 | +3.09 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.35 | 103.6 | 398 | 61.9% | -0.37 | -3.24 | -17.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.72 | 106.8 | 415 | 64.5% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.10 | 109.9 | 430 | 66.9% | +0.37 | +3.09 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.35 | 103.6 | 371 | 57.7% | -0.37 | -3.24 | -44.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.72 | 106.8 | 387 | 60.2% | +0.00 | +0.00 | -28.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.10 | 109.9 | 408 | 63.5% | +0.37 | +3.09 | -7.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.35 | 128.7 | 407 | 63.3% | -0.37 | +21.83 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.72 | 132.5 | 418 | 65.0% | +0.00 | +25.65 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.10 | 136.6 | 428 | 66.6% | +0.37 | +29.76 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.35 | 128.7 | 397 | 61.7% | -0.37 | +21.83 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.72 | 132.5 | 407 | 63.3% | +0.00 | +25.65 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.10 | 136.6 | 416 | 64.7% | +0.37 | +29.76 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.35 | 128.7 | 376 | 58.5% | -0.37 | +21.83 | -39.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.72 | 132.5 | 395 | 61.4% | +0.00 | +25.65 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.10 | 136.6 | 407 | 63.3% | +0.37 | +29.76 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._