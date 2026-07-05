# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-06-30
- **Number of days:** 545
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
| Mean ETc | 3.77 mm/day |
| Mean root-zone depletion | 97.3 mm |
| High-stress days | 297 (54.5%) |
| Medium-stress days | 37 |
| Low-stress days | 211 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.77 | 64.6 | 307 (56.3%) | +10.00 |
| **1.0** | 126 | 63 | 3.77 | 81.1 | 302 (55.4%) | +5.00 |
| **1.2** | 152 | 76 | 3.77 | 97.3 | 297 (54.5%) | +0.00 |
| **1.5** | 190 | 95 | 3.77 | 120.8 | 289 (53.0%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 97.3 | 312 (57.2%) | +15.00 |
| **0.50** | 76 | 97.3 | 297 (54.5%) | +0.00 |
| **0.60** | 91 | 97.3 | 281 (51.6%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.39 | -0.38 mm/d | 93.4 | 286 (52.5%) | -11.00 |
| **1.00** | 3.77 | +0.00 mm/d | 97.3 | 297 (54.5%) | +0.00 |
| **1.10** | 4.14 | +0.38 mm/d | 101.1 | 312 (57.2%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **327** (60.0%)
- Mean ETc: 4.14 mm/day
- Mean depletion: 67.1 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **264** (48.4%)
- Mean ETc: 3.39 mm/day
- Mean depletion: 116.2 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.39 | 62.2 | 306 | 56.1% | -0.38 | -35.16 | +9.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.77 | 64.6 | 317 | 58.2% | +0.00 | -32.80 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.14 | 67.1 | 327 | 60.0% | +0.38 | -30.25 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.39 | 62.2 | 295 | 54.1% | -0.38 | -35.16 | -2.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.77 | 64.6 | 307 | 56.3% | +0.00 | -32.80 | +10.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.14 | 67.1 | 318 | 58.4% | +0.38 | -30.25 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.39 | 62.2 | 282 | 51.7% | -0.38 | -35.16 | -15.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.77 | 64.6 | 295 | 54.1% | +0.00 | -32.80 | -2.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.14 | 67.1 | 307 | 56.3% | +0.38 | -30.25 | +10.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.39 | 77.6 | 306 | 56.1% | -0.38 | -19.75 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.77 | 81.1 | 316 | 58.0% | +0.00 | -16.26 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.14 | 84.4 | 327 | 60.0% | +0.38 | -12.94 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.39 | 77.6 | 291 | 53.4% | -0.38 | -19.75 | -6.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.77 | 81.1 | 302 | 55.4% | +0.00 | -16.26 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.14 | 84.4 | 312 | 57.2% | +0.38 | -12.94 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.39 | 77.6 | 274 | 50.3% | -0.38 | -19.75 | -23.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.77 | 81.1 | 290 | 53.2% | +0.00 | -16.26 | -7.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.14 | 84.4 | 301 | 55.2% | +0.38 | -12.94 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.39 | 93.4 | 300 | 55.0% | -0.38 | -3.91 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.77 | 97.3 | 312 | 57.2% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.14 | 101.1 | 321 | 58.9% | +0.38 | +3.73 | +24.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.39 | 93.4 | 286 | 52.5% | -0.38 | -3.91 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.77 | 97.3 | 297 | 54.5% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.14 | 101.1 | 312 | 57.2% | +0.38 | +3.73 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.39 | 93.4 | 268 | 49.2% | -0.38 | -3.91 | -29.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.77 | 97.3 | 281 | 51.6% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.14 | 101.1 | 295 | 54.1% | +0.38 | +3.73 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.39 | 116.2 | 290 | 53.2% | -0.38 | +18.85 | -7.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.77 | 120.8 | 309 | 56.7% | +0.00 | +23.44 | +12.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.14 | 125.7 | 320 | 58.7% | +0.38 | +28.37 | +23.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.39 | 116.2 | 279 | 51.2% | -0.38 | +18.85 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.77 | 120.8 | 289 | 53.0% | +0.00 | +23.44 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.14 | 125.7 | 301 | 55.2% | +0.38 | +28.37 | +4.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.39 | 116.2 | 264 | 48.4% | -0.38 | +18.85 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.77 | 120.8 | 277 | 50.8% | +0.00 | +23.44 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.14 | 125.7 | 289 | 53.0% | +0.38 | +28.37 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._