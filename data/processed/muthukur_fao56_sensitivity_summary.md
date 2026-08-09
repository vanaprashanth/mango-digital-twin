# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-08-04
- **Number of days:** 581
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
| Mean ETc | 3.73 mm/day |
| Mean root-zone depletion | 103.2 mm |
| High-stress days | 353 (60.8%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.73 | 69.2 | 364 (62.6%) | +11.00 |
| **1.0** | 126 | 63 | 3.73 | 86.3 | 358 (61.6%) | +5.00 |
| **1.2** | 152 | 76 | 3.73 | 103.2 | 353 (60.8%) | +0.00 |
| **1.5** | 190 | 95 | 3.73 | 127.5 | 345 (59.4%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 103.2 | 368 (63.3%) | +15.00 |
| **0.50** | 76 | 103.2 | 353 (60.8%) | +0.00 |
| **0.60** | 91 | 103.2 | 337 (58.0%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.36 | -0.37 mm/d | 99.8 | 342 (58.9%) | -11.00 |
| **1.00** | 3.73 | +0.00 mm/d | 103.2 | 353 (60.8%) | +0.00 |
| **1.10** | 4.11 | +0.37 mm/d | 106.4 | 368 (63.3%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **383** (65.9%)
- Mean ETc: 4.11 mm/day
- Mean depletion: 71.4 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **320** (55.1%)
- Mean ETc: 3.36 mm/day
- Mean depletion: 123.5 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.36 | 67.2 | 363 | 62.5% | -0.37 | -35.95 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.73 | 69.2 | 373 | 64.2% | +0.00 | -33.91 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.11 | 71.4 | 383 | 65.9% | +0.37 | -31.72 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.36 | 67.2 | 352 | 60.6% | -0.37 | -35.95 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.73 | 69.2 | 364 | 62.6% | +0.00 | -33.91 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.11 | 71.4 | 374 | 64.4% | +0.37 | -31.72 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.36 | 67.2 | 338 | 58.2% | -0.37 | -35.95 | -15.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.73 | 69.2 | 351 | 60.4% | +0.00 | -33.91 | -2.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.11 | 71.4 | 364 | 62.6% | +0.37 | -31.72 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.36 | 83.3 | 362 | 62.3% | -0.37 | -19.83 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.73 | 86.3 | 372 | 64.0% | +0.00 | -16.82 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.11 | 89.2 | 383 | 65.9% | +0.37 | -13.92 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.36 | 83.3 | 348 | 59.9% | -0.37 | -19.83 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.73 | 86.3 | 358 | 61.6% | +0.00 | -16.82 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.11 | 89.2 | 368 | 63.3% | +0.37 | -13.92 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.36 | 83.3 | 331 | 57.0% | -0.37 | -19.83 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.73 | 86.3 | 347 | 59.7% | +0.00 | -16.82 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.11 | 89.2 | 357 | 61.5% | +0.37 | -13.92 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.36 | 99.8 | 356 | 61.3% | -0.37 | -3.40 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.73 | 103.2 | 368 | 63.3% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.11 | 106.4 | 376 | 64.7% | +0.37 | +3.28 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.36 | 99.8 | 342 | 58.9% | -0.37 | -3.40 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.73 | 103.2 | 353 | 60.8% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.11 | 106.4 | 368 | 63.3% | +0.37 | +3.28 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.36 | 99.8 | 325 | 55.9% | -0.37 | -3.40 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.73 | 103.2 | 337 | 58.0% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.11 | 106.4 | 351 | 60.4% | +0.37 | +3.28 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.36 | 123.5 | 345 | 59.4% | -0.37 | +20.30 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.73 | 127.5 | 356 | 61.3% | +0.00 | +24.34 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.11 | 131.9 | 366 | 63.0% | +0.37 | +28.75 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.36 | 123.5 | 335 | 57.7% | -0.37 | +20.30 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.73 | 127.5 | 345 | 59.4% | +0.00 | +24.34 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.11 | 131.9 | 354 | 60.9% | +0.37 | +28.75 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.36 | 123.5 | 320 | 55.1% | -0.37 | +20.30 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.73 | 127.5 | 333 | 57.3% | +0.00 | +24.34 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.11 | 131.9 | 345 | 59.4% | +0.37 | +28.75 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._