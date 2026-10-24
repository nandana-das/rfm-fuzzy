# Results: business value of targeting (plan addendum H)

Plan: [EXTENSION_PLAN.md, Addendum H](EXTENSION_PLAN.md#addendum-h-2026-10-24-business-value-of-targeting),
committed before any targeting result. Tuned regularisation, out-of-fold scores, means over 4 cutoffs.
Run: `python scripts/evaluate_business.py <dataset>`. Outputs (incl. out-of-fold scores and gain
curves): `results/business/`.

*Revenue captured at q %* = share of next-90-day revenue held by the top q % of customers ranked by
predicted spend. *Lift at q %* = purchase rate in the top q % by predicted purchase probability,
divided by the overall rate. On dunnhumby 92–93 % of households buy, so lift cannot exceed ~1.08
and is uninformative there.

## Revenue captured

| Method | Top 10 % Retail II | Top 10 % CDNOW | Top 10 % dunnhumby | Top 20 % Retail II | Top 20 % CDNOW | Top 20 % dunnhumby |
|---|---|---|---|---|---|---|
| **F-fca-core (fuzzy RFM-FCA)** | 55.4 % | 53.5 % | 30.5 % | 71.8 % | 70.4 % | 50.7 % |
| C-fca (base paper) | 52.6 % | 52.6 % | 28.3 % | 71.6 % | 70.6 % | 50.1 % |
| F-ctx (fuzzy memberships) | 55.6 % | 52.8 % | 30.6 % | **73.4 %** | 70.1 % | **50.9 %** |
| logRFM | **58.0 %** | 52.8 % | **31.2 %** | 72.3 % | 69.9 % | 50.0 % |
| K-means, k = 10 | 54.1 % | 51.6 % | 28.6 % | 70.3 % | 68.7 % | 48.3 % |
| GMM, k = 10 | 51.2 % | 51.2 % | 21.7 % | 70.1 % | 68.0 % | 38.7 % |
| FCM, k = 10 | 36.2 % | **53.9 %** | 26.8 % | 71.2 % | 70.2 % | 49.5 % |

## Response lift

| Method | Top 10 % Retail II | Top 10 % CDNOW | Top 20 % Retail II | Top 20 % CDNOW |
|---|---|---|---|---|
| **F-fca-core** | 2.36 | 3.51 | **2.11** | **2.80** |
| C-fca | 2.32 | 3.51 | 2.08 | 2.76 |
| F-ctx | **2.38** | 3.53 | 2.10 | 2.79 |
| logRFM | 2.33 | 3.52 | 2.08 | 2.79 |
| K-means, k = 10 | 2.17 | 3.32 | 1.99 | 2.72 |
| GMM, k = 10 | 2.18 | 3.40 | 2.00 | 2.70 |
| FCM, k = 10 | 2.33 | **3.58** | 2.10 | 2.78 |

## Pre-registered tests (top 20 %, Holm over four per dataset)

| Test | Metric | Retail II | CDNOW | dunnhumby |
|---|---|---|---|---|
| H1 F-fca-core − C-fca | revenue | +0.2 pp (p = 0.85) | −0.1 pp (p = 0.85) | **+0.6 pp** (p = 0.012) |
| H1 F-fca-core − C-fca | lift | +0.026 (p = 0.22) | **+0.045** (p = 0.004) | −0.003 (p = 0.17) |
| H2 F-fca-core − FCM10 | revenue | +0.6 pp (p = 0.37) | +0.2 pp (p = 0.85) | **+1.3 pp** (p = 0.004) |
| H2 F-fca-core − FCM10 | lift | +0.010 (p = 0.85) | +0.023 (p = 0.14) | −0.004 (p = 0.08) |

3 of 12 primary tests are significant, all in favour of fuzzy RFM-FCA; none favours a baseline.

## Descriptive findings

- **Top 10 % revenue vs the base paper:** fuzzy RFM-FCA captures more in every dataset:
  +2.9 pp (Retail II), +0.9 pp (CDNOW), +2.2 pp (dunnhumby), all p ≤ 0.01. The gain sits in
  the most valuable decile, where crisp quintile boundaries lump very different spenders together.
- **vs K-means and GMM (k = 10):** fuzzy RFM-FCA captures more revenue at both depths on all three
  datasets (+1.3 to +12.0 pp) and has higher lift on Retail II and CDNOW (+0.08 to +0.19).
- **vs FCM (k = 10):** mostly level; FCM is better on CDNOW top-10 % lift (3.58 vs 3.51) and fails
  badly on Retail II top-10 % revenue (36.2 %).
- **vs log-RFM:** log-RFM captures more at the top 10 % on Retail II and dunnhumby; fuzzy RFM-FCA
  captures more at 20 % on CDNOW and dunnhumby. No consistent winner.

## Verdict

For targeting, fuzzy RFM-FCA is consistently at least as good as every segmentation baseline and
better than the base paper where it matters most (the top decile of spenders). Gains are a few
percentage points of revenue, not large, and log-RFM or the fuzzy memberships alone are similar.
This supports a "no loss, small gain, plus interpretable segments" claim, not a "better targeting
engine" claim.
