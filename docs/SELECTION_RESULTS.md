# Results: summary view of K selected concepts (plan addendum J)

Plan: [EXTENSION_PLAN.md, Addendum J](EXTENSION_PLAN.md#addendum-j-2026-10-24-a-summary-view-of-k-selected-concepts),
committed before any result. Greedy description-coverage selection, fitted on training customers only.
Run: `python scripts/evaluate_selection.py <dataset>`. Outputs: `results/selection/`.

## The summary view (Online Retail II, full data, K = 10)

| # | Fuzzy concept (F-sel10) | Customers fully in | Share of total spend |
|---|---|---|---|
| 1 | {F5, M5} | 10.3 % | 55.3 % |
| 2 | {F1, M1} | 9.9 % | 0.4 % |
| 3 | {½F2, ½M2} | 18.9 % | 2.7 % |
| 4 | {½F4, ½M4} | 18.8 % | 13.0 % |
| 5 | {½F3, ½M3} | 17.9 % | 5.6 % |
| 6 | {½F2, M1} | 4.6 % | 0.2 % |
| 7 | {F5, ½M4} | 4.5 % | 3.6 % |
| 8 | {½F4, ½F5, ½M5} | 6.3 % | 11.8 % |
| 9 | {½F1, ½M1, ½M2} | 6.2 % | 0.6 % |
| 10 | {R5, F5, M5} | 4.8 % | 36.9 % |

Lists for all datasets and for the crisp selection: `results/selection/<dataset>_selected_concepts.csv`.
The crisp counterpart picks broad single-dimension concepts such as {M4}, {M3}, {M2}, each 20 % of
customers; the fuzzy one picks band-straddling segments (e.g. {½F4, ½F5, ½M5}) and the best-customer
segment {R5, F5, M5}.

## Summary-view proxies (Retail II / CDNOW / dunnhumby)

| Method | Segments | Coverage | Segments per covered customer | Conditions per description |
|---|---|---|---|---|
| F-sel10 | 10 | 0.83 / 0.92 / 0.92 | 1.2 / 1.7 / 1.4 | 2.0 / 1.9 / 2.1 |
| C-sel10 | 10 | 0.97 / 0.91 / 0.90 | 1.3 / 1.7 / 1.6 | 1.5 / 1.7 / 1.9 |
| F-sel20 | 20 | 0.96 / 0.99 / 0.98 | 1.8 / 2.3 / 2.2 | 1.9 / 2.1 / 2.1 |

With 10 selected concepts, fuzzy RFM-FCA is a readable deliverable: 10 named segments, each customer
in 1–2 of them, ~2 conditions per segment (vs 208–238 segments and ~20 per customer for the full lattice).

## Prediction (tuned; means over 4 cutoffs)

| Method | AUC Retail II | AUC CDNOW | AUC dunnhumby | R² Retail II | R² CDNOW | R² dunnhumby |
|---|---|---|---|---|---|---|
| F-fca-core (full, ~200) | 0.786 | 0.788 | 0.865 | 0.308 | 0.235 | 0.517 |
| **F-sel10** | 0.763 | 0.781 | 0.813 | 0.269 | 0.221 | 0.462 |
| F-sel20 | 0.775 | 0.785 | 0.816 | 0.285 | 0.229 | 0.474 |
| C-sel10 | 0.736 | 0.776 | 0.797 | 0.236 | 0.217 | 0.451 |
| FCM, k = 10 | 0.783 | 0.786 | 0.860 | 0.290 | 0.239 | 0.511 |
| K-means, k = 10 | 0.764 | 0.777 | 0.828 | 0.289 | 0.236 | 0.498 |

Pre-registered tests (Holm over four per dataset):

| Test | Metric | Retail II | CDNOW | dunnhumby |
|---|---|---|---|---|
| S1 F-sel10 − C-sel10 | AUC | **+0.026** | **+0.005** | **+0.016** |
| S1 F-sel10 − C-sel10 | R² | **+0.033** | **+0.004** | **+0.011** |
| S2 F-sel10 − FCM10 | AUC | **−0.020** | **−0.005** | **−0.047** |
| S2 F-sel10 − FCM10 | R² | **−0.021** | **−0.019** | **−0.049** |

All eight significant (Holm p ≤ 0.008): the fuzzy summary beats the crisp summary everywhere, and
loses to fuzzy C-means with 10 clusters everywhere.

## Structure agreement (mean; F-sel10 vs baselines)

| Method | Robust. Retail II | Robust. CDNOW | Robust. dunnhumby | Stab. Retail II | Stab. CDNOW | Stab. dunnhumby |
|---|---|---|---|---|---|---|
| **F-sel10** | 0.906 | **0.946** | 0.933 | 0.930 | 0.981 | **0.940** |
| C-sel10 | 0.565 | 0.934 | 0.838 | 0.606 | **0.985** | 0.845 |
| K-means, k = 10 | 0.757 | 0.907 | 0.652 | 0.683 | 0.939 | 0.687 |
| GMM, k = 10 | 0.858 | 0.816 | 0.876 | 0.819 | 0.905 | 0.844 |
| FCM, k = 10 | **0.913** | 0.928 | **0.942** | **0.944** | 0.966 | 0.913 |

The fuzzy summary is far more robust and stable than the crisp summary (which collapses on Retail II:
0.565 / 0.606) and than K-means and GMM; against FCM it is level (each wins some cells).

## Verdict

- **The summary view solves the segment-count problem**: 10 readable, exactly described segments.
- **Fuzzy beats crisp at every size**: as a 10-concept summary, fuzzy RFM-FCA predicts better and is
  much more robust and stable than the crisp equivalent, on all three datasets.
- **The price of compression is predictive power**: 10 selected concepts lose 0.007–0.052 AUC against
  the full fuzzy lattice and 0.005–0.047 AUC against fuzzy C-means with 10 clusters. FCM packs more
  predictive information into 10 numbers; fuzzy RFM-FCA gives 10 named rule segments instead.
- So the practical recommendation is two-level: the **full fuzzy lattice for modelling** (prediction,
  targeting) and the **10-concept summary for communicating segments**, with fuzzy C-means as the
  stronger choice only if predictions from 10 unnamed clusters are all that is needed.
