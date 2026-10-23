# Results: hybrid of segment features and log-RFM (plan addendum E)

**Exploratory.** Designed after all three datasets had been analysed; plan committed before
any hybrid result. Tuned regularisation only. Run: `python scripts/evaluate_hybrid.py <dataset>`.
Outputs: `results/hybrid/`.

Hybrid = segment features + log1p(R, F, M) in one model: `HYB-fca` (fuzzy concepts),
`HYB-ctx` (fuzzy memberships), `HYB-cfca` (base-paper crisp concepts).

## Means over 4 cutoffs

| Method | AUC Retail II | AUC CDNOW | AUC dunnhumby | R² Retail II | R² CDNOW | R² dunnhumby |
|---|---|---|---|---|---|---|
| logRFM | 0.7864 | 0.7884 | 0.8872 | 0.2927 | 0.2407 | 0.5169 |
| F-fca-core | 0.7861 | 0.7878 | 0.8651 | 0.3082 | 0.2348 | 0.5167 |
| HYB-cfca (crisp concepts + logRFM) | 0.7829 | 0.7887 | 0.8725 | 0.3117 | 0.2549 | 0.5258 |
| HYB-ctx (fuzzy memberships + logRFM) | **0.7874** | **0.7900** | **0.8897** | **0.3124** | 0.2534 | **0.5352** |
| HYB-fca (fuzzy concepts + logRFM) | 0.7868 | **0.7900** | 0.8714 | **0.3124** | **0.2554** | 0.5213 |

## Tests (Holm over six per dataset)

| Test | Metric | Retail II | CDNOW | dunnhumby |
|---|---|---|---|---|
| E1 HYB-fca − logRFM | AUC | +0.0004 (p = 1.0) | +0.0017 (p = 0.06) | **−0.0158** (p = 0.006) |
| E1 HYB-fca − logRFM | R² | **+0.0197** (p = 0.006) | **+0.0147** (p = 0.006) | +0.0044 (p = 0.42) |
| E2 HYB-fca − HYB-cfca | AUC | **+0.0039** (p = 0.01) | +0.0014 (p = 0.10) | −0.0012 (p = 0.76) |
| E2 HYB-fca − HYB-cfca | R² | +0.0007 (p = 1.0) | +0.0004 (p = 1.0) | −0.0045 (p = 0.29) |
| E3 HYB-fca − HYB-ctx | AUC | −0.0007 (p = 1.0) | +0.0000 (p = 1.0) | **−0.0183** (p = 0.006) |
| E3 HYB-fca − HYB-ctx | R² | −0.0000 (p = 1.0) | **+0.0019** (p = 0.03) | **−0.0139** (p = 0.006) |

## Reading

- **Segment features do add to exact RFM for spend.** Adding fuzzy concepts to log-RFM raises
  spend R² by 0.020 (Online Retail II) and 0.015 (CDNOW), significantly and at every cutoff;
  on dunnhumby +0.004, not significant. Purchase AUC does not improve.
- **The best predictor overall is a hybrid**, but usually the simpler one: fuzzy memberships
  + log-RFM (HYB-ctx) is best or tied-best in 5 of 6 dataset-metric cells. The fuzzy lattice
  hybrid ties it on Online Retail II and CDNOW and is clearly worse on dunnhumby.
- **Fuzzy vs crisp concepts inside the hybrid:** no consistent difference (one significant
  AUC gain on Online Retail II, otherwise not significant).
- So for prediction, fuzzy memberships beside the exact RFM values are the practical choice;
  the fuzzy lattice's value remains interpretability, not extra predictive signal.
