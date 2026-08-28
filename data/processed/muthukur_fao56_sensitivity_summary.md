# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-08-23
- **Number of days:** 600
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.97 mm/day |
| Mean ETc | 3.75 mm/day |
| Mean root-zone depletion | 104.2 mm |
| High-stress days | 372 (62.0%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.75 | 69.7 | 383 (63.8%) | +11.00 |
| **1.0** | 126 | 63 | 3.75 | 87.1 | 377 (62.8%) | +5.00 |
| **1.2** | 152 | 76 | 3.75 | 104.2 | 372 (62.0%) | +0.00 |
| **1.5** | 190 | 95 | 3.75 | 129.0 | 364 (60.7%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 104.2 | 387 (64.5%) | +15.00 |
| **0.50** | 76 | 104.2 | 372 (62.0%) | +0.00 |
| **0.60** | 91 | 104.2 | 356 (59.3%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.38 | -0.38 mm/d | 100.9 | 361 (60.2%) | -11.00 |
| **1.00** | 3.75 | +0.00 mm/d | 104.2 | 372 (62.0%) | +0.00 |
| **1.10** | 4.13 | +0.38 mm/d | 107.4 | 387 (64.5%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **402** (67.0%)
- Mean ETc: 4.13 mm/day
- Mean depletion: 71.9 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **339** (56.5%)
- Mean ETc: 3.38 mm/day
- Mean depletion: 125.0 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.38 | 67.7 | 382 | 63.7% | -0.38 | -36.45 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.75 | 69.7 | 392 | 65.3% | +0.00 | -34.44 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.13 | 71.9 | 402 | 67.0% | +0.38 | -32.25 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.38 | 67.7 | 371 | 61.8% | -0.38 | -36.45 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.75 | 69.7 | 383 | 63.8% | +0.00 | -34.44 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.13 | 71.9 | 393 | 65.5% | +0.38 | -32.25 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.38 | 67.7 | 350 | 58.3% | -0.38 | -36.45 | -22.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.75 | 69.7 | 371 | 61.8% | +0.00 | -34.44 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.13 | 71.9 | 383 | 63.8% | +0.38 | -32.25 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.38 | 84.2 | 381 | 63.5% | -0.38 | -20.03 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.75 | 87.1 | 391 | 65.2% | +0.00 | -17.09 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.13 | 90.0 | 402 | 67.0% | +0.38 | -14.21 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.38 | 84.2 | 367 | 61.2% | -0.38 | -20.03 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.75 | 87.1 | 377 | 62.8% | +0.00 | -17.09 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.13 | 90.0 | 387 | 64.5% | +0.38 | -14.21 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.38 | 84.2 | 350 | 58.3% | -0.38 | -20.03 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.75 | 87.1 | 366 | 61.0% | +0.00 | -17.09 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.13 | 90.0 | 376 | 62.7% | +0.38 | -14.21 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.38 | 100.9 | 375 | 62.5% | -0.38 | -3.32 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.75 | 104.2 | 387 | 64.5% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.13 | 107.4 | 395 | 65.8% | +0.38 | +3.25 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.38 | 100.9 | 361 | 60.2% | -0.38 | -3.32 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.75 | 104.2 | 372 | 62.0% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.13 | 107.4 | 387 | 64.5% | +0.38 | +3.25 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.38 | 100.9 | 344 | 57.3% | -0.38 | -3.32 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.75 | 104.2 | 356 | 59.3% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.13 | 107.4 | 370 | 61.7% | +0.38 | +3.25 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.38 | 125.0 | 364 | 60.7% | -0.38 | +20.82 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.75 | 129.0 | 375 | 62.5% | +0.00 | +24.77 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.13 | 133.3 | 385 | 64.2% | +0.38 | +29.11 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.38 | 125.0 | 354 | 59.0% | -0.38 | +20.82 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.75 | 129.0 | 364 | 60.7% | +0.00 | +24.77 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.13 | 133.3 | 373 | 62.2% | +0.38 | +29.11 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.38 | 125.0 | 339 | 56.5% | -0.38 | +20.82 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.75 | 129.0 | 352 | 58.7% | +0.00 | +24.77 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.13 | 133.3 | 364 | 60.7% | +0.38 | +29.11 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._