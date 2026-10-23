# Results: CDNOW confirmation (plan addendum B)

Plan: [EXTENSION_PLAN.md, Addendum B](EXTENSION_PLAN.md#addendum-b-2026-10-23-confirmation-on-cdnow),
committed before any outcome-based CDNOW analysis. Method applied unchanged from
Online Retail II. Run: `python scripts/confirm_cdnow.py` (≈ 75 min). Outputs: `results/cdnow/`.

**Disclosure.** Before the full run, a smoke test on a 3,000-customer sample at one cutoff
with 2 folds printed comparison numbers; the plan was already committed and was not changed.

## Data and design

23,570 customers (first purchase Q1 1997), 69,659 purchase rows to 1998-06-30. Four
cutoffs (1997-07-01 … 1998-04-01), ~23,500 customers each, 14–18 % buy in the next 90 days.
52–65 % of customers have bought once, so F1 and F3 are empty and fuzzy partial
memberships on F are rare (`band_occupancy.csv`).

## Confirmatory claims

| Claim | Setting | Comparison | Metric | Difference [95 % CI] | Holm p | Origins | Replicates |
|---|---|---|---|---|---|---|---|
| B1a | fixed | F-ctx − C-ctx | AUC | +0.0038 [+0.0029, +0.0048] | 0.005 | 4 / 4 | **yes** |
| B1b | fixed | F-ctx − C-ctx | R² | +0.0099 [+0.0083, +0.0114] | 0.005 | 4 / 4 | **yes** |
| B2a | tuned | F-fca-core − C-fca | AUC | +0.0040 [+0.0026, +0.0056] | 0.005 | 4 / 4 | **yes** |
| B2b | tuned | F-fca-core − C-fca | R² | +0.0124 [+0.0100, +0.0148] | 0.005 | 4 / 4 | **yes** |
| B3 | tuned | F-fca-core − F-ctx | R² | +0.0154 [+0.0134, +0.0173] | 0.005 | 4 / 4 | **yes** |
| B4a | — | context change, fuzzy vs crisp | | 0.0321 vs 0.0341 | — | 20 / 20 replicates | **yes** |
| B4b | — | concept change, F-fca-core vs C-fca | | 0.0076 vs 0.0087 | — | 20 / 20 replicates | **yes** |

p = 0.001 is the bootstrap floor, so 0.005 is the smallest Holm value possible for five tests.
Effect sizes are close to Online Retail II (e.g. B1a +0.0038 vs +0.0036; B2b +0.0124 vs +0.0089).

## All methods (means over origins)

| Method | AUC fixed | R² fixed | AUC tuned | R² tuned |
|---|---|---|---|---|
| C-ctx | 0.7847 | 0.2094 | 0.7837 | 0.2094 |
| C-fca (base paper) | 0.7836 | 0.2220 | 0.7839 | 0.2223 |
| F-ctx | 0.7885 | 0.2193 | **0.7885** | 0.2193 |
| F-fca-core (Łukasiewicz) | 0.7852 | 0.2330 | 0.7878 | 0.2348 |
| F-fca-G-core (Gödel) | 0.7851 | 0.2330 | 0.7865 | 0.2349 |
| logRFM | **0.7903** | **0.2407** | 0.7884 | **0.2407** |

Differences from Online Retail II worth reporting:
- **Fixed regularisation no longer hurts the fuzzy lattice.** On CDNOW (5× more customers)
  F-fca-core vs C-fca at fixed settings is +0.0016 AUC (p = 0.06) and +0.0110 R² (p = 0.001),
  where on Online Retail II it was significantly negative. The overfitting seen there is a
  small-sample effect.
- **Continuous log-RFM is best on spend** (R² 0.241 vs 0.235 for the best FCA method,
  significant), and ties on AUC. On Online Retail II the FCA methods matched or beat it.
  With heavy ties in frequency, a discretised representation loses more of the
  monetary/frequency gradient than a continuous one.
- **Structure stability is worse for fuzzy here.** Bootstrap Jaccard: crisp 0.966 (min 0.893),
  Łukasiewicz-core 0.908 (min 0.524), Gödel-core 0.925 (min 0.610). Concepts built around
  the large tied one-purchase block appear and disappear with resampling.
- **Many rules are tie artifacts.** The top core rules, e.g. {½/F2} ⇒ {F2} with confidence 1.0,
  restate that one-time buyers sit exactly at the F2 centre; they carry no marketing
  content. 238 core-frequent concepts and 209 rules (crisp: 54 and 19).

## Verdict

Every pre-registered claim replicates on CDNOW: fuzzy memberships beat crisp quintile
indicators, the core-filtered fuzzy lattice (with tuned regularisation) beats the
crisp lattice and adds spend-prediction signal beyond the fuzzy memberships, and fuzzy
representations are more robust to dropped transactions. The limits also replicate or
sharpen: no FCA representation beats continuous log-RFM on CDNOW spend, and with heavily
tied frequency the fuzzy lattice is less stable and partly filled with trivial rules.
A tie-aware membership (spreading a tied block over the rank interval it occupies) is the
obvious fix and was not tested.
