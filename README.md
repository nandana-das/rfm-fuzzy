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
- [ ] Fuzzy RFM context and fuzzy concept lattice.
- [ ] Evaluation against the crisp baseline.

## Layout

```
rfmfca/            library: data loading, RFM scoring, FCA lattice, clustering baselines
scripts/           fetch_data.py, replicate_base_paper.py, compare_with_paper.py
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
