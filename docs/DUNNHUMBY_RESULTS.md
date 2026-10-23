# Results: dunnhumby confirmation (plan addendum D)

Plan: [EXTENSION_PLAN.md, Addendum D](EXTENSION_PLAN.md#addendum-d-2026-10-23-confirmation-on-dunnhumby-the-complete-journey),
committed before any outcome-based analysis of this dataset in this project (prior exposure
through an earlier, separate project is disclosed there). Method unchanged.
Run: `python scripts/confirm_dunnhumby.py` (≈ 35 min). Outputs: `results/dunnhumby/`
(aggregate results only; raw data not redistributed).

## Data and design

2,500 households, 2,581,266 basket lines, 711 days. Cutoffs at days 351, 441, 531, 621;
~2,500 households each; 92–93 % buy in every 90-day horizon, so AUC rests on few
non-buyers. The tie-aware variant changes ≤ 0.1 % of customers and was not tested.

## Confirmatory claims: 4 of 7 replicate

| Claim | Setting | Comparison | Metric | Difference [95 % CI] | Holm p | Origins | Replicates |
|---|---|---|---|---|---|---|---|
| D1a | fixed | F-ctx − C-ctx | AUC | +0.0090 [+0.0048, +0.0131] | 0.005 | 4 / 4 | **yes** |
| D1b | fixed | F-ctx − C-ctx | R² | +0.0139 [+0.0093, +0.0184] | 0.005 | 4 / 4 | **yes** |
| D2a | tuned | F-fca-core − C-fca | AUC | +0.0098 [+0.0014, +0.0188] | 0.018 | 3 / 4 | **yes** |
| D2b | tuned | F-fca-core − C-fca | R² | +0.0089 [+0.0034, +0.0142] | 0.008 | 4 / 4 | **yes** |
| D3 | tuned | F-fca-core − F-ctx | R² | **−0.0082** [−0.0112, −0.0051] | 0.005 | 0 / 4 | **no (reversed)** |
| D4a | — | context change, fuzzy vs crisp | | **0.0492 vs 0.0394** | — | fuzzy lower 2 / 20 | **no (reversed)** |
| D4b | — | concept change, F-fca-core vs C-fca | | 0.0100 vs 0.0110 | — | fuzzy lower 14 / 20 | **no** |

## All methods (means over origins)

| Method | AUC fixed | R² fixed | AUC tuned | R² tuned |
|---|---|---|---|---|
| C-ctx | 0.8709 | 0.5109 | 0.8692 | 0.5108 |
| C-fca (base paper) | 0.8650 | 0.5038 | 0.8552 | 0.5078 |
| F-ctx | 0.8799 | **0.5249** | 0.8767 | **0.5249** |
| F-fca-core | 0.8559 | 0.4905 | 0.8651 | 0.5167 |
| F-fca-G-core | 0.8558 | 0.4902 | 0.8639 | 0.5156 |
| logRFM | **0.8849** | 0.5171 | **0.8872** | 0.5169 |

- At fixed regularisation the core-filtered fuzzy lattice is again *below* crisp FCA
  (AUC −0.009, R² −0.013), as on Online Retail II: ~220 features for ~2,000 training
  households overfit. On CDNOW (~19,000 per fold) it did not.
- The fuzzy **memberships** (F-ctx) are the best method on spend R² (0.525, vs log-RFM
  0.517, p = 0.04), and second on AUC behind log-RFM.

## Structure

| | Crisp | Fuzzy core (Łuk.) | Fuzzy core (Gödel) |
|---|---|---|---|
| Concepts / core-frequent | 158 / 49 | 2,230 / 215 | 2,294 / 220 |
| Rules ≥ 0.60 | 18 | 185 | 194 |
| Bootstrap Jaccard, mean (min) | 0.799 (0.623) | **0.869 (0.795)** | 0.882 (0.814) |

Here the fuzzy structure is clearly **more** stable than the crisp one. Top rules are
monetary/frequency co-occurrence near the extremes, e.g. {R5, F5} ⇒ {R5, F5, ½/M5}, 0.99.

## Why the robustness claim failed here

Dropping 5 % of basket lines lowers almost every household's F and M a little, so
everyone's rank jitters slightly. With the 3-level chain there are two rounding cut
points between neighbouring term centres (memberships 0.25 and 0.75), each worth a
half-step, against one full-step cut point per quintile boundary for crisp. Under small
rank jitter the expected change is therefore about the same, and which one is lower
depends on where customers sit relative to the cut points. Here 9.2 % of households
change fuzzy context vs 6.6 % crisp, and the fuzzy total is higher. The earlier wins
(Online Retail II, CDNOW) were real but are **not a general property** of this
fuzzification.

## Verdict

Across three datasets (Online Retail II exploratory for Addendum A; CDNOW and dunnhumby
confirmatory):

| Finding | Online Retail II | CDNOW | dunnhumby | Status |
|---|---|---|---|---|
| Fuzzy memberships beat crisp quintiles (AUC, R²) | yes | yes | yes | **Robust** |
| Core-filtered fuzzy lattice beats crisp FCA (tuned) | yes | yes | yes | **Robust** |
| Fuzzy lattice adds spend signal beyond memberships | yes | yes | **reversed** | Not general |
| Fuzzy memberships more robust to dropped transactions | yes | yes | **reversed** | Not general |
| Fuzzy lattice needs tuned regularisation at small n | yes | n/a (large n) | yes | Consistent |
| Continuous log-RFM matched or beaten | matched | **beats FCA on spend** | F-ctx beats it on R² | Mixed |
