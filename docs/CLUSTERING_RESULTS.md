# Results: clustering baselines (plan addendum F)

Plan: [EXTENSION_PLAN.md, Addendum F](EXTENSION_PLAN.md#addendum-f-2026-10-24-clustering-baselines-k-means-gmm-fuzzy-c-means),
committed before any baseline result. Fuzzy RFM-FCA (F-fca-core) unchanged. Tuned regularisation.
Run: `python scripts/evaluate_clustering.py <dataset>`. Outputs: `results/clustering/`.

**Implementation note.** Fuzzy C-means is seeded with k-means++ centres; random initial
memberships collapsed all centres to the mean in the unit test. Fixed before any result.

**Chosen k.** The silhouette rule (base paper's criterion) picked **k = 2 in all 60 training
folds** on all three datasets, giving very coarse baselines. The pre-specified k = 10 variants
are therefore the fairer comparison and are reported next to the primary ones.

## Prediction (means over 4 cutoffs)

| Method | AUC Retail II | AUC CDNOW | AUC dunnhumby | R² Retail II | R² CDNOW | R² dunnhumby |
|---|---|---|---|---|---|---|
| **F-fca-core (fuzzy RFM-FCA)** | 0.7861 | 0.7878 | 0.8651 | **0.3082** | 0.2348 | 0.5167 |
| C-fca (base paper) | 0.7799 | 0.7839 | 0.8552 | 0.2993 | 0.2223 | 0.5078 |
| F-ctx (fuzzy memberships) | **0.7870** | **0.7885** | 0.8767 | 0.3038 | 0.2193 | **0.5249** |
| logRFM | 0.7864 | 0.7884 | **0.8872** | 0.2927 | **0.2407** | 0.5169 |
| K-means, k = 2 | 0.7013 | 0.7214 | 0.6838 | 0.1914 | 0.1612 | 0.3664 |
| GMM, k = 2 | 0.6897 | 0.7125 | 0.7433 | 0.1361 | 0.1090 | 0.4197 |
| FCM, k = 2 | 0.7520 | 0.7695 | 0.6841 | 0.2235 | 0.1765 | 0.4185 |
| K-means, k = 10 | 0.7641 | 0.7768 | 0.8279 | 0.2893 | 0.2364 | 0.4980 |
| GMM, k = 10 | 0.7698 | 0.7776 | 0.8752 | 0.2595 | 0.2323 | 0.4532 |
| FCM, k = 10 | 0.7832 | 0.7858 | 0.8599 | 0.2902 | 0.2394 | 0.5109 |

### Pre-registered tests (silhouette k; Holm over six per dataset)

F-fca-core beats FCM (F1), K-means (F2) and GMM (F3) on both metrics on all three datasets,
at every cutoff, Holm p = 0.006 (the floor). Differences range from +0.018 AUC (vs FCM, CDNOW)
to +0.181 AUC (vs FCM and K-means, dunnhumby). With k = 2 this mostly shows that two clusters
are too coarse.

### Against k = 10 (descriptive)

| F-fca-core minus | AUC Retail II | AUC CDNOW | AUC dunnhumby | R² Retail II | R² CDNOW | R² dunnhumby |
|---|---|---|---|---|---|---|
| K-means, k = 10 | **+0.022** | **+0.011** | **+0.037** | **+0.019** | −0.002 (p = 0.35) | **+0.019** |
| GMM, k = 10 | **+0.016** | **+0.010** | **−0.010** | **+0.049** | +0.002 (p = 0.22) | **+0.063** |
| FCM, k = 10 | **+0.003** | **+0.002** | +0.005 (p = 0.27) | **+0.018** | **−0.005** | +0.006 (p = 0.05) |

Bold = significant at p < 0.05 (uncorrected). Against the strongest baseline, FCM with k = 10,
fuzzy RFM-FCA is slightly better on Online Retail II, mixed on CDNOW (better AUC, worse R²) and
not significantly different on dunnhumby.

## Structure agreement (pair-similarity correlation; 1 = identical)

| Method | Robust. Retail II | Robust. CDNOW | Robust. dunnhumby | Stab. Retail II | Stab. CDNOW | Stab. dunnhumby |
|---|---|---|---|---|---|---|
| C-fca | 0.886 | 0.936 | 0.928 | 0.957 | 0.987 | 0.936 |
| **F-fca-core** | 0.958 | 0.955 | 0.948 | 0.986 | 0.993 | 0.972 |
| K-means, k = 2 | 0.932 | 0.941 | 0.945 | 0.980 | 0.993 | 0.937 |
| GMM, k = 2 | 0.956 | 0.949 | 0.992 | 0.961 | 1.000 | 0.981 |
| FCM, k = 2 | **0.973** | **0.977** | **0.991** | **1.000** | **1.000** | **0.998** |

- Fuzzy RFM-FCA is clearly more robust and stable than the base paper's crisp lattice
  (robustness higher in 20/20 replicates on all three datasets; stability in 20, 19, 17 of 20).
- It is more robust than K-means (20, 20, 13 of 20 replicates).
- Fuzzy C-means is the most robust and stable everywhere, but these baselines have only two
  clusters, and a two-cluster structure is almost trivially stable. Structure was not measured
  at k = 10 (not in the plan), so this comparison is not like for like.

## Structure agreement against k = 10 clustering (Addendum G)

Same design, baselines with k = 10 (`results/clustering/<dataset>_structure_agreement_k10.csv`).
Mean (minimum) over 20 replicates:

| Method | Robust. Retail II | Robust. CDNOW | Robust. dunnhumby | Stab. Retail II | Stab. CDNOW | Stab. dunnhumby |
|---|---|---|---|---|---|---|
| C-fca | 0.886 (0.874) | 0.936 (0.929) | 0.928 (0.906) | 0.957 (0.922) | 0.987 (0.953) | 0.936 (0.867) |
| **F-fca-core** | **0.958** (0.948) | **0.955** (0.952) | **0.948** (0.939) | **0.986** (0.978) | **0.993** (0.924) | **0.972** (0.942) |
| K-means, k = 10 | 0.760 (0.549) | 0.907 (0.807) | 0.650 (0.546) | 0.683 (0.508) | 0.937 (0.804) | 0.692 (0.498) |
| GMM, k = 10 | 0.858 (0.731) | 0.816 (0.795) | 0.878 (0.793) | 0.818 (0.701) | 0.904 (0.845) | 0.843 (0.583) |
| FCM, k = 10 | 0.913 (0.894) | 0.929 (0.849) | 0.942 (0.815) | 0.944 (0.910) | 0.966 (0.890) | 0.914 (0.825) |

Replicates in which F-fca-core is higher (of 20):

| Baseline | Robust. Retail II | Robust. CDNOW | Robust. dunnhumby | Stab. Retail II | Stab. CDNOW | Stab. dunnhumby |
|---|---|---|---|---|---|---|
| K-means, k = 10 | 20 | 20 | 20 | 20 | 19 | 20 |
| GMM, k = 10 | 20 | 20 | 20 | 20 | 19 | 20 |
| FCM, k = 10 | 20 | 15 | 8 | 16 | 9 | 17 |

- At a comparable granularity, fuzzy RFM-FCA has the **highest mean robustness and stability
  on all three datasets**, and the best or near-best worst case.
- It beats K-means and GMM in essentially every replicate.
- Against FCM the margin is smaller: clearly ahead on Online Retail II, and in the other
  cells FCM wins some replicates (dunnhumby robustness: 8 of 20, where FCM's mean is pulled
  down by occasional bad fits, min 0.815). Fuzzy RFM-FCA is the more *consistent* of the two:
  its minima are higher in all six cells.

## Verdict

- **Against the base paper's crisp FCA:** fuzzy RFM-FCA is better on prediction, robustness and
  stability, on all three datasets.
- **Against standard clustering at the base paper's k selection:** fuzzy RFM-FCA predicts far
  better; clustering with two segments is too coarse.
- **Against well-sized clustering (k = 10):** fuzzy RFM-FCA beats K-means and mostly GMM, and is
  roughly on par with fuzzy C-means (small gains on Online Retail II, mixed on CDNOW, a tie on
  dunnhumby). Its advantage over FCM is therefore not predictive power; it is that its segments
  come with explicit intents and rules (e.g. {R5, ½F5, M5}), which FCM clusters do not.
- **Structure at k = 10 (Addendum G):** fuzzy RFM-FCA is the most robust and stable method on
  average on all three datasets, far ahead of K-means and GMM and slightly ahead of FCM, with
  more consistent worst cases.
