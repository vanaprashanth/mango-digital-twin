# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-07-10
- **Number of days:** 555
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
| Mean ETc | 3.75 mm/day |
| Mean root-zone depletion | 96.5 mm |
| High-stress days | 297 (53.5%) |
| Medium-stress days | 37 |
| Low-stress days | 221 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.75 | 63.5 | 307 (55.3%) | +10.00 |
| **1.0** | 126 | 63 | 3.75 | 80.1 | 302 (54.4%) | +5.00 |
| **1.2** | 152 | 76 | 3.75 | 96.5 | 297 (53.5%) | +0.00 |
| **1.5** | 190 | 95 | 3.75 | 120.2 | 289 (52.1%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 96.5 | 312 (56.2%) | +15.00 |
| **0.50** | 76 | 96.5 | 297 (53.5%) | +0.00 |
| **0.60** | 91 | 96.5 | 281 (50.6%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.37 | -0.37 mm/d | 92.4 | 286 (51.5%) | -11.00 |
| **1.00** | 3.75 | +0.00 mm/d | 96.5 | 297 (53.5%) | +0.00 |
| **1.10** | 4.12 | +0.37 mm/d | 100.4 | 312 (56.2%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **327** (58.9%)
- Mean ETc: 4.12 mm/day
- Mean depletion: 66.1 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **264** (47.6%)
- Mean ETc: 3.37 mm/day
- Mean depletion: 115.5 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.37 | 61.2 | 306 | 55.1% | -0.37 | -35.37 | +9.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.75 | 63.5 | 317 | 57.1% | +0.00 | -33.03 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.12 | 66.1 | 327 | 58.9% | +0.37 | -30.40 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.37 | 61.2 | 295 | 53.1% | -0.37 | -35.37 | -2.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.75 | 63.5 | 307 | 55.3% | +0.00 | -33.03 | +10.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.12 | 66.1 | 318 | 57.3% | +0.37 | -30.40 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.37 | 61.2 | 282 | 50.8% | -0.37 | -35.37 | -15.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.75 | 63.5 | 295 | 53.1% | +0.00 | -33.03 | -2.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.12 | 66.1 | 307 | 55.3% | +0.37 | -30.40 | +10.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.37 | 76.4 | 306 | 55.1% | -0.37 | -20.10 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.75 | 80.1 | 316 | 56.9% | +0.00 | -16.43 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.12 | 83.6 | 327 | 58.9% | +0.37 | -12.95 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.37 | 76.4 | 291 | 52.4% | -0.37 | -20.10 | -6.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.75 | 80.1 | 302 | 54.4% | +0.00 | -16.43 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.12 | 83.6 | 312 | 56.2% | +0.37 | -12.95 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.37 | 76.4 | 274 | 49.4% | -0.37 | -20.10 | -23.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.75 | 80.1 | 290 | 52.2% | +0.00 | -16.43 | -7.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.12 | 83.6 | 301 | 54.2% | +0.37 | -12.95 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.37 | 92.4 | 300 | 54.0% | -0.37 | -4.09 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.75 | 96.5 | 312 | 56.2% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.12 | 100.4 | 321 | 57.8% | +0.37 | +3.88 | +24.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.37 | 92.4 | 286 | 51.5% | -0.37 | -4.09 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.75 | 96.5 | 297 | 53.5% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.12 | 100.4 | 312 | 56.2% | +0.37 | +3.88 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.37 | 92.4 | 268 | 48.3% | -0.37 | -4.09 | -29.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.75 | 96.5 | 281 | 50.6% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.12 | 100.4 | 295 | 53.1% | +0.37 | +3.88 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.37 | 115.5 | 290 | 52.2% | -0.37 | +18.94 | -7.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.75 | 120.2 | 309 | 55.7% | +0.00 | +23.70 | +12.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.12 | 125.3 | 320 | 57.7% | +0.37 | +28.76 | +23.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.37 | 115.5 | 279 | 50.3% | -0.37 | +18.94 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.75 | 120.2 | 289 | 52.1% | +0.00 | +23.70 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.12 | 125.3 | 301 | 54.2% | +0.37 | +28.76 | +4.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.37 | 115.5 | 264 | 47.6% | -0.37 | +18.94 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.75 | 120.2 | 277 | 49.9% | +0.00 | +23.70 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.12 | 125.3 | 289 | 52.1% | +0.37 | +28.76 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._