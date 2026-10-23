# Results: tie-aware fuzzy memberships (plan addendum C)

Plan: [EXTENSION_PLAN.md, Addendum C](EXTENSION_PLAN.md#addendum-c-2026-10-23-tie-aware-fuzzy-memberships),
committed before any outcome-based analysis of the variant. **Exploratory**: motivated by
the CDNOW results and evaluated on CDNOW, which had already been analysed.
Run: `python scripts/evaluate_tie_aware.py` (≈ 2 h). Outputs: `results/tie_aware/`.

## Method

A block of k > 1 customers with the same value occupies k ranks. Each member's term
memberships are averaged over that rank interval before rounding to {0, ½, 1}. On CDNOW
the 11,840 one-time buyers move from "fully F2" to "partly F1, F2 and F3"; R, M and all
untied values are unchanged.

## Summary

| Question | Result |
|---|---|
| Fewer tie-artifact rules? | **Yes: 41 → 0.** Rules ≥ 0.60 drop from 209 to 158, core-frequent concepts from 238 to 197 |
| More stable structure? | **Yes, back to crisp level.** Bootstrap Jaccard 0.963 (min 0.920) vs 0.908 (min 0.524) plain fuzzy; crisp 0.966 (min 0.893) |
| More robust concept memberships? | **Slightly.** Concept-degree change 0.0072 vs 0.0076, lower in 20/20 replicates |
| Different predictions? | **No.** All four tests non-significant, every difference < 0.0002 |
| Online Retail II affected? | Essentially no: no customer changes on full data; in 19 of 40 fold/part checks a few customers change, max 0.8 % |

## Prediction (C1–C2, Holm over four)

| Test | Setting | Comparison | Metric | Difference [95 % CI] | Holm p |
|---|---|---|---|---|---|
| C1a | fixed | F-ctx-T − F-ctx | AUC | −0.00002 [−0.00006, +0.00003] | 1.00 |
| C1b | fixed | F-ctx-T − F-ctx | R² | −0.000002 [≈ 0, ≈ 0] | 0.64 |
| C2a | tuned | F-fca-core-T − F-fca-core | AUC | −0.0001 [−0.0005, +0.0003] | 1.00 |
| C2b | tuned | F-fca-core-T − F-fca-core | R² | +0.0001 [−0.0001, +0.0004] | 0.98 |

Means (tuned): F-fca-core-T AUC 0.7877, R² 0.2349; F-fca-core 0.7878, 0.2348; logRFM 0.7884,
0.2407. The tie-aware lattice keeps every advantage of the plain one over the crisp
methods (vs C-fca: AUC +0.0039, R² +0.0126; vs F-ctx-T: R² +0.0156; all 4/4 origins, p = 0.001)
and the same gap to continuous log-RFM on spend (−0.006 R²).

At fixed regularisation, the tie-aware lattice is 0.0005 R² below the plain one (p = 0.001,
descriptive). The difference is negligible in size.

## Structure

| | Crisp | Fuzzy core | Fuzzy core, tie-aware (Łuk.) | Tie-aware (Gödel) |
|---|---|---|---|---|
| Concepts | 151 | 1,892 | 1,742 | 1,730 |
| Core-frequent | 54 | 238 | 197 | 198 |
| Rules ≥ 0.60 | 19 | 209 | 158 | 161 |
| Tie-artifact rules | 0 | 41 | **0** | **0** |
| Bootstrap Jaccard, mean (min) | 0.966 (0.893) | 0.908 (0.524) | **0.963 (0.920)** | 0.964 (0.920) |

A tie-artifact rule only raises one F term from ½ to 1 with confidence ≥ 0.999, e.g.
{½/F2} ⇒ {F2}.

## Robustness (20 replicates, 5 % of purchases dropped)

| | Crisp | Fuzzy | Fuzzy tie-aware |
|---|---|---|---|
| Context change | 0.0341 | 0.0321 | 0.0321 (identical in every replicate) |
| Concept-degree change | 0.0087 | 0.0076 | **0.0072** (lower in 20/20) |

## Verdict

Spreading tied blocks over their rank interval fixes the two structural problems CDNOW
exposed: the trivial rules disappear and the lattice becomes as stable as the crisp one,
with a better worst case. It costs nothing in predictive performance and adds nothing,
which is expected: the members of a tied block are indistinguishable, so spreading them
cannot add information; it only describes the ambiguity honestly. Being exploratory, the
structural gains should be checked on a third dataset with heavy ties.

## Deviations

- The plan said the variant is identical on Online Retail II at full-data level and that
  per-fold identity would be checked. Per fold it is *nearly* identical: a few customers
  change in 19 of 40 checks (max 0.8 %). The variant was not run on Online Retail II.
