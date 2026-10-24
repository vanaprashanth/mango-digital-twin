# FAO-56 Sensitivity Analysis — Summary

> **Disclaimer:** All FAO-56 parameters in this project are assumption-based, not field-calibrated to this specific orchard or cultivar. This sensitivity analysis shows how output metrics change when those assumptions are varied — it does not identify which scenario is 'correct'. Use it to understand the uncertainty band around the baseline estimates.

---

## Overview

- **Date range analysed:** 2025-01-01 - 2026-10-19
- **Number of days:** 657
- **Parameter grid:** 4 root-depth × 3 depletion-fraction × 3 Kc-multiplier = **36 scenarios**

### Baseline scenario

| Parameter | Baseline value |
|---|---|
| Root depth | 1.2 m |
| Depletion fraction *p* | 0.50 |
| Kc multiplier | 1.00 |
| TAW | 151.7 mm |
| RAW | 75.8 mm |
| Mean ET0 | 5.01 mm/day |
| Mean ETc | 3.72 mm/day |
| Mean root-zone depletion | 26.4 mm |
| High-stress days | 69 (10.5%) |
| Medium-stress days | 15 |
| Low-stress days | 573 |

---

## Sensitivity to root depth

_Depletion fraction p and Kc multiplier held at baseline._

| Root depth (m) | TAW (mm) | RAW (mm) | Mean ETc (mm/d) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|---|
| **0.8** | 101 | 51 | 3.72 | 21.7 | 87 (13.2%) | +18.00 |
| **1.0** | 126 | 63 | 3.72 | 24.3 | 78 (11.9%) | +9.00 |
| **1.2** | 152 | 76 | 3.72 | 26.4 | 69 (10.5%) | +0.00 |
| **1.5** | 190 | 95 | 3.72 | 28.6 | 56 (8.5%) | -13.00 |

_Interpretation: larger root depth → higher TAW → soil holds more water → fewer High-stress days, but root depth is an assumption for this prototype and has not been measured at the study site._

---

## Sensitivity to depletion fraction *p*

_Root depth and Kc multiplier held at baseline._

| Depletion fraction *p* | RAW (mm) | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|
| **0.40** | 61 | 26.4 | 75 (11.4%) | +6.00 |
| **0.50** | 76 | 26.4 | 69 (10.5%) | +0.00 |
| **0.60** | 91 | 26.4 | 61 (9.3%) | -8.00 |

_Interpretation: higher p → higher RAW → stress threshold is harder to reach → fewer High-stress days.  FAO-56 Table 22 gives p ≈ 0.50 for fruit trees, but the true value for this orchard is unknown._

---

## Sensitivity to Kc multiplier

_Root depth and depletion fraction held at baseline._

| Kc multiplier | Mean ETc (mm/d) | Δ Mean ETc | Mean depletion (mm) | High-stress days | Δ High-stress days |
|---|---|---|---|---|---|
| **0.90** | 3.35 | -0.37 mm/d | 24.2 | 62 (9.4%) | -7.00 |
| **1.00** | 3.72 | +0.00 mm/d | 26.4 | 69 (10.5%) | +0.00 |
| **1.10** | 4.09 | +0.37 mm/d | 28.3 | 75 (11.4%) | +6.00 |

_Interpretation: higher Kc → higher ETc → faster depletion → more High-stress days.  A ±10% Kc uncertainty band is a rough proxy for the calibration uncertainty of the stage Kc values in this prototype._

---

## Most and least conservative scenarios

### Worst case (most High-stress days)

- Root depth: 0.8 m  |  p: 0.40  |  Kc ×1.10
- High-stress days: **104** (15.8%)
- Mean ETc: 4.09 mm/day
- Mean depletion: 23.2 mm

### Best case (fewest High-stress days)

- Root depth: 1.5 m  |  p: 0.60  |  Kc ×0.90
- High-stress days: **38** (5.8%)
- Mean ETc: 3.35 mm/day
- Mean depletion: 26.0 mm

---

## Full scenario table

| Scenario | Root (m) | *p* | Kc× | Baseline? | Mean ETc | Mean Dep. | High days | % High | Δ ETc | Δ Dep. | Δ High |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.8 | 0.40 | 0.90 |  | 3.35 | 20.2 | 87 | 13.2% | -0.37 | -6.19 | +18.00 |
| 2 | 0.8 | 0.40 | 1.00 |  | 3.72 | 21.7 | 96 | 14.6% | +0.00 | -4.66 | +27.00 |
| 3 | 0.8 | 0.40 | 1.10 |  | 4.09 | 23.2 | 104 | 15.8% | +0.37 | -3.20 | +35.00 |
| 4 | 0.8 | 0.50 | 0.90 |  | 3.35 | 20.2 | 82 | 12.5% | -0.37 | -6.19 | +13.00 |
| 5 | 0.8 | 0.50 | 1.00 |  | 3.72 | 21.7 | 87 | 13.2% | +0.00 | -4.66 | +18.00 |
| 6 | 0.8 | 0.50 | 1.10 |  | 4.09 | 23.2 | 97 | 14.8% | +0.37 | -3.20 | +28.00 |
| 7 | 0.8 | 0.60 | 0.90 |  | 3.35 | 20.2 | 74 | 11.3% | -0.37 | -6.19 | +5.00 |
| 8 | 0.8 | 0.60 | 1.00 |  | 3.72 | 21.7 | 82 | 12.5% | +0.00 | -4.66 | +13.00 |
| 9 | 0.8 | 0.60 | 1.10 |  | 4.09 | 23.2 | 89 | 13.6% | +0.37 | -3.20 | +20.00 |
| 10 | 1.0 | 0.40 | 0.90 |  | 3.35 | 22.5 | 78 | 11.9% | -0.37 | -3.87 | +9.00 |
| 11 | 1.0 | 0.40 | 1.00 |  | 3.72 | 24.3 | 84 | 12.8% | +0.00 | -2.07 | +15.00 |
| 12 | 1.0 | 0.40 | 1.10 |  | 4.09 | 26.0 | 90 | 13.7% | +0.37 | -0.37 | +21.00 |
| 13 | 1.0 | 0.50 | 0.90 |  | 3.35 | 22.5 | 71 | 10.8% | -0.37 | -3.87 | +2.00 |
| 14 | 1.0 | 0.50 | 1.00 |  | 3.72 | 24.3 | 78 | 11.9% | +0.00 | -2.07 | +9.00 |
| 15 | 1.0 | 0.50 | 1.10 |  | 4.09 | 26.0 | 83 | 12.6% | +0.37 | -0.37 | +14.00 |
| 16 | 1.0 | 0.60 | 0.90 |  | 3.35 | 22.5 | 66 | 10.1% | -0.37 | -3.87 | -3.00 |
| 17 | 1.0 | 0.60 | 1.00 |  | 3.72 | 24.3 | 72 | 11.0% | +0.00 | -2.07 | +3.00 |
| 18 | 1.0 | 0.60 | 1.10 |  | 4.09 | 26.0 | 78 | 11.9% | +0.37 | -0.37 | +9.00 |
| 19 | 1.2 | 0.40 | 0.90 |  | 3.35 | 24.2 | 68 | 10.3% | -0.37 | -2.12 | -1.00 |
| 20 | 1.2 | 0.40 | 1.00 |  | 3.72 | 26.4 | 75 | 11.4% | +0.00 | +0.00 | +6.00 |
| 21 | 1.2 | 0.40 | 1.10 |  | 4.09 | 28.3 | 81 | 12.3% | +0.37 | +1.96 | +12.00 |
| 22 | 1.2 | 0.50 | 0.90 |  | 3.35 | 24.2 | 62 | 9.4% | -0.37 | -2.12 | -7.00 |
| 23 | 1.2 | 0.50 | 1.00 | ✓ | 3.72 | 26.4 | 69 | 10.5% | +0.00 | +0.00 | +0.00 |
| 24 | 1.2 | 0.50 | 1.10 |  | 4.09 | 28.3 | 75 | 11.4% | +0.37 | +1.96 | +6.00 |
| 25 | 1.2 | 0.60 | 0.90 |  | 3.35 | 24.2 | 54 | 8.2% | -0.37 | -2.12 | -15.00 |
| 26 | 1.2 | 0.60 | 1.00 |  | 3.72 | 26.4 | 61 | 9.3% | +0.00 | +0.00 | -8.00 |
| 27 | 1.2 | 0.60 | 1.10 |  | 4.09 | 28.3 | 69 | 10.5% | +0.37 | +1.96 | +0.00 |
| 28 | 1.5 | 0.40 | 0.90 |  | 3.35 | 26.0 | 55 | 8.4% | -0.37 | -0.41 | -14.00 |
| 29 | 1.5 | 0.40 | 1.00 |  | 3.72 | 28.6 | 62 | 9.4% | +0.00 | +2.25 | -7.00 |
| 30 | 1.5 | 0.40 | 1.10 |  | 4.09 | 31.0 | 68 | 10.3% | +0.37 | +4.64 | -1.00 |
| 31 | 1.5 | 0.50 | 0.90 |  | 3.35 | 26.0 | 48 | 7.3% | -0.37 | -0.41 | -21.00 |
| 32 | 1.5 | 0.50 | 1.00 |  | 3.72 | 28.6 | 56 | 8.5% | +0.00 | +2.25 | -13.00 |
| 33 | 1.5 | 0.50 | 1.10 |  | 4.09 | 31.0 | 63 | 9.6% | +0.37 | +4.64 | -6.00 |
| 34 | 1.5 | 0.60 | 0.90 |  | 3.35 | 26.0 | 38 | 5.8% | -0.37 | -0.41 | -31.00 |
| 35 | 1.5 | 0.60 | 1.00 |  | 3.72 | 28.6 | 46 | 7.0% | +0.00 | +2.25 | -23.00 |
| 36 | 1.5 | 0.60 | 1.10 |  | 4.09 | 31.0 | 54 | 8.2% | +0.37 | +4.64 | -15.00 |

---

## Limitations and next steps

- All parameters varied here are assumed, not measured at this orchard.
- The water balance is rainfed-only — no irrigation events are tracked.
- Soil texture parameters (for TAW/RAW) come from SoilGrids estimates,   not measured profiles; this is a separate source of uncertainty not   explored in this analysis.
- ET0 is the same across all scenarios (it does not depend on Kc, root   depth, or p), so ET0 sensitivity is not analysed here.
- Suggested next steps: field measurement of root depth and soil-moisture   profiles; local agronomic literature on mango Kc for the Andhra Pradesh   region; cross-validation of stress periods against visible crop stress   indicators in the field.

_Generated by src/validation/fao56_sensitivity_analysis.py._