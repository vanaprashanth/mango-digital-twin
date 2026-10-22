# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-10-17
- **Number of days:** 652
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 5.02 mm/day |
| Mean ETc | 3.73 mm/day |
| Mean root-zone depletion | 26.6 mm |
| High-stress days | 69 (10.6%) |
| Medium-stress days | 15 |
| Low-stress days | 568 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.73 | 21.9 | 87 (13.3%) | +18.00 |
| **1.0** | 126 | 63 | 3.73 | 24.5 | 78 (12.0%) | +9.00 |
| **1.2** | 152 | 76 | 3.73 | 26.6 | 69 (10.6%) | +0.00 |
| **1.5** | 190 | 95 | 3.73 | 28.8 | 56 (8.6%) | -13.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 26.6 | 75 (11.5%) | +6.00 |
| **0.50** | 76 | 26.6 | 69 (10.6%) | +0.00 |
| **0.60** | 91 | 26.6 | 61 (9.4%) | -8.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.36 | -0.37 mm/d | 24.4 | 62 (9.5%) | -7.00 |
| **1.00** | 3.73 | +0.00 mm/d | 26.6 | 69 (10.6%) | +0.00 |
| **1.10** | 4.10 | +0.37 mm/d | 28.5 | 75 (11.5%) | +6.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **104** (15.9%)
- Mean ETc: 4.10 mm/day
- Mean depletion: 23.3 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **38** (5.8%)
- Mean ETc: 3.36 mm/day
- Mean depletion: 26.1 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.36 | 20.3 | 87 | 13.3% | -0.37 | -6.23 | +18.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.73 | 21.9 | 96 | 14.7% | +0.00 | -4.70 | +27.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.10 | 23.3 | 104 | 15.9% | +0.37 | -3.22 | +35.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.36 | 20.3 | 82 | 12.6% | -0.37 | -6.23 | +13.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.73 | 21.9 | 87 | 13.3% | +0.00 | -4.70 | +18.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.10 | 23.3 | 97 | 14.9% | +0.37 | -3.22 | +28.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.36 | 20.3 | 74 | 11.3% | -0.37 | -6.23 | +5.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.73 | 21.9 | 82 | 12.6% | +0.00 | -4.70 | +13.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.10 | 23.3 | 89 | 13.7% | +0.37 | -3.22 | +20.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.36 | 22.7 | 78 | 12.0% | -0.37 | -3.89 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.73 | 24.5 | 84 | 12.9% | +0.00 | -2.09 | +15.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.10 | 26.2 | 90 | 13.8% | +0.37 | -0.37 | +21.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.36 | 22.7 | 71 | 10.9% | -0.37 | -3.89 | +2.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.73 | 24.5 | 78 | 12.0% | +0.00 | -2.09 | +9.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.10 | 26.2 | 83 | 12.7% | +0.37 | -0.37 | +14.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.36 | 22.7 | 66 | 10.1% | -0.37 | -3.89 | -3.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.73 | 24.5 | 72 | 11.0% | +0.00 | -2.09 | +3.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.10 | 26.2 | 78 | 12.0% | +0.37 | -0.37 | +9.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.36 | 24.4 | 68 | 10.4% | -0.37 | -2.14 | -1.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.73 | 26.6 | 75 | 11.5% | +0.00 | +0.00 | +6.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.10 | 28.5 | 81 | 12.4% | +0.37 | +1.98 | +12.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.36 | 24.4 | 62 | 9.5% | -0.37 | -2.14 | -7.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.73 | 26.6 | 69 | 10.6% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.10 | 28.5 | 75 | 11.5% | +0.37 | +1.98 | +6.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.36 | 24.4 | 54 | 8.3% | -0.37 | -2.14 | -15.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.73 | 26.6 | 61 | 9.4% | +0.00 | +0.00 | -8.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.10 | 28.5 | 69 | 10.6% | +0.37 | +1.98 | +0.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.36 | 26.1 | 55 | 8.4% | -0.37 | -0.41 | -14.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.73 | 28.8 | 62 | 9.5% | +0.00 | +2.27 | -7.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.10 | 31.2 | 68 | 10.4% | +0.37 | +4.67 | -1.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.36 | 26.1 | 48 | 7.4% | -0.37 | -0.41 | -21.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.73 | 28.8 | 56 | 8.6% | +0.00 | +2.27 | -13.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.10 | 31.2 | 63 | 9.7% | +0.37 | +4.67 | -6.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.36 | 26.1 | 38 | 5.8% | -0.37 | -0.41 | -31.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.73 | 28.8 | 46 | 7.1% | +0.00 | +2.27 | -23.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.10 | 31.2 | 54 | 8.3% | +0.37 | +4.67 | -15.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._