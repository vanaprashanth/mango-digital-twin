# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-07-05
- **Number of days:** 550
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
| Mean root-zone depletion | 96.9 mm |
| High-stress days | 297 (54.0%) |
| Medium-stress days | 37 |
| Low-stress days | 216 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.76 | 64.0 | 307 (55.8%) | +10.00 |
| **1.0** | 126 | 63 | 3.76 | 80.6 | 302 (54.9%) | +5.00 |
| **1.2** | 152 | 76 | 3.76 | 96.9 | 297 (54.0%) | +0.00 |
| **1.5** | 190 | 95 | 3.76 | 120.5 | 289 (52.5%) | -8.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 96.9 | 312 (56.7%) | +15.00 |
| **0.50** | 76 | 96.9 | 297 (54.0%) | +0.00 |
| **0.60** | 91 | 96.9 | 281 (51.1%) | -16.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.38 | -0.38 mm/d | 92.9 | 286 (52.0%) | -11.00 |
| **1.00** | 3.76 | +0.00 mm/d | 96.9 | 297 (54.0%) | +0.00 |
| **1.10** | 4.13 | +0.38 mm/d | 100.7 | 312 (56.7%) | +15.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **327** (59.5%)
- Mean ETc: 4.13 mm/day
- Mean depletion: 66.6 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **264** (48.0%)
- Mean ETc: 3.38 mm/day
- Mean depletion: 115.8 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.38 | 61.6 | 306 | 55.6% | -0.38 | -35.26 | +9.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.76 | 64.0 | 317 | 57.6% | +0.00 | -32.91 | +20.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.13 | 66.6 | 327 | 59.5% | +0.38 | -30.33 | +30.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.38 | 61.6 | 295 | 53.6% | -0.38 | -35.26 | -2.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.76 | 64.0 | 307 | 55.8% | +0.00 | -32.91 | +10.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.13 | 66.6 | 318 | 57.8% | +0.38 | -30.33 | +21.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.38 | 61.6 | 282 | 51.3% | -0.38 | -35.26 | -15.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.76 | 64.0 | 295 | 53.6% | +0.00 | -32.91 | -2.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.13 | 66.6 | 307 | 55.8% | +0.38 | -30.33 | +10.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.38 | 77.0 | 306 | 55.6% | -0.38 | -19.92 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.76 | 80.6 | 316 | 57.5% | +0.00 | -16.35 | +19.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.13 | 83.9 | 327 | 59.5% | +0.38 | -12.95 | +30.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.38 | 77.0 | 291 | 52.9% | -0.38 | -19.92 | -6.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.76 | 80.6 | 302 | 54.9% | +0.00 | -16.35 | +5.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.13 | 83.9 | 312 | 56.7% | +0.38 | -12.95 | +15.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.38 | 77.0 | 274 | 49.8% | -0.38 | -19.92 | -23.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.76 | 80.6 | 290 | 52.7% | +0.00 | -16.35 | -7.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.13 | 83.9 | 301 | 54.7% | +0.38 | -12.95 | +4.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.38 | 92.9 | 300 | 54.5% | -0.38 | -3.99 | +3.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.76 | 96.9 | 312 | 56.7% | +0.00 | +0.00 | +15.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.13 | 100.7 | 321 | 58.4% | +0.38 | +3.80 | +24.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.38 | 92.9 | 286 | 52.0% | -0.38 | -3.99 | -11.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.76 | 96.9 | 297 | 54.0% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.13 | 100.7 | 312 | 56.7% | +0.38 | +3.80 | +15.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.38 | 92.9 | 268 | 48.7% | -0.38 | -3.99 | -29.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.76 | 96.9 | 281 | 51.1% | +0.00 | +0.00 | -16.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.13 | 100.7 | 295 | 53.6% | +0.38 | +3.80 | -2.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.38 | 115.8 | 290 | 52.7% | -0.38 | +18.90 | -7.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.76 | 120.5 | 309 | 56.2% | +0.00 | +23.57 | +12.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.13 | 125.5 | 320 | 58.2% | +0.38 | +28.56 | +23.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.38 | 115.8 | 279 | 50.7% | -0.38 | +18.90 | -18.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.76 | 120.5 | 289 | 52.5% | +0.00 | +23.57 | -8.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.13 | 125.5 | 301 | 54.7% | +0.38 | +28.56 | +4.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.38 | 115.8 | 264 | 48.0% | -0.38 | +18.90 | -33.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.76 | 120.5 | 277 | 50.4% | +0.00 | +23.57 | -20.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.13 | 125.5 | 289 | 52.5% | +0.38 | +28.56 | -8.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._