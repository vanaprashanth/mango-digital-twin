# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-07-07
- **Number of days:** 552
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
| Mean ETc | 3.76 mm/day |
| Mean root-zone depletion | 96.8 mm |
| High-stress days | 297 (53.8%) |
| Medium-stress days | 37 |
| Low-stress days | 218 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.76 | 63.8 | 307 (55.6%) | +10.00 |
| **1.0** | 126 | 63 | 3.76 | 80.4 | 302 (54.7%) | +5.00 |
| **1.2** | 152 | 76 | 3.76 | 96.8 | 297 (53.8%) | +0.00 |
| **1.5** | 190 | 95 | 3.76 | 120.4 | 289 (52.4%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 96.8 | 312 (56.5%) | +15.00 |
| **0.50** | 76 | 96.8 | 297 (53.8%) | +0.00 |
| **0.60** | 91 | 96.8 | 281 (50.9%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.38 | -0.38 mm/d | 92.7 | 286 (51.8%) | -11.00 |
| **1.00** | 3.76 | +0.00 mm/d | 96.8 | 297 (53.8%) | +0.00 |
| **1.10** | 4.13 | +0.38 mm/d | 100.6 | 312 (56.5%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **327** (59.2%)
- Mean ETc: 4.13 mm/day
- Mean depletion: 66.4 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **264** (47.8%)
- Mean ETc: 3.38 mm/day
- Mean depletion: 115.7 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.38 | 61.4 | 306 | 55.4% | -0.38 | -35.30 | +9.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.76 | 63.8 | 317 | 57.4% | +0.00 | -32.96 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.13 | 66.4 | 327 | 59.2% | +0.38 | -30.36 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.38 | 61.4 | 295 | 53.4% | -0.38 | -35.30 | -2.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.76 | 63.8 | 307 | 55.6% | +0.00 | -32.96 | +10.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.13 | 66.4 | 318 | 57.6% | +0.38 | -30.36 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.38 | 61.4 | 282 | 51.1% | -0.38 | -35.30 | -15.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.76 | 63.8 | 295 | 53.4% | +0.00 | -32.96 | -2.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.13 | 66.4 | 307 | 55.6% | +0.38 | -30.36 | +10.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.38 | 76.8 | 306 | 55.4% | -0.38 | -19.99 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.76 | 80.4 | 316 | 57.2% | +0.00 | -16.38 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.13 | 83.8 | 327 | 59.2% | +0.38 | -12.95 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.38 | 76.8 | 291 | 52.7% | -0.38 | -19.99 | -6.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.76 | 80.4 | 302 | 54.7% | +0.00 | -16.38 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.13 | 83.8 | 312 | 56.5% | +0.38 | -12.95 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.38 | 76.8 | 274 | 49.6% | -0.38 | -19.99 | -23.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.76 | 80.4 | 290 | 52.5% | +0.00 | -16.38 | -7.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.13 | 83.8 | 301 | 54.5% | +0.38 | -12.95 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.38 | 92.7 | 300 | 54.4% | -0.38 | -4.03 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.76 | 96.8 | 312 | 56.5% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.13 | 100.6 | 321 | 58.1% | +0.38 | +3.83 | +24.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.38 | 92.7 | 286 | 51.8% | -0.38 | -4.03 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.76 | 96.8 | 297 | 53.8% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.13 | 100.6 | 312 | 56.5% | +0.38 | +3.83 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.38 | 92.7 | 268 | 48.5% | -0.38 | -4.03 | -29.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.76 | 96.8 | 281 | 50.9% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.13 | 100.6 | 295 | 53.4% | +0.38 | +3.83 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.38 | 115.7 | 290 | 52.5% | -0.38 | +18.92 | -7.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.76 | 120.4 | 309 | 56.0% | +0.00 | +23.62 | +12.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.13 | 125.4 | 320 | 58.0% | +0.38 | +28.64 | +23.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.38 | 115.7 | 279 | 50.5% | -0.38 | +18.92 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.76 | 120.4 | 289 | 52.4% | +0.00 | +23.62 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.13 | 125.4 | 301 | 54.5% | +0.38 | +28.64 | +4.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.38 | 115.7 | 264 | 47.8% | -0.38 | +18.92 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.76 | 120.4 | 277 | 50.2% | +0.00 | +23.62 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.13 | 125.4 | 289 | 52.4% | +0.38 | +28.64 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._