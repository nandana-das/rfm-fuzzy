# rfm-fuzzy

Fuzzy formal concept analysis for RFM customer segmentation, extending
Rungruang et al., *RFM Model Customer Segmentation Based on Hierarchical Approach Using FCA*
(SSRN 4416218).

The base paper scores customers into recency, frequency and monetary quintiles, turns
the scores into a binary formal context (R1..R5, F1..F5, M1..M5), and reads segments
and association rules off the concept lattice. Its stated future work is a
**non-binary (fuzzy) formal context**; that is what this repository builds.

## Status

- [x] **Replication of the base paper.** 208 concepts, the paper's concept sizes to within
  0.8 customers on average, all 18 published rules recomputed. See [docs/REPLICATION.md](docs/REPLICATION.md).
- [x] **Fuzzy RFM context and fuzzy concept lattice** (Bělohlávek, Łukasiewicz and Gödel,
  3-level chain). Plan fixed before evaluation: [docs/EXTENSION_PLAN.md](docs/EXTENSION_PLAN.md).
- [x] **Evaluation against the crisp baseline**: [docs/EXTENSION_RESULTS.md](docs/EXTENSION_RESULTS.md).
  - Fuzzy memberships beat crisp quintile scores out of sample at every origin
    (AUC +0.004, R² +0.008) and change less when 5 % of invoices are dropped (20/20 replicates).
  - The pre-registered fuzzy lattice predicted *worse* than the crisp lattice
    (overfitting: ~2,600 concepts vs ~50). With tuned regularisation (exploratory) it
    is slightly better than the crisp lattice, but not better than the fuzzy memberships alone.
- [x] **Addendum A: core-support threshold** (share of customers *fully* in a concept).
  It cuts the Łukasiewicz lattice from 2,649 to 208 frequent concepts and gives readable
  boundary-aware rules (e.g. {M5} ⇒ {½/F5, M5}, 0.86). Still worse than crisp FCA at the planned
  fixed regularisation. With tuned regularisation it beats crisp FCA (AUC +0.006, R² +0.009) and is
  the best method on spend R², a second-stage result that needs another dataset.

## Layout

```
rfmfca/            library: data loading, RFM scoring, FCA lattice, clustering baselines
scripts/           fetch_data.py, replicate_base_paper.py, compare_with_paper.py,
                   evaluate_{prediction,robustness,structure}.py, posthoc_tuned_regularization.py
results/           generated tables and figures
docs/              write-ups
tests/             pytest suite
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_data.py            # UCI Online Retail II -> data/raw/
python scripts/replicate_base_paper.py
python scripts/compare_with_paper.py
pytest
```

Data: Chen, D. (2019). *Online Retail II*. UCI Machine Learning Repository,
https://doi.org/10.24432/C5CG6D (CC BY 4.0). Not redistributed here.
