# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-10-15
- **Number of days:** 650
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 5.01 mm/day |
| Mean ETc | 3.72 mm/day |
| Mean root-zone depletion | 106.9 mm |
| High-stress days | 422 (64.9%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.72 | 71.3 | 413 (63.5%) | -9.00 |
| **1.0** | 126 | 63 | 3.72 | 89.2 | 419 (64.5%) | -3.00 |
| **1.2** | 152 | 76 | 3.72 | 106.9 | 422 (64.9%) | +0.00 |
| **1.5** | 190 | 95 | 3.72 | 132.7 | 414 (63.7%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 106.9 | 437 (67.2%) | +15.00 |
| **0.50** | 76 | 106.9 | 422 (64.9%) | +0.00 |
| **0.60** | 91 | 106.9 | 391 (60.1%) | -31.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.35 | -0.37 mm/d | 103.6 | 402 (61.9%) | -20.00 |
| **1.00** | 3.72 | +0.00 mm/d | 106.9 | 422 (64.9%) | +0.00 |
| **1.10** | 4.09 | +0.37 mm/d | 110.1 | 437 (67.2%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.0 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **452** (69.5%)
- Mean ETc: 4.09 mm/day
- Mean depletion: 92.0 mm

### Best case (fewest High-stress days)

- Root depth: 1.2 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **371** (57.1%)
- Mean ETc: 3.35 mm/day
- Mean depletion: 103.6 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.35 | 69.2 | 409 | 62.9% | -0.37 | -37.78 | -13.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.72 | 71.3 | 427 | 65.7% | +0.00 | -35.68 | +5.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.09 | 73.4 | 447 | 68.8% | +0.37 | -33.50 | +25.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.35 | 69.2 | 397 | 61.1% | -0.37 | -37.78 | -25.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.72 | 71.3 | 413 | 63.5% | +0.00 | -35.68 | -9.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.09 | 73.4 | 431 | 66.3% | +0.37 | -33.50 | +9.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.35 | 69.2 | 383 | 58.9% | -0.37 | -37.78 | -39.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.72 | 71.3 | 397 | 61.1% | +0.00 | -35.68 | -25.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.09 | 73.4 | 413 | 63.5% | +0.37 | -33.50 | -9.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.35 | 86.3 | 422 | 64.9% | -0.37 | -20.68 | +0.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.72 | 89.2 | 441 | 67.8% | +0.00 | -17.72 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.09 | 92.0 | 452 | 69.5% | +0.37 | -14.91 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.35 | 86.3 | 396 | 60.9% | -0.37 | -20.68 | -26.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.72 | 89.2 | 419 | 64.5% | +0.00 | -17.72 | -3.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.09 | 92.0 | 432 | 66.5% | +0.37 | -14.91 | +10.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.35 | 86.3 | 376 | 57.9% | -0.37 | -20.68 | -46.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.72 | 89.2 | 396 | 60.9% | +0.00 | -17.72 | -26.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.09 | 92.0 | 414 | 63.7% | +0.37 | -14.91 | -8.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.35 | 103.6 | 425 | 65.4% | -0.37 | -3.31 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.72 | 106.9 | 437 | 67.2% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.09 | 110.1 | 445 | 68.5% | +0.37 | +3.15 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.35 | 103.6 | 402 | 61.9% | -0.37 | -3.31 | -20.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.72 | 106.9 | 422 | 64.9% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.09 | 110.1 | 437 | 67.2% | +0.37 | +3.15 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.35 | 103.6 | 371 | 57.1% | -0.37 | -3.31 | -51.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.72 | 106.9 | 391 | 60.1% | +0.00 | +0.00 | -31.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.09 | 110.1 | 415 | 63.9% | +0.37 | +3.15 | -7.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.35 | 128.8 | 414 | 63.7% | -0.37 | +21.89 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.72 | 132.7 | 425 | 65.4% | +0.00 | +25.78 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.09 | 136.9 | 435 | 66.9% | +0.37 | +29.94 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.35 | 128.8 | 404 | 62.1% | -0.37 | +21.89 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.72 | 132.7 | 414 | 63.7% | +0.00 | +25.78 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.09 | 136.9 | 423 | 65.1% | +0.37 | +29.94 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.35 | 128.8 | 380 | 58.5% | -0.37 | +21.89 | -42.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.72 | 132.7 | 402 | 61.9% | +0.00 | +25.78 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.09 | 136.9 | 414 | 63.7% | +0.37 | +29.94 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._