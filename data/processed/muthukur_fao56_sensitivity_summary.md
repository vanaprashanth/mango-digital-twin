# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-10-16
- **Number of days:** 651
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 5.03 mm/day |
| Mean ETc | 3.73 mm/day |
| Mean root-zone depletion | 106.3 mm |
| High-stress days | 402 (61.8%) |
| Medium-stress days | 48 |
| Low-stress days | 201 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.73 | 70.7 | 409 (62.8%) | +7.00 |
| **1.0** | 126 | 63 | 3.73 | 88.6 | 403 (61.9%) | +1.00 |
| **1.2** | 152 | 76 | 3.73 | 106.3 | 402 (61.8%) | +0.00 |
| **1.5** | 190 | 95 | 3.73 | 132.1 | 409 (62.8%) | +7.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 106.3 | 430 (66.0%) | +28.00 |
| **0.50** | 76 | 106.3 | 402 (61.8%) | +0.00 |
| **0.60** | 91 | 106.3 | 382 (58.7%) | -20.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.36 | -0.37 mm/d | 103.2 | 388 (59.6%) | -14.00 |
| **1.00** | 3.73 | +0.00 mm/d | 106.3 | 402 (61.8%) | +0.00 |
| **1.10** | 4.10 | +0.37 mm/d | 109.4 | 422 (64.8%) | +20.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.2 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **442** (67.9%)
- Mean ETc: 4.10 mm/day
- Mean depletion: 109.4 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **366** (56.2%)
- Mean ETc: 3.36 mm/day
- Mean depletion: 128.4 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.36 | 68.7 | 408 | 62.7% | -0.37 | -37.61 | +6.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.73 | 70.7 | 418 | 64.2% | +0.00 | -35.69 | +16.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.10 | 72.7 | 429 | 65.9% | +0.37 | -33.59 | +27.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.36 | 68.7 | 397 | 61.0% | -0.37 | -37.61 | -5.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.73 | 70.7 | 409 | 62.8% | +0.00 | -35.69 | +7.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.10 | 72.7 | 419 | 64.4% | +0.37 | -33.59 | +17.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.36 | 68.7 | 383 | 58.8% | -0.37 | -37.61 | -19.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.73 | 70.7 | 396 | 60.8% | +0.00 | -35.69 | -6.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.10 | 72.7 | 409 | 62.8% | +0.37 | -33.59 | +7.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.36 | 85.8 | 408 | 62.7% | -0.37 | -20.53 | +6.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.73 | 88.6 | 421 | 64.7% | +0.00 | -17.73 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.10 | 91.3 | 437 | 67.1% | +0.37 | -15.00 | +35.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.36 | 85.8 | 393 | 60.4% | -0.37 | -20.53 | -9.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.73 | 88.6 | 403 | 61.9% | +0.00 | -17.73 | +1.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.10 | 91.3 | 414 | 63.6% | +0.37 | -15.00 | +12.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.36 | 85.8 | 376 | 57.8% | -0.37 | -20.53 | -26.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.73 | 88.6 | 392 | 60.2% | +0.00 | -17.73 | -10.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.10 | 91.3 | 402 | 61.8% | +0.37 | -15.00 | +0.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.36 | 103.2 | 409 | 62.8% | -0.37 | -3.15 | +7.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.73 | 106.3 | 430 | 66.0% | +0.00 | +0.00 | +28.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.10 | 109.4 | 442 | 67.9% | +0.37 | +3.08 | +40.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.36 | 103.2 | 388 | 59.6% | -0.37 | -3.15 | -14.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.73 | 106.3 | 402 | 61.8% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.10 | 109.4 | 422 | 64.8% | +0.37 | +3.08 | +20.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.36 | 103.2 | 370 | 56.8% | -0.37 | -3.15 | -32.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.73 | 106.3 | 382 | 58.7% | +0.00 | +0.00 | -20.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.10 | 109.4 | 397 | 61.0% | +0.37 | +3.08 | -5.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.36 | 128.4 | 414 | 63.6% | -0.37 | +22.08 | +12.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.73 | 132.1 | 425 | 65.3% | +0.00 | +25.80 | +23.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.10 | 136.2 | 435 | 66.8% | +0.37 | +29.88 | +33.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.36 | 128.4 | 392 | 60.2% | -0.37 | +22.08 | -10.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.73 | 132.1 | 409 | 62.8% | +0.00 | +25.80 | +7.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.10 | 136.2 | 420 | 64.5% | +0.37 | +29.88 | +18.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.36 | 128.4 | 366 | 56.2% | -0.37 | +22.08 | -36.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.73 | 132.1 | 382 | 58.7% | +0.00 | +25.80 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.10 | 136.2 | 399 | 61.3% | +0.37 | +29.88 | -3.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._