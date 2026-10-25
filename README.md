# rfm-fuzzy

Fuzzy formal concept analysis for RFM customer segmentation, extending
Rungruang et al., *RFM model customer segmentation based on hierarchical approach using FCA*,
Expert Systems with Applications 237 (2024) 121449.

The base paper scores customers into recency, frequency and monetary quintiles, turns the
scores into a binary formal context (R1..R5, F1..F5, M1..M5), and reads segments and
association rules off the concept lattice. Its stated future work is a **non-binary (fuzzy)
formal context**; this repository builds it, evaluates it out of sample on three retail
datasets, and compares it with crisp RFM-FCA, log-RFM and clustering baselines.

## Main results

- **Replication:** the base paper's 208 concepts and all 18 published rules are reproduced on
  Online Retail II (concept sizes within 0.8 customers on average).
- **Fuzzy RFM-FCA beats crisp RFM-FCA** on purchase AUC and spend R² on all three datasets
  (+0.004 to +0.010 AUC, +0.009 to +0.012 R²), and in **47 of 48** sensitivity settings (none worse).
- **Targeting:** it reaches 0.9–2.9 percentage points more next-quarter revenue in the top
  customer decile than crisp RFM-FCA.
- **Robustness and stability:** the highest of all methods compared (crisp FCA, K-means,
  Gaussian mixture, fuzzy C-means at k = 10).
- **Interpretability:** segments are exactly described by short rules (fidelity 1.0 vs 0.53–0.80
  for clusters); a greedy 10-concept summary makes them readable for marketers.
- **Limits:** not a better predictor than log-RFM; roughly level with fuzzy C-means; the full
  fuzzy lattice has about four times as many segments as the crisp one.

## Method

```
Transactions -> R, F, M per customer at a cutoff
  -> mid-rank percentiles (fitted on training customers)
  -> 5 triangular fuzzy terms per dimension, degrees in {0, 1/2, 1}
  -> Belohlavek fuzzy concept lattice (Lukasiewicz; Goedel as a check)
  -> segments = concepts with core support >= 0.04 (share of customers fully in the concept)
  -> optional 10-concept summary (greedy, (1 - 1/e) guarantee)
```

Crisp RFM-FCA is the special case with degrees {0, 1}. Theoretical properties are checked
numerically in `tests/test_theory.py`.

## Analyses

Every analysis was run under a plan committed before it ran: [docs/EXTENSION_PLAN.md](docs/EXTENSION_PLAN.md)
(main plan and addenda A–K).

| Analysis | Plan | Results | Script |
|---|---|---|---|
| Replication of the base paper | — | [REPLICATION.md](docs/REPLICATION.md) | `replicate_base_paper.py`, `compare_with_paper.py` |
| Fuzzy vs crisp, Online Retail II (H1–H3) | main plan | [EXTENSION_RESULTS.md](docs/EXTENSION_RESULTS.md) | `evaluate_prediction.py`, `evaluate_robustness.py`, `evaluate_structure.py`, `posthoc_tuned_regularization.py` |
| Core-support threshold | A | [EXTENSION_RESULTS.md](docs/EXTENSION_RESULTS.md) | `evaluate_core_support.py` |
| CDNOW confirmation (7/7 claims) | B | [CDNOW_RESULTS.md](docs/CDNOW_RESULTS.md) | `confirm_cdnow.py` |
| Tie-aware memberships (exploratory) | C | [TIE_AWARE_RESULTS.md](docs/TIE_AWARE_RESULTS.md) | `evaluate_tie_aware.py` |
| dunnhumby confirmation (4/7 claims) | D | [DUNNHUMBY_RESULTS.md](docs/DUNNHUMBY_RESULTS.md) | `confirm_dunnhumby.py` |
| Hybrid with log-RFM (exploratory) | E | [HYBRID_RESULTS.md](docs/HYBRID_RESULTS.md) | `evaluate_hybrid.py` |
| K-means, GMM, fuzzy C-means baselines | F, G | [CLUSTERING_RESULTS.md](docs/CLUSTERING_RESULTS.md) | `evaluate_clustering.py` |
| Targeting value | H | [BUSINESS_RESULTS.md](docs/BUSINESS_RESULTS.md) | `evaluate_business.py` |
| Interpretability proxies | I | [INTERPRETABILITY_RESULTS.md](docs/INTERPRETABILITY_RESULTS.md) | `evaluate_interpretability.py` |
| 10-concept summary view | J | [SELECTION_RESULTS.md](docs/SELECTION_RESULTS.md) | `evaluate_selection.py` |
| Sensitivity analysis | K | [SENSITIVITY_RESULTS.md](docs/SENSITIVITY_RESULTS.md) | `evaluate_sensitivity.py` |

Scripts taking a dataset argument use `retail`, `cdnow` or `dunnhumby`
(e.g. `python scripts/evaluate_clustering.py cdnow`).

## Layout

```
rfmfca/    library: data loaders, RFM scoring, crisp and fuzzy concept lattices,
           concept selection, clustering baselines, evaluation and bootstrap
scripts/   one script per analysis (table above), plus fetch_data.py
results/   result tables per analysis (CSV), committed
docs/      analysis plans and result write-ups
tests/     pytest suite, including numerical checks of the theory
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_data.py      # Online Retail II and CDNOW -> data/raw/
pytest
```

dunnhumby *The Complete Journey* must be obtained from dunnhumby and placed at
`data/raw/dunnhumby_transaction_data.csv`; it is not redistributed.

## Data

- Online Retail II: Chen, D. (2019), UCI Machine Learning Repository,
  https://doi.org/10.24432/C5CG6D (CC BY 4.0).
- CDNOW: Fader, Hardie & Lee (2005), Journal of Marketing Research 42(4), 415–430.
- dunnhumby: *The Complete Journey*, https://www.dunnhumby.com/source-files/.

Raw data are not stored in the repository (`data/raw/` is gitignored); only aggregate results are.
