# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-11-09
- **Number of days:** 678
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.96 mm/day |
| Mean ETc | 3.67 mm/day |
| Mean root-zone depletion | 102.6 mm |
| High-stress days | 404 (59.6%) |
| Medium-stress days | 48 |
| Low-stress days | 226 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.67 | 68.1 | 409 (60.3%) | +5.00 |
| **1.0** | 126 | 63 | 3.67 | 85.5 | 404 (59.6%) | +0.00 |
| **1.2** | 152 | 76 | 3.67 | 102.6 | 404 (59.6%) | +0.00 |
| **1.5** | 190 | 95 | 3.67 | 127.7 | 411 (60.6%) | +7.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 102.6 | 432 (63.7%) | +28.00 |
| **0.50** | 76 | 102.6 | 404 (59.6%) | +0.00 |
| **0.60** | 91 | 102.6 | 382 (56.3%) | -22.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.30 | -0.37 mm/d | 99.5 | 389 (57.4%) | -15.00 |
| **1.00** | 3.67 | +0.00 mm/d | 102.6 | 404 (59.6%) | +0.00 |
| **1.10** | 4.04 | +0.37 mm/d | 105.6 | 424 (62.5%) | +20.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 1.2 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **444** (65.5%)
- Mean ETc: 4.04 mm/day
- Mean depletion: 105.6 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **367** (54.1%)
- Mean ETc: 3.30 mm/day
- Mean depletion: 124.0 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.30 | 66.3 | 408 | 60.2% | -0.37 | -36.36 | +4.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.67 | 68.1 | 418 | 61.6% | +0.00 | -34.46 | +14.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.04 | 70.2 | 431 | 63.6% | +0.37 | -32.40 | +27.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.30 | 66.3 | 397 | 58.5% | -0.37 | -36.36 | -7.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.67 | 68.1 | 409 | 60.3% | +0.00 | -34.46 | +5.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.04 | 70.2 | 420 | 62.0% | +0.37 | -32.40 | +16.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.30 | 66.3 | 383 | 56.5% | -0.37 | -36.36 | -21.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.67 | 68.1 | 396 | 58.4% | +0.00 | -34.46 | -8.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.04 | 70.2 | 409 | 60.3% | +0.37 | -32.40 | +5.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.30 | 82.8 | 409 | 60.3% | -0.37 | -19.85 | +5.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.67 | 85.5 | 423 | 62.4% | +0.00 | -17.13 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.04 | 88.2 | 439 | 64.8% | +0.37 | -14.46 | +35.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.30 | 82.8 | 393 | 58.0% | -0.37 | -19.85 | -11.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.67 | 85.5 | 404 | 59.6% | +0.00 | -17.13 | +0.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.04 | 88.2 | 416 | 61.4% | +0.37 | -14.46 | +12.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.30 | 82.8 | 376 | 55.5% | -0.37 | -19.85 | -28.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.67 | 85.5 | 392 | 57.8% | +0.00 | -17.13 | -12.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.04 | 88.2 | 403 | 59.4% | +0.37 | -14.46 | -1.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.30 | 99.5 | 411 | 60.6% | -0.37 | -3.08 | +7.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.67 | 102.6 | 432 | 63.7% | +0.00 | +0.00 | +28.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.04 | 105.6 | 444 | 65.5% | +0.37 | +3.01 | +40.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.30 | 99.5 | 389 | 57.4% | -0.37 | -3.08 | -15.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.67 | 102.6 | 404 | 59.6% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.04 | 105.6 | 424 | 62.5% | +0.37 | +3.01 | +20.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.30 | 99.5 | 370 | 54.6% | -0.37 | -3.08 | -34.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.67 | 102.6 | 382 | 56.3% | +0.00 | +0.00 | -22.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.04 | 105.6 | 399 | 58.9% | +0.37 | +3.01 | -5.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.30 | 124.0 | 415 | 61.2% | -0.37 | +21.37 | +11.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.67 | 127.7 | 427 | 63.0% | +0.00 | +25.05 | +23.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.04 | 131.7 | 438 | 64.6% | +0.37 | +29.09 | +34.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.30 | 124.0 | 394 | 58.1% | -0.37 | +21.37 | -10.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.67 | 127.7 | 411 | 60.6% | +0.00 | +25.05 | +7.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.04 | 131.7 | 422 | 62.2% | +0.37 | +29.09 | +18.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.30 | 124.0 | 367 | 54.1% | -0.37 | +21.37 | -37.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.67 | 127.7 | 384 | 56.6% | +0.00 | +25.05 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.04 | 131.7 | 401 | 59.1% | +0.37 | +29.09 | -3.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._