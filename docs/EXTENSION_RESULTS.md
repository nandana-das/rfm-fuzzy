# Results: fuzzy RFM formal concept analysis

Analysis plan: [EXTENSION_PLAN.md](EXTENSION_PLAN.md), committed before any evaluation
code ran. Data: UCI Online Retail II (see [REPLICATION.md](REPLICATION.md)).

## Summary

| Hypothesis | Verdict |
|---|---|
| **H1** fuzzy FCA (Łukasiewicz) predicts better than crisp FCA | **Rejected, opposite direction.** It is significantly *worse* on both targets (AUC −0.048, R² −0.125; Holm p = 0.002), at every origin. The Gödel variant is also worse than crisp FCA |
| H1 secondary: does fuzzifying the context alone help? | **Yes.** The 15 fuzzy memberships beat the 15 crisp quintile indicators at every origin (AUC +0.004, R² +0.008, p = 0.001), and are on par with or better than continuous log-RFM |
| **H2** fuzzy memberships are more robust to small data perturbations | **Supported.** Lower change in all 20 replicates (0.048 vs 0.052 at context level; 0.008 vs 0.013 at concept level) |
| **H3** structure size and stability (descriptive) | Fuzzy lattices are 17–18× larger (3,841 / 3,635 vs 208 concepts). Their frequent-concept sets are slightly *more* stable under bootstrap (Jaccard 0.946 / 0.945 vs 0.932) with far lower variance |

**Bottom line.** Fuzzy memberships help: they predict better and are more robust than
crisp quintile scores. Building a fuzzy concept lattice on top of them, as specified
here, does not help: the lattice blows up, the Łukasiewicz version fills up with
uninformative concepts, and predictions get worse. The value of fuzzification for
RFM-FCA lies in the context, not in the concept lattice.

## H1: prediction (rolling origin, 90-day horizon)

Four origins, 4,266–5,249 customers each, purchase rate 33–43 %. Out-of-fold, 5-fold
CV; rank scale and lattices fitted on training folds only. Means over origins:

| Method | Features | ROC AUC | R² (log spend) |
|---|---|---|---|
| C-ctx: crisp quintile indicators | 15 | 0.7840 | 0.2957 |
| **C-fca: crisp frequent concepts (base paper)** | 49–54 | 0.7806 | 0.2980 |
| F-ctx: fuzzy memberships | 15 | **0.7876** | **0.3037** |
| **F-fca: fuzzy concepts, Łukasiewicz (proposed)** | 2,568–2,647 | 0.7326 | 0.1731 |
| F-fca-G: fuzzy concepts, Gödel | 344–372 | 0.7657 | 0.2694 |
| logRFM: log1p(R, F, M) | 3 | 0.7866 | 0.2928 |

Paired customer bootstrap, pooled over origins (`prediction_comparisons.csv`):

| Comparison | Metric | Difference [95 % CI] | p | Origins A better |
|---|---|---|---|---|
| **F-fca − C-fca (primary)** | AUC | −0.0480 [−0.0533, −0.0420] | 0.002 (Holm) | 0 / 4 |
| **F-fca − C-fca (primary)** | R² | −0.1249 [−0.1379, −0.1123] | 0.002 (Holm) | 0 / 4 |
| F-ctx − C-ctx | AUC | +0.0036 [+0.0019, +0.0052] | 0.001 | 4 / 4 |
| F-ctx − C-ctx | R² | +0.0080 [+0.0046, +0.0113] | 0.001 | 4 / 4 |
| F-fca-G − C-fca | AUC | −0.0149 [−0.0191, −0.0106] | 0.001 | 0 / 4 |
| F-fca-G − C-fca | R² | −0.0286 [−0.0359, −0.0219] | 0.001 | 0 / 4 |
| F-ctx − logRFM | AUC | +0.0010 [−0.0007, +0.0026] | 0.26 | 2 / 4 |
| F-ctx − logRFM | R² | +0.0110 [+0.0065, +0.0159] | 0.001 | 4 / 4 |
| C-fca − C-ctx | AUC | −0.0034 (derived) | — | — |

Notes:
- p = 0.001 is the bootstrap floor (1,000 resamples).
- The crisp lattice adds nothing over the crisp context it is built from (C-fca vs
  C-ctx: −0.003 AUC, +0.002 R²). This holds for the base paper's method too, not just
  for the fuzzy one.
- Per-origin values are in `prediction_per_origin.csv`; the direction of every
  primary and secondary comparison is the same at all four origins.

## H2: robustness to dropping 5 % of invoices (20 replicates)

| Measure | Crisp | Fuzzy (3-level) |
|---|---|---|
| Context change (mean total-variation distance per dimension) | 0.0524 (0.047–0.058) | **0.0479** (0.044–0.054) |
| Customers whose context changes at all | 12.3 % | 19.0 % |
| Concept-degree change, frequent concepts of the full-data lattice | 0.0134 (C-fca) | **0.0081** (Łukasiewicz), 0.0119 (Gödel) |

Fuzzy is lower in **20 / 20** replicates (difference −0.0045, range −0.0081 to −0.0009),
so H2 holds as defined. Its character: under fuzzy memberships *more* customers move
(19 % vs 12 %), but each by a half-step (1 → ½) instead of a full flip between
quintiles, so the total change is smaller. 12 % of customers change crisp RFM cell when
just 5 % of invoices are removed, which is the instability that motivates the extension.

## H3: structure size and stability

| | Crisp | Fuzzy Łukasiewicz | Fuzzy Gödel |
|---|---|---|---|
| Concepts | 208 | 3,841 | 3,635 |
| Frequent concepts (support ≥ 0.04) | 51 | 2,649 | 378 |
| Rules, confidence ≥ 0.60 (along covers) | 17 | 8,714 | 4,727 |
| Mean intent size of frequent concepts | 1.76 | 2.37 | 1.56 |
| Bootstrap Jaccard of frequent-intent sets (50 samples), mean (min) | 0.932 (0.855) | 0.946 (0.934) | 0.945 (0.927) |

74 % of customers have at least one partial (½) membership.

**Why Łukasiewicz fails.** With a ½-intent, the Łukasiewicz residuum gives every customer
degree ≥ ½ (½ → 0 = ½). Its most supported concepts are therefore intents such as
{½/F1, ½/F2, ½/M1, ½/M2}, with support ≈ 0.52 and almost no discriminating power, and
its top rules have confidence 0.9998 between such near-universal concepts. The 0.04
support threshold, taken from the crisp paper, filters nothing out on this scale.

**Gödel is readable.** Its frequent concepts look like the crisp ones plus
boundary-aware variants: {F5, M5} (σ-count 856.5), {R5, F5}, {½/R5, F5, M5} ("frequent
big spenders who are at least partly very recent", 506.5). Its rules with confidence ≥ 0.60
mostly state that customers partly in a term are in practice fully in it, given the
other two terms (e.g. {R5, F5, ½/M5} ⇒ {R5, F5, M5}, 0.96), which is true but adds
little for marketing.

## Exploratory follow-up: is the H1 failure just overfitting?

POST_HOC_PLACEHOLDER

## Deviations from the plan

1. **H2 context metric.** The plan says "L1 change divided by 3 (so 0 = no change,
   1 = every dimension moved fully to other terms)". A full move on one dimension has
   L1 = 2, so the stated meaning needs L1 / 6 (mean total-variation distance per
   dimension). The implementation follows the stated meaning. It scales crisp and fuzzy
   values equally, so the comparison and verdict are unaffected.
2. The tuned-regularisation analysis above was not in the plan and is exploratory.

No other deviations. All planned numbers are reported above or in `results/extension/`.

## Limitations

- One dataset (Online Retail II). The base paper uses only this dataset.
- Only one fuzzification was tested (rank-scale triangles, 3-level chain); a 5-level
  chain was infeasible with the min-closure algorithm used.
- The lattice support threshold and rule definition were carried over from the crisp
  paper. They suit Gödel better than Łukasiewicz; a scale-aware threshold or
  hedges (Bělohlávek & Vychodil) were not tried.
- Predictive value was measured with linear models; interpretability for marketers
  was not measured.

## Reproduce

```bash
python scripts/evaluate_prediction.py           # H1  (~16 min)
python scripts/evaluate_robustness.py           # H2  (~5 min)
python scripts/evaluate_structure.py            # H3  (~25 min)
python scripts/posthoc_tuned_regularization.py  # exploratory
```
