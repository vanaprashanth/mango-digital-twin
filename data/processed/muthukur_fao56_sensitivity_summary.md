# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-07-17
- **Number of days:** 559
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
| Mean ETc | 3.76 mm/day |
| Mean root-zone depletion | 101.4 mm |
| High-stress days | 331 (59.2%) |
| Medium-stress days | 28 |
| Low-stress days | 200 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.76 | 68.1 | 342 (61.2%) | +11.00 |
| **1.0** | 126 | 63 | 3.76 | 84.9 | 336 (60.1%) | +5.00 |
| **1.2** | 152 | 76 | 3.76 | 101.4 | 331 (59.2%) | +0.00 |
| **1.5** | 190 | 95 | 3.76 | 125.2 | 323 (57.8%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 101.4 | 346 (61.9%) | +15.00 |
| **0.50** | 76 | 101.4 | 331 (59.2%) | +0.00 |
| **0.60** | 91 | 101.4 | 315 (56.4%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.39 | -0.38 mm/d | 97.9 | 320 (57.2%) | -11.00 |
| **1.00** | 3.76 | +0.00 mm/d | 101.4 | 331 (59.2%) | +0.00 |
| **1.10** | 4.14 | +0.38 mm/d | 104.7 | 346 (61.9%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **361** (64.6%)
- Mean ETc: 4.14 mm/day
- Mean depletion: 70.3 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **298** (53.3%)
- Mean ETc: 3.39 mm/day
- Mean depletion: 121.0 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.39 | 66.1 | 341 | 61.0% | -0.38 | -35.30 | +10.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.76 | 68.1 | 351 | 62.8% | +0.00 | -33.26 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.14 | 70.3 | 361 | 64.6% | +0.38 | -31.03 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.39 | 66.1 | 330 | 59.0% | -0.38 | -35.30 | -1.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.76 | 68.1 | 342 | 61.2% | +0.00 | -33.26 | +11.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.14 | 70.3 | 352 | 63.0% | +0.38 | -31.03 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.39 | 66.1 | 317 | 56.7% | -0.38 | -35.30 | -14.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.76 | 68.1 | 330 | 59.0% | +0.00 | -33.26 | -1.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.14 | 70.3 | 342 | 61.2% | +0.38 | -31.03 | +11.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.39 | 81.8 | 340 | 60.8% | -0.38 | -19.53 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.76 | 84.9 | 350 | 62.6% | +0.00 | -16.49 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.14 | 87.8 | 361 | 64.6% | +0.38 | -13.53 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.39 | 81.8 | 326 | 58.3% | -0.38 | -19.53 | -5.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.76 | 84.9 | 336 | 60.1% | +0.00 | -16.49 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.14 | 87.8 | 346 | 61.9% | +0.38 | -13.53 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.39 | 81.8 | 309 | 55.3% | -0.38 | -19.53 | -22.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.76 | 84.9 | 325 | 58.1% | +0.00 | -16.49 | -6.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.14 | 87.8 | 335 | 59.9% | +0.38 | -13.53 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.39 | 97.9 | 334 | 59.8% | -0.38 | -3.45 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.76 | 101.4 | 346 | 61.9% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.14 | 104.7 | 354 | 63.3% | +0.38 | +3.36 | +23.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.39 | 97.9 | 320 | 57.2% | -0.38 | -3.45 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.76 | 101.4 | 331 | 59.2% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.14 | 104.7 | 346 | 61.9% | +0.38 | +3.36 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.39 | 97.9 | 303 | 54.2% | -0.38 | -3.45 | -28.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.76 | 101.4 | 315 | 56.4% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.14 | 104.7 | 329 | 58.9% | +0.38 | +3.36 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.39 | 121.0 | 323 | 57.8% | -0.38 | +19.68 | -8.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.76 | 125.2 | 334 | 59.8% | +0.00 | +23.80 | +3.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.14 | 129.7 | 344 | 61.5% | +0.38 | +28.33 | +13.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.39 | 121.0 | 313 | 56.0% | -0.38 | +19.68 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.76 | 125.2 | 323 | 57.8% | +0.00 | +23.80 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.14 | 129.7 | 332 | 59.4% | +0.38 | +28.33 | +1.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.39 | 121.0 | 298 | 53.3% | -0.38 | +19.68 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.76 | 125.2 | 311 | 55.6% | +0.00 | +23.80 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.14 | 129.7 | 323 | 57.8% | +0.38 | +28.33 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._