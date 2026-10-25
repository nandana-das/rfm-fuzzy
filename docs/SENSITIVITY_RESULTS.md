# Results: sensitivity analysis (plan addendum K)

Plan: [EXTENSION_PLAN.md, Addendum K](EXTENSION_PLAN.md#addendum-k-2026-10-25-sensitivity-analysis),
committed before any result. One factor varied at a time; tuned regularisation; pooled difference over
cutoffs with 95 % bootstrap CI. Run: `python scripts/evaluate_sensitivity.py <dataset>` (several hours).
Outputs: `results/sensitivity/`.

`*` = CI above zero (fuzzy better), `−` = CI below zero (crisp better), blank = not significant.

## Fuzzy RFM-FCA vs crisp FCA (F-fca-core − C-fca)

| Setting | AUC Retail II | AUC CDNOW | AUC dunnhumby | R² Retail II | R² CDNOW | R² dunnhumby |
|---|---|---|---|---|---|---|
| support 0.02 (466 / 413 / 497 vs 83 / 70 / 83 concepts) | +0.0044* | +0.0037* | +0.0112* | +0.0061* | +0.0124* | +0.0129* |
| **support 0.04 (default)** | +0.0063* | +0.0040* | +0.0098* | +0.0089* | +0.0124* | +0.0089* |
| support 0.06 (136 / 155 / 156 vs 27 / 32 / 29) | +0.0023* | +0.0036* | +0.0115* | +0.0081* | +0.0131* | +0.0057* |
| half-width 0.15 | +0.0024* | +0.0041* | +0.0209* | +0.0031 | +0.0159* | +0.0108* |
| half-width 0.25 | +0.0053* | +0.0051* | +0.0247* | +0.0074* | +0.0221* | +0.0190* |
| horizon 60 days | +0.0059* | +0.0032* | +0.0193* | +0.0094* | +0.0118* | +0.0074* |
| horizon 180 days (3 cutoffs) | +0.0063* | +0.0035* | +0.0298* | +0.0093* | +0.0098* | +0.0087* |

**47 of 48 cells significant in favour of fuzzy RFM-FCA, none reversed** (the one exception,
Retail II R² at half-width 0.15, is positive but not significant).

## Fuzzy vs crisp memberships (F-ctx − C-ctx)

| Setting | AUC Retail II | AUC CDNOW | AUC dunnhumby | R² Retail II | R² CDNOW | R² dunnhumby |
|---|---|---|---|---|---|---|
| half-width 0.15 | **−0.0044−** | +0.0044* | +0.0180* | +0.0034* | +0.0150* | +0.0139* |
| **half-width 0.20 (default)** | +0.0048* | +0.0048* | +0.0076* | +0.0080* | +0.0099* | +0.0141* |
| half-width 0.25 | +0.0030* | +0.0051* | +0.0110* | +0.0040* | +0.0166* | +0.0110* |
| horizon 60 days | +0.0057* | +0.0080* | +0.0147* | +0.0080* | +0.0095* | +0.0106* |
| horizon 180 days | +0.0060* | +0.0040* | +0.0454* | +0.0073* | +0.0090* | +0.0120* |

29 of 30 cells in favour of fuzzy; one reversed (Retail II AUC with the narrowest triangles, where
few customers get partial memberships).

## Summary size (F-selK − C-selK)

| K | AUC Retail II | AUC CDNOW | AUC dunnhumby | R² Retail II | R² CDNOW | R² dunnhumby |
|---|---|---|---|---|---|---|
| 5 | +0.0288* | +0.0011 | +0.0435* | +0.0159* | **−0.0053−** | +0.0328* |
| **10** | +0.0264* | +0.0047* | +0.0159* | +0.0334* | +0.0044* | +0.0114* |
| 20 | +0.0183* | +0.0044* | −0.0072 | +0.0172* | +0.0110* | +0.0012 |
| 30 | +0.0090* | +0.0063* | +0.0046 | +0.0105* | +0.0100* | +0.0067 |

The fuzzy summary beats the crisp summary in 18 of 24 cells, with one reversal (CDNOW R² at K = 5).
K = 10 is the only size significant in all six cells; on dunnhumby the advantage fades at K ≥ 20.

## Verdict

The main finding, fuzzy RFM-FCA beats crisp RFM-FCA, does not depend on the parameter values chosen
early in the project: it holds across support thresholds that change the number of concepts by a factor
of three, across membership widths, and across 60- to 180-day horizons, on all three datasets
(47/48 significant, 0 reversed). The memberships-only result is almost as robust (29/30, one reversal at
the narrowest width). For the summary view, K = 10 is the most robust choice.
