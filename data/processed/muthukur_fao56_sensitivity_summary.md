# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-06-29
- **Number of days:** 544
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
| Mean root-zone depletion | 97.4 mm |
| High-stress days | 297 (54.6%) |
| Medium-stress days | 37 |
| Low-stress days | 210 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.77 | 64.7 | 307 (56.4%) | +10.00 |
| **1.0** | 126 | 63 | 3.77 | 81.2 | 302 (55.5%) | +5.00 |
| **1.2** | 152 | 76 | 3.77 | 97.4 | 297 (54.6%) | +0.00 |
| **1.5** | 190 | 95 | 3.77 | 120.9 | 289 (53.1%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 97.4 | 312 (57.4%) | +15.00 |
| **0.50** | 76 | 97.4 | 297 (54.6%) | +0.00 |
| **0.60** | 91 | 97.4 | 281 (51.6%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.39 | -0.38 mm/d | 93.6 | 286 (52.6%) | -11.00 |
| **1.00** | 3.77 | +0.00 mm/d | 97.4 | 297 (54.6%) | +0.00 |
| **1.10** | 4.15 | +0.38 mm/d | 101.2 | 312 (57.4%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **327** (60.1%)
- Mean ETc: 4.15 mm/day
- Mean depletion: 67.2 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **264** (48.5%)
- Mean ETc: 3.39 mm/day
- Mean depletion: 116.3 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.39 | 62.3 | 306 | 56.2% | -0.38 | -35.14 | +9.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.77 | 64.7 | 317 | 58.3% | +0.00 | -32.77 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.15 | 67.2 | 327 | 60.1% | +0.38 | -30.23 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.39 | 62.3 | 295 | 54.2% | -0.38 | -35.14 | -2.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.77 | 64.7 | 307 | 56.4% | +0.00 | -32.77 | +10.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.15 | 67.2 | 318 | 58.5% | +0.38 | -30.23 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.39 | 62.3 | 282 | 51.8% | -0.38 | -35.14 | -15.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.77 | 64.7 | 295 | 54.2% | +0.00 | -32.77 | -2.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.15 | 67.2 | 307 | 56.4% | +0.38 | -30.23 | +10.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.39 | 77.7 | 306 | 56.2% | -0.38 | -19.71 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.77 | 81.2 | 316 | 58.1% | +0.00 | -16.25 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.15 | 84.5 | 327 | 60.1% | +0.38 | -12.94 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.39 | 77.7 | 291 | 53.5% | -0.38 | -19.71 | -6.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.77 | 81.2 | 302 | 55.5% | +0.00 | -16.25 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.15 | 84.5 | 312 | 57.4% | +0.38 | -12.94 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.39 | 77.7 | 274 | 50.4% | -0.38 | -19.71 | -23.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.77 | 81.2 | 290 | 53.3% | +0.00 | -16.25 | -7.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.15 | 84.5 | 301 | 55.3% | +0.38 | -12.94 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.39 | 93.6 | 300 | 55.1% | -0.38 | -3.89 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.77 | 97.4 | 312 | 57.4% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.15 | 101.2 | 321 | 59.0% | +0.38 | +3.72 | +24.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.39 | 93.6 | 286 | 52.6% | -0.38 | -3.89 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.77 | 97.4 | 297 | 54.6% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.15 | 101.2 | 312 | 57.4% | +0.38 | +3.72 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.39 | 93.6 | 268 | 49.3% | -0.38 | -3.89 | -29.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.77 | 97.4 | 281 | 51.6% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.15 | 101.2 | 295 | 54.2% | +0.38 | +3.72 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.39 | 116.3 | 290 | 53.3% | -0.38 | +18.84 | -7.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.77 | 120.9 | 309 | 56.8% | +0.00 | +23.41 | +12.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.15 | 125.8 | 320 | 58.8% | +0.38 | +28.33 | +23.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.39 | 116.3 | 279 | 51.3% | -0.38 | +18.84 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.77 | 120.9 | 289 | 53.1% | +0.00 | +23.41 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.15 | 125.8 | 301 | 55.3% | +0.38 | +28.33 | +4.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.39 | 116.3 | 264 | 48.5% | -0.38 | +18.84 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.77 | 120.9 | 277 | 50.9% | +0.00 | +23.41 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.15 | 125.8 | 289 | 53.1% | +0.38 | +28.33 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._