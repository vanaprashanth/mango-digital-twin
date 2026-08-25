# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-08-20
- **Number of days:** 597
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
| Mean ETc | 3.76 mm/day |
| Mean root-zone depletion | 104.0 mm |
| High-stress days | 369 (61.8%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.76 | 69.7 | 380 (63.6%) | +11.00 |
| **1.0** | 126 | 63 | 3.76 | 87.0 | 374 (62.6%) | +5.00 |
| **1.2** | 152 | 76 | 3.76 | 104.0 | 369 (61.8%) | +0.00 |
| **1.5** | 190 | 95 | 3.76 | 128.7 | 361 (60.5%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 104.0 | 384 (64.3%) | +15.00 |
| **0.50** | 76 | 104.0 | 369 (61.8%) | +0.00 |
| **0.60** | 91 | 104.0 | 353 (59.1%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.38 | -0.38 mm/d | 100.7 | 358 (60.0%) | -11.00 |
| **1.00** | 3.76 | +0.00 mm/d | 104.0 | 369 (61.8%) | +0.00 |
| **1.10** | 4.13 | +0.38 mm/d | 107.3 | 384 (64.3%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **399** (66.8%)
- Mean ETc: 4.13 mm/day
- Mean depletion: 71.9 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **336** (56.3%)
- Mean ETc: 3.38 mm/day
- Mean depletion: 124.8 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.38 | 67.7 | 379 | 63.5% | -0.38 | -36.35 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.76 | 69.7 | 389 | 65.2% | +0.00 | -34.36 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.13 | 71.9 | 399 | 66.8% | +0.38 | -32.18 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.38 | 67.7 | 368 | 61.6% | -0.38 | -36.35 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.76 | 69.7 | 380 | 63.6% | +0.00 | -34.36 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.13 | 71.9 | 390 | 65.3% | +0.38 | -32.18 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.38 | 67.7 | 348 | 58.3% | -0.38 | -36.35 | -21.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.76 | 69.7 | 368 | 61.6% | +0.00 | -34.36 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.13 | 71.9 | 380 | 63.6% | +0.38 | -32.18 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.38 | 84.1 | 378 | 63.3% | -0.38 | -19.97 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.76 | 87.0 | 388 | 65.0% | +0.00 | -17.05 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.13 | 89.9 | 399 | 66.8% | +0.38 | -14.18 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.38 | 84.1 | 364 | 61.0% | -0.38 | -19.97 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.76 | 87.0 | 374 | 62.6% | +0.00 | -17.05 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.13 | 89.9 | 384 | 64.3% | +0.38 | -14.18 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.38 | 84.1 | 347 | 58.1% | -0.38 | -19.97 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.76 | 87.0 | 363 | 60.8% | +0.00 | -17.05 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.13 | 89.9 | 373 | 62.5% | +0.38 | -14.18 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.38 | 100.7 | 372 | 62.3% | -0.38 | -3.31 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.76 | 104.0 | 384 | 64.3% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.13 | 107.3 | 392 | 65.7% | +0.38 | +3.24 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.38 | 100.7 | 358 | 60.0% | -0.38 | -3.31 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.76 | 104.0 | 369 | 61.8% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.13 | 107.3 | 384 | 64.3% | +0.38 | +3.24 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.38 | 100.7 | 341 | 57.1% | -0.38 | -3.31 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.76 | 104.0 | 353 | 59.1% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.13 | 107.3 | 367 | 61.5% | +0.38 | +3.24 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.38 | 124.8 | 361 | 60.5% | -0.38 | +20.77 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.76 | 128.7 | 372 | 62.3% | +0.00 | +24.70 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.13 | 133.1 | 382 | 64.0% | +0.38 | +29.03 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.38 | 124.8 | 351 | 58.8% | -0.38 | +20.77 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.76 | 128.7 | 361 | 60.5% | +0.00 | +24.70 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.13 | 133.1 | 370 | 62.0% | +0.38 | +29.03 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.38 | 124.8 | 336 | 56.3% | -0.38 | +20.77 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.76 | 128.7 | 349 | 58.5% | +0.00 | +24.70 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.13 | 133.1 | 361 | 60.5% | +0.38 | +29.03 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._