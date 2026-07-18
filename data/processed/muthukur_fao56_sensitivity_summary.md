# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-07-13
- **Number of days:** 558
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 4.86 mm/day |
| Mean ETc | 3.74 mm/day |
| Mean root-zone depletion | 96.3 mm |
| High-stress days | 297 (53.2%) |
| Medium-stress days | 37 |
| Low-stress days | 224 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.74 | 63.2 | 307 (55.0%) | +10.00 |
| **1.0** | 126 | 63 | 3.74 | 79.9 | 302 (54.1%) | +5.00 |
| **1.2** | 152 | 76 | 3.74 | 96.3 | 297 (53.2%) | +0.00 |
| **1.5** | 190 | 95 | 3.74 | 120.1 | 289 (51.8%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 96.3 | 312 (55.9%) | +15.00 |
| **0.50** | 76 | 96.3 | 297 (53.2%) | +0.00 |
| **0.60** | 91 | 96.3 | 281 (50.4%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.36 | -0.37 mm/d | 92.2 | 286 (51.2%) | -11.00 |
| **1.00** | 3.74 | +0.00 mm/d | 96.3 | 297 (53.2%) | +0.00 |
| **1.10** | 4.11 | +0.37 mm/d | 100.3 | 312 (55.9%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **327** (58.6%)
- Mean ETc: 4.11 mm/day
- Mean depletion: 65.9 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **264** (47.3%)
- Mean ETc: 3.36 mm/day
- Mean depletion: 115.3 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.36 | 60.9 | 306 | 54.8% | -0.37 | -35.44 | +9.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.74 | 63.2 | 317 | 56.8% | +0.00 | -33.10 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.11 | 65.9 | 327 | 58.6% | +0.37 | -30.43 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.36 | 60.9 | 295 | 52.9% | -0.37 | -35.44 | -2.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.74 | 63.2 | 307 | 55.0% | +0.00 | -33.10 | +10.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.11 | 65.9 | 318 | 57.0% | +0.37 | -30.43 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.36 | 60.9 | 282 | 50.5% | -0.37 | -35.44 | -15.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.74 | 63.2 | 295 | 52.9% | +0.00 | -33.10 | -2.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.11 | 65.9 | 307 | 55.0% | +0.37 | -30.43 | +10.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.36 | 76.1 | 306 | 54.8% | -0.37 | -20.21 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.74 | 79.9 | 316 | 56.6% | +0.00 | -16.47 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.11 | 83.4 | 327 | 58.6% | +0.37 | -12.94 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.36 | 76.1 | 291 | 52.1% | -0.37 | -20.21 | -6.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.74 | 79.9 | 302 | 54.1% | +0.00 | -16.47 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.11 | 83.4 | 312 | 55.9% | +0.37 | -12.94 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.36 | 76.1 | 274 | 49.1% | -0.37 | -20.21 | -23.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.74 | 79.9 | 290 | 52.0% | +0.00 | -16.47 | -7.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.11 | 83.4 | 301 | 53.9% | +0.37 | -12.94 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.36 | 92.2 | 300 | 53.8% | -0.37 | -4.15 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.74 | 96.3 | 312 | 55.9% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.11 | 100.3 | 321 | 57.5% | +0.37 | +3.93 | +24.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.36 | 92.2 | 286 | 51.2% | -0.37 | -4.15 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.74 | 96.3 | 297 | 53.2% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.11 | 100.3 | 312 | 55.9% | +0.37 | +3.93 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.36 | 92.2 | 268 | 48.0% | -0.37 | -4.15 | -29.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.74 | 96.3 | 281 | 50.4% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.11 | 100.3 | 295 | 52.9% | +0.37 | +3.93 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.36 | 115.3 | 290 | 52.0% | -0.37 | +18.96 | -7.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.74 | 120.1 | 309 | 55.4% | +0.00 | +23.78 | +12.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.11 | 125.2 | 320 | 57.4% | +0.37 | +28.88 | +23.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.36 | 115.3 | 279 | 50.0% | -0.37 | +18.96 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.74 | 120.1 | 289 | 51.8% | +0.00 | +23.78 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.11 | 125.2 | 301 | 53.9% | +0.37 | +28.88 | +4.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.36 | 115.3 | 264 | 47.3% | -0.37 | +18.96 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.74 | 120.1 | 277 | 49.6% | +0.00 | +23.78 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.11 | 125.2 | 289 | 51.8% | +0.37 | +28.88 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._