# FAO-56 Model Comparison: Constant-Kc vs Phenology-Aware

A model-to-model comparison of the two FAO-56 soil-water balance prototypes built so far for this project, quantifying how much replacing a constant crop coefficient with a growth-stage-specific one changes estimated crop water demand and water-stress interpretation.

## Input Files

- Constant-Kc FAO-56 output: `/home/runner/work/mango-digital-twin/mango-digital-twin/data/processed/muthukur_fao56_water_balance.csv`
- Phenology-aware FAO-56 output: `/home/runner/work/mango-digital-twin/mango-digital-twin/data/processed/muthukur_fao56_phenology_water_balance.csv`

## Method

The two CSVs above are joined on `date` (inner join — only dates present in both files are compared). The constant-Kc file's single configured Kc value is broadcast to every row as `constant_kc`, alongside the phenology-aware file's per-day `phenology_kc`. Differences are computed as **phenology minus constant** for ETc, root-zone depletion, and Ks, plus a flag for whether the Low/Medium/High water-stress label changed between the two models. Full column-by-column detail is in `muthukur_fao56_model_comparison.csv`.

## Key Findings

- Matched days compared: **558**
- Date range: **2025-01-01** to **2026-07-13**
- Mean ETc difference (phenology - constant): **+0.093 mm/day**
- Mean absolute ETc difference: **0.529 mm/day**
- Largest single-day ETc difference: **+1.328 mm/day** on **2026-04-27**
- Days where the Low/Medium/High water-stress label changed: **6.1%** of matched days

### Biggest single-day ETc swings

| Date | Mango stage | ETc difference (mm/day) | Stress level changed |
|---|---|---|---|
| 2026-04-27 | Fruit development | +1.328 | No |
| 2026-04-15 | Fruit development | +1.268 | No |
| 2026-04-17 | Fruit development | +1.267 | No |
| 2026-04-25 | Fruit development | +1.255 | No |
| 2026-04-26 | Fruit development | +1.253 | No |

## Stage-Wise Comparison

| Mango stage | Days | Avg ETc difference (mm/day) | Days stress level changed |
|---|---|---|---|
| Flower induction / pre-flowering | 92 | -0.285 | 0 |
| Flowering | 92 | +0.000 | 13 |
| Fruit development | 122 | +1.023 | 0 |
| Fruit set | 56 | +0.587 | 0 |
| Maturity / harvest | 61 | +0.259 | 3 |
| Rest / vegetative phase | 135 | -0.707 | 18 |

## Limitations

- This is **not ground-truth validation** yet — it is a model-to-model
  comparison between two prototypes built by this same project.
- The phenology-aware Kc values are first-pass assumptions based on
  general mango/FAO-56 guidance, not locally calibrated for this orchard
  or cultivar.
- No irrigation-event records are included in either model (both are
  rainfed-only depletion balances).
- No field soil-moisture sensor data has been used to validate either
  model's depletion/Ks output.
- No yield validation has been performed.
