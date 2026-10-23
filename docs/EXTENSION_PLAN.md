# Extension plan: fuzzy RFM formal concept analysis

Written and committed **before** any evaluation code was run. The only computation
done beforehand was a feasibility check of lattice size (3-level scale: about 3,600
fuzzy concepts on the full data, built in ~10 s; 5-level scale: did not finish in
10 minutes). No predictive, stability or perturbation results were looked at.

## Motivation

The base paper (Rungruang et al.) turns quintile scores into a binary context. A
customer just below a quintile cut point and one just above it get disjoint
attributes (e.g. M4 vs M5) although their spend is almost equal. The paper names a
non-binary formal context as future work.

## Method (fixed)

1. **Rank scale.** For each dimension, map a customer's value to its mid-rank
   percentile u in (0, 1] among the customers being fitted (recency reversed, so
   higher u = more recent). Test customers are mapped through the fitted customers'
   empirical CDF.
2. **Linguistic terms.** Five triangular fuzzy sets per dimension centred at the
   quintile midpoints u = 0.1, 0.3, 0.5, 0.7, 0.9, half-width 0.2, with saturating
   outer shoulders. Memberships on each dimension sum to 1 (Ruspini partition), and
   the term with the largest membership is the customer's crisp quintile score, so
   the crisp base-paper context is the 0.5-cut of the fuzzy one.
3. **Truth scale.** Memberships are rounded to the nearest of L = {0, 0.5, 1}
   ("not", "partly", "fully"). Chosen for tractability and readability before any
   evaluation.
4. **Fuzzy concepts.** Bělohlávek's fuzzy concept lattice over L with the
   **Łukasiewicz** residuum a → b = min(1, 1 − a + b) (primary) and Gödel
   (sensitivity). Intents are computed as the min-closure of the generators
   {a → I(g, ·) : g ∈ G, a ∈ L}. A customer's degree in a concept is its extent
   degree B↓(g) = min_m (B(m) → I(g, m)).
5. **Frequent concepts.** Support = sigma-count of the extent / |G|; keep concepts
   with support ≥ 0.04 (the paper's threshold), excluding the top concept.
6. **Rules.** Along lattice covers, confidence = ‖ext(lower)‖ / ‖ext(upper)‖ with
   sigma-counts; report rules with confidence ≥ 0.60.

## Comparisons

Feature sets fed to the same downstream models:

| Code | Features | Role |
|---|---|---|
| C-ctx | 15 crisp attributes (quintile one-hot) | crisp context |
| C-fca | indicators of frequent crisp concepts | **base-paper method** |
| F-ctx | 15 fuzzy memberships (3-level) | fuzzy context |
| F-fca | degrees in frequent fuzzy concepts (Łukasiewicz) | **proposed method** |
| F-fca-G | as F-fca with Gödel residuum | sensitivity |
| logRFM | log1p of R, F, M (3 continuous features) | non-FCA reference |

## Hypotheses and tests

**H1 (prediction).** F-fca predicts next-period behaviour better than C-fca.

- Origins (cutoffs): 2010-12-01, 2011-03-01, 2011-06-01, 2011-09-01. Features use all
  transactions before the cutoff; targets use the next 90 days.
- Population: customers with positive spend before the cutoff.
- Targets: (a) any purchase in the horizon, ROC AUC from L2 logistic regression;
  (b) log1p horizon spend, R² from ridge regression (α = 1). Features standardised.
- 5-fold cross-validation per origin (seed 0). Rank scale, lattice and frequent
  concepts are fitted on the training fold only and applied to the test fold.
- Test: per origin, paired bootstrap (1,000 resamples of customers, out-of-fold
  predictions) of the metric difference; the pooled estimate is the mean over
  origins, with a bootstrap CI from resampling customers within each origin.
  Two-sided, α = 0.05, Holm correction over the two targets.
- Secondary (descriptive): F-ctx vs C-ctx (does fuzzification alone help?),
  F-fca-G vs F-fca, and every method vs logRFM.

**H2 (boundary robustness).** Fuzzy memberships change less than crisp ones under
small perturbations of the data.

- 20 replicates; in each, every invoice is dropped independently with p = 0.05,
  R/F/M are recomputed on the full-period data, and both contexts are refitted.
- Metric: mean over customers of the L1 change in the 15-attribute context,
  divided by 3 (so 0 = no change, 1 = every dimension moved fully to other terms);
  plus the share of customers whose crisp RFM cell changes.
- Also measured at concept level: mean absolute change in degree of membership in
  the frequent concepts of the unperturbed lattice.
- Test: paired difference across replicates (fuzzy − crisp), reported with its range;
  H2 holds if fuzzy is lower in all 20 replicates.

**H3 (structure, two-sided, descriptive).** Size and stability of the concept
structure.

- Number of concepts, frequent concepts, rules ≥ 0.60, mean intent size.
- Bootstrap stability: 50 bootstrap samples of customers; Jaccard similarity between
  the set of frequent intents in the sample and in the full data, crisp vs fuzzy.

## What will be reported regardless of outcome

All metrics in the tables above, for every origin and replicate, including results
that do not favour the fuzzy method. Any change to this plan after evaluation code
is run will be listed in a "deviations" section of the results document.

---

## Addendum A (2026-10-23): scale-aware support threshold

Written and committed **after** the results in EXTENSION_RESULTS.md were known and
**before** any outcome (prediction, robustness, stability) was computed for the new
filter. It is a follow-up on the same dataset, motivated by the H1 failure, so its
results are a second-stage analysis, not an independent confirmation.

**Problem.** Under the Łukasiewicz residuum every customer has degree ≥ 1 − max B(m) in
a concept with intent B, so sigma-count support treats near-universal ½-intents as
frequent: 2,649 of 3,841 concepts pass support ≥ 0.04.

**Structure-only check done before fixing this addendum** (full data, no outcomes):
at 0.04, sigma-count keeps 2,649 (Łukasiewicz) / 378 (Gödel) concepts; support rescaled
above the Łukasiewicz floor keeps 1,889 / 378; core support keeps 208 / 208; crisp keeps 51
under all three.

**Filter (fixed).** *Core support* = share of customers whose degree in the concept is
exactly 1 (the 1-cut of the fuzzy extent). Keep non-top concepts with core support ≥ 0.04.
For a binary context this equals ordinary support, so the crisp method is unchanged.
Membership features are still the full fuzzy degrees.

**Methods.** `F-fca-core` (Łukasiewicz degrees, primary) and `F-fca-G-core` (Gödel degrees,
secondary), compared with C-fca, C-ctx and F-ctx as defined above.

**Hypotheses and tests** (same origins, folds, models, bootstrap and α as the main plan):

- **A1 (prediction).** F-fca-core vs C-fca on AUC and R², fixed regularisation (C = 1,
  α = 1), Holm over the two targets. Secondary: F-fca-core vs F-ctx, F-fca-G-core vs C-fca,
  and the same comparisons with regularisation tuned by inner 3-fold CV over 10⁻⁴…10²
  (as in the exploratory follow-up).
- **A2 (robustness).** Concept-degree change of the core-frequent concepts under the H2
  invoice-drop design (20 replicates), F-fca-core vs C-fca; holds if lower in all 20.
- **A3 (structure, descriptive).** Concept counts, mean intent size, rules ≥ 0.60 among
  core-frequent concepts (confidence by core counts along induced covers), and bootstrap
  Jaccard stability of the core-frequent intent set (50 samples) vs crisp.

All numbers will be reported whatever their direction.
