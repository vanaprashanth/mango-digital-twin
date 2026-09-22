# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-09-14
- **Number of days:** 622
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
| Mean ETc | 3.72 mm/day |
| Mean root-zone depletion | 105.6 mm |
| High-stress days | 394 (63.3%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.72 | 70.6 | 405 (65.1%) | +11.00 |
| **1.0** | 126 | 63 | 3.72 | 88.3 | 399 (64.2%) | +5.00 |
| **1.2** | 152 | 76 | 3.72 | 105.6 | 394 (63.3%) | +0.00 |
| **1.5** | 190 | 95 | 3.72 | 130.9 | 386 (62.1%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 105.6 | 409 (65.8%) | +15.00 |
| **0.50** | 76 | 105.6 | 394 (63.3%) | +0.00 |
| **0.60** | 91 | 105.6 | 378 (60.8%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.35 | -0.37 mm/d | 102.1 | 383 (61.6%) | -11.00 |
| **1.00** | 3.72 | +0.00 mm/d | 105.6 | 394 (63.3%) | +0.00 |
| **1.10** | 4.10 | +0.37 mm/d | 108.9 | 409 (65.8%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **424** (68.2%)
- Mean ETc: 4.10 mm/day
- Mean depletion: 72.8 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **361** (58.0%)
- Mean ETc: 3.35 mm/day
- Mean depletion: 126.8 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.35 | 68.4 | 404 | 65.0% | -0.37 | -37.23 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.72 | 70.6 | 414 | 66.6% | +0.00 | -35.01 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.10 | 72.8 | 424 | 68.2% | +0.37 | -32.80 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.35 | 68.4 | 393 | 63.2% | -0.37 | -37.23 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.72 | 70.6 | 405 | 65.1% | +0.00 | -35.01 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.10 | 72.8 | 415 | 66.7% | +0.37 | -32.80 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.35 | 68.4 | 370 | 59.5% | -0.37 | -37.23 | -24.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.72 | 70.6 | 393 | 63.2% | +0.00 | -35.01 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.10 | 72.8 | 405 | 65.1% | +0.37 | -32.80 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.35 | 85.1 | 403 | 64.8% | -0.37 | -20.50 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.72 | 88.3 | 413 | 66.4% | +0.00 | -17.38 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.10 | 91.1 | 424 | 68.2% | +0.37 | -14.51 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.35 | 85.1 | 389 | 62.5% | -0.37 | -20.50 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.72 | 88.3 | 399 | 64.2% | +0.00 | -17.38 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.10 | 91.1 | 409 | 65.8% | +0.37 | -14.51 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.35 | 85.1 | 372 | 59.8% | -0.37 | -20.50 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.72 | 88.3 | 388 | 62.4% | +0.00 | -17.38 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.10 | 91.1 | 398 | 64.0% | +0.37 | -14.51 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.35 | 102.1 | 397 | 63.8% | -0.37 | -3.49 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.72 | 105.6 | 409 | 65.8% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.10 | 108.9 | 417 | 67.0% | +0.37 | +3.23 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.35 | 102.1 | 383 | 61.6% | -0.37 | -3.49 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.72 | 105.6 | 394 | 63.3% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.10 | 108.9 | 409 | 65.8% | +0.37 | +3.23 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.35 | 102.1 | 366 | 58.8% | -0.37 | -3.49 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.72 | 105.6 | 378 | 60.8% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.10 | 108.9 | 392 | 63.0% | +0.37 | +3.23 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.35 | 126.8 | 386 | 62.1% | -0.37 | +21.15 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.72 | 130.9 | 397 | 63.8% | +0.00 | +25.23 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.10 | 135.1 | 407 | 65.4% | +0.37 | +29.51 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.35 | 126.8 | 376 | 60.5% | -0.37 | +21.15 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.72 | 130.9 | 386 | 62.1% | +0.00 | +25.23 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.10 | 135.1 | 395 | 63.5% | +0.37 | +29.51 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.35 | 126.8 | 361 | 58.0% | -0.37 | +21.15 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.72 | 130.9 | 374 | 60.1% | +0.00 | +25.23 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.10 | 135.1 | 386 | 62.1% | +0.37 | +29.51 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._