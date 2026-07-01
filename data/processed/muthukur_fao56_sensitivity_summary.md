# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 – 2026-06-21
- **Number of days:** 536
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.87 mm/day |
| Mean ETc | 3.78 mm/day |
| Mean root-zone depletion | 98.0 mm |
| High-stress days | 297 (55.4%) |
| Medium-stress days | 37 |
| Low-stress days | 202 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.78 | 65.5 | 307 (57.3%) | +10.00 |
| **1.0** | 126 | 63 | 3.78 | 81.9 | 302 (56.3%) | +5.00 |
| **1.2** | 152 | 76 | 3.78 | 98.0 | 297 (55.4%) | +0.00 |
| **1.5** | 190 | 95 | 3.78 | 121.2 | 289 (53.9%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 98.0 | 312 (58.2%) | +15.00 |
| **0.50** | 76 | 98.0 | 297 (55.4%) | +0.00 |
| **0.60** | 91 | 98.0 | 281 (52.4%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.40 | -0.38 mm/d | 94.3 | 286 (53.4%) | -11.00 |
| **1.00** | 3.78 | +0.00 mm/d | 98.0 | 297 (55.4%) | +0.00 |
| **1.10** | 4.16 | +0.38 mm/d | 101.7 | 312 (58.2%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **327** (61.0%)
- Mean ETc: 4.16 mm/day
- Mean depletion: 68.0 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **264** (49.2%)
- Mean ETc: 3.40 mm/day
- Mean depletion: 116.8 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.40 | 63.2 | 306 | 57.1% | -0.38 | -34.82 | +9.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.78 | 65.5 | 317 | 59.1% | +0.00 | -32.52 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.16 | 68.0 | 327 | 61.0% | +0.38 | -30.06 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.40 | 63.2 | 295 | 55.0% | -0.38 | -34.82 | -2.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.78 | 65.5 | 307 | 57.3% | +0.00 | -32.52 | +10.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.16 | 68.0 | 318 | 59.3% | +0.38 | -30.06 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.40 | 63.2 | 282 | 52.6% | -0.38 | -34.82 | -15.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.78 | 65.5 | 295 | 55.0% | +0.00 | -32.52 | -2.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.16 | 68.0 | 307 | 57.3% | +0.38 | -30.06 | +10.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.40 | 78.6 | 306 | 57.1% | -0.38 | -19.46 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.78 | 81.9 | 316 | 59.0% | +0.00 | -16.11 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.16 | 85.1 | 327 | 61.0% | +0.38 | -12.89 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.40 | 78.6 | 291 | 54.3% | -0.38 | -19.46 | -6.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.78 | 81.9 | 302 | 56.3% | +0.00 | -16.11 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.16 | 85.1 | 312 | 58.2% | +0.38 | -12.89 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.40 | 78.6 | 274 | 51.1% | -0.38 | -19.46 | -23.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.78 | 81.9 | 290 | 54.1% | +0.00 | -16.11 | -7.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.16 | 85.1 | 301 | 56.2% | +0.38 | -12.89 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.40 | 94.3 | 300 | 56.0% | -0.38 | -3.78 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.78 | 98.0 | 312 | 58.2% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.16 | 101.7 | 321 | 59.9% | +0.38 | +3.63 | +24.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.40 | 94.3 | 286 | 53.4% | -0.38 | -3.78 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.78 | 98.0 | 297 | 55.4% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.16 | 101.7 | 312 | 58.2% | +0.38 | +3.63 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.40 | 94.3 | 268 | 50.0% | -0.38 | -3.78 | -29.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.78 | 98.0 | 281 | 52.4% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.16 | 101.7 | 295 | 55.0% | +0.38 | +3.63 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.40 | 116.8 | 290 | 54.1% | -0.38 | +18.72 | -7.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.78 | 121.2 | 309 | 57.6% | +0.00 | +23.20 | +12.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.16 | 126.1 | 320 | 59.7% | +0.38 | +28.05 | +23.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.40 | 116.8 | 279 | 52.0% | -0.38 | +18.72 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.78 | 121.2 | 289 | 53.9% | +0.00 | +23.20 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.16 | 126.1 | 301 | 56.2% | +0.38 | +28.05 | +4.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.40 | 116.8 | 264 | 49.2% | -0.38 | +18.72 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.78 | 121.2 | 277 | 51.7% | +0.00 | +23.20 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.16 | 126.1 | 289 | 53.9% | +0.38 | +28.05 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._