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

---

## Addendum B (2026-10-23): confirmation on CDNOW

Written and committed **before** any outcome-based analysis of CDNOW. Done beforehand
(structure and base rates only): row/customer counts, band occupancy, lattice sizes and
build times at the four cutoffs below, and the share of customers who buy in each horizon.

**Data.** CDNOW master (Fader & Hardie): 23,570 customers who first bought in Q1 1997,
69,659 purchase rows to 1998-06-30. Each purchase row is treated as one invoice line;
frequency = purchase rows, monetary = summed dollar value. Zero-value rows are kept and
zero-spend customers dropped, as for Online Retail II.

**Method.** Exactly as in the main plan and Addendum A, no changes. In particular, ties
keep their mid-rank. Known consequence (seen in the feasibility check): 52–65 % of customers
have one purchase, so F1 and F3 are empty and fuzzy partial memberships on F are rare;
fuzzification acts mainly on R and M. This makes CDNOW a conservative test.

**Design.** Cutoffs 1997-07-01, 1997-10-01, 1998-01-01, 1998-04-01; 90-day horizons;
customers with positive spend before the cutoff (~23,500). Same targets, models, 5-fold CV,
fold-wise fitting, fixed (C = 1, α = 1) and tuned (inner 3-fold CV, 10⁻⁴…10²) settings,
and the same paired bootstrap. Methods: C-ctx, C-fca, F-ctx, F-fca-core, F-fca-G-core,
logRFM. (The sigma-count F-fca is not carried forward.)

**Confirmatory claims** (each replicates if the difference has the Online Retail II sign
and Holm-adjusted p < 0.05 over the five tests):

| # | Claim | Setting | Metric |
|---|---|---|---|
| B1a | F-ctx > C-ctx | fixed | AUC |
| B1b | F-ctx > C-ctx | fixed | R² |
| B2a | F-fca-core > C-fca | tuned | AUC |
| B2b | F-fca-core > C-fca | tuned | R² |
| B3 | F-fca-core > F-ctx | tuned | R² |

**Robustness claims** (replicate if fuzzy is lower in all 20 invoice-drop replicates, p = 0.05):
B4a context-level change, F-ctx vs C-ctx; B4b concept-degree change, F-fca-core vs C-fca.

**Descriptive:** all other method comparisons in both settings, concept counts, rules
≥ 0.60 among core-frequent concepts, bootstrap Jaccard stability (50 samples) of the
frequent sets, band occupancy per cutoff.

---

## Addendum C (2026-10-23): tie-aware fuzzy memberships

Written and committed **before** any outcome-based analysis of the tie-aware variant. It
is motivated by the CDNOW results (heavily tied frequency), and CDNOW has already been
analysed, so this is an exploratory follow-up, not a confirmation.

**Method.** A block of k > 1 customers with the same value occupies k ranks. Instead of
placing all of them at the block's mid-rank, each member's term memberships are the
triangular memberships averaged over u ~ Uniform on the block's rank interval (centred on
the same mid-rank), then rounded to {0, ½, 1} as before. Untied and unseen values are
unchanged. Crisp methods are unchanged.

**Structure-only check before this addendum** (full data): on CDNOW the context changes for
50.4 % of customers, all on F (one-time buyers move from "fully F2" to "partly F1, F2, F3");
R and M do not change. Core-frequent concepts: 197 (Łukasiewicz) / 198 (Gödel). On Online
Retail II **no customer's context changes**, so the variant is identical there and is
evaluated on CDNOW only; per-fold identity on Online Retail II is checked and reported.

**Methods** (CDNOW, same design as Addendum B): F-ctx-T, F-fca-core-T (Łukasiewicz),
F-fca-G-core-T (Gödel), alongside C-ctx, C-fca, F-ctx, F-fca-core, logRFM.

**Tests** (two-sided; the tie-aware variant could help or hurt):

| # | Comparison | Setting | Metric |
|---|---|---|---|
| C1a | F-ctx-T − F-ctx | fixed | AUC |
| C1b | F-ctx-T − F-ctx | fixed | R² |
| C2a | F-fca-core-T − F-fca-core | tuned | AUC |
| C2b | F-fca-core-T − F-fca-core | tuned | R² |

Holm over the four. Descriptive: every method vs logRFM and vs crisp; both settings.

**Structure and robustness (descriptive, expected direction stated):**
- Bootstrap Jaccard (50 samples) of core-frequent sets, F-fca-core-T vs F-fca-core
  (expected higher, especially the minimum).
- Number of "tie-artifact" rules among rules ≥ 0.60: rules whose consequent only raises a
  ½ to 1 on one F term, with confidence ≥ 0.999 (expected fewer).
- Context and concept-degree change under the 20-replicate invoice-drop design, tie-aware
  vs plain fuzzy.

---

## Addendum D (2026-10-23): confirmation on dunnhumby "The Complete Journey"

Written and committed **before** any outcome-based analysis of this dataset in this
project. Done beforehand (structure and base rates only): row/household counts, tie sizes,
lattice sizes and build times at the cutoffs below, the share of customers changed by the
tie-aware variant, and the share of households buying in each horizon.

**Prior exposure, disclosed.** An earlier, separate project by the same author analysed this
dataset with a different fuzzy RFM-FCA method (threshold-scaled context, no core filter, no
tie handling); its summary results were seen during this project. No method or claim below
was tuned on this dataset.

**Data.** 2,500 households, 2,595,732 basket lines over 711 days (2,581,266 after dropping
quantity ≤ 0 or negative sales value). Household = customer, basket line = invoice line,
SALES_VALUE = spend. Day numbers are mapped to dates from an arbitrary anchor.

**Design.** As in Addendum B. Cutoffs at days 351, 441, 531, 621 (≥ 350 days of history,
90-day horizons, last horizon ends at day 711), ~2,500 households each. Same methods
(C-ctx, C-fca, F-ctx, F-fca-core, F-fca-G-core, logRFM), models, folds, settings and bootstrap.

**Confirmatory claims:** D1a, D1b, D2a, D2b, D3, identical in content to B1a–B3 (same
comparisons, settings, metrics, direction, Holm over five), and D4a, D4b identical to B4a–B4b.

**Known limitations from the structure check:**
- 92–93 % of households buy in every horizon, so the AUC claims rest on few non-buyers;
  spend R² is the more informative target.
- The tie-aware variant changes 0–0.1 % of customers here, so it is **not** tested on this
  dataset (it cannot be confirmed where it does nothing).

---

## Addendum E (2026-10-23): hybrid of fuzzy concepts and log-RFM

Written and committed **before** any hybrid result was computed. **Exploratory**: designed
after all three datasets showed that continuous log-RFM often matches or beats every
segment representation, and run on those same datasets.

**Question.** Do fuzzy concept memberships add predictive information *on top of* the
exact R, F, M values?

**Methods** (tuned regularisation only, same origins, folds, models and bootstrap as before):
`HYB-fca` = F-fca-core degrees + log1p(R, F, M); `HYB-ctx` = F-ctx memberships + log1p(R, F, M);
`HYB-cfca` = C-fca indicators + log1p(R, F, M) (the base-paper lattice in the same hybrid);
plus F-fca-core and logRFM for reference.

**Comparisons** (two-sided, per dataset, Holm over the six tests within a dataset):
E1 HYB-fca − logRFM (AUC, R²); E2 HYB-fca − HYB-cfca (AUC, R²); E3 HYB-fca − HYB-ctx (AUC, R²).
All three datasets reported, whatever the direction.

---

## Addendum F (2026-10-24): clustering baselines (K-means, GMM, fuzzy C-means)

Written and committed **before** any clustering-baseline result was computed. The fuzzy
RFM-FCA method is fixed as specified in Addendum A; only new baselines are added. The
datasets have been analysed before, so dataset reuse is disclosed, but no baseline result
has been seen and nothing about the proposed method is changed after this point.

**Baselines.** Fitted on the standardised log1p(R, F, M) of the training customers of each fold:
- `KM`: K-means (n_init = 10), features = one-hot cluster membership;
- `GMM`: Gaussian mixture, full covariance (n_init = 3), features = posterior probabilities;
- `FCM`: fuzzy C-means, fuzzifier m = 2 (max 300 iterations, tolerance 1e-5), features = membership degrees.

**Number of clusters.** Primary: chosen inside each training fold as the k in 2–10 with the
highest silhouette of K-means on a random sample of ≤ 3,000 training customers (the base
paper's criterion, no outcome used); the same k is used for all three algorithms.
Sensitivity: k = 10 for all three (`KM10`, `GMM10`, `FCM10`).

**Prediction** (tuned regularisation, same origins, folds, models, bootstrap as before):
F1 F-fca-core − FCM, F2 F-fca-core − KM, F3 F-fca-core − GMM, each on AUC and R²;
two-sided, Holm over the six within each dataset; all three datasets reported.
Descriptive: F-ctx, C-fca and logRFM against every baseline, and the k = 10 variants.

**Structure similarity** (a measure that applies to every representation): draw 20,000
random customer pairs; for a representation (rows = customers' feature vectors), the
similarity of a pair is the cosine of their two vectors. Agreement between two fits =
Pearson correlation of the pair similarities over the same pairs (1 = identical structure).
- *Robustness:* 20 replicates dropping 5 % of invoices; refit on perturbed data; compare with
  the full-data fit on customers present in both.
- *Stability:* 20 bootstrap samples of customers; fit on the sample, apply to all original
  customers; compare with the full-data fit.
Methods: C-fca, F-fca-core, KM, GMM, FCM (primary k chosen on the full data the same way).
Reported descriptively (mean, min, and replicates where F-fca-core exceeds each baseline).

---

## Addendum G (2026-10-24): structure agreement against k = 10 clustering

Written and committed **before** this analysis was run. Motivated by Addendum F, where the
silhouette rule chose k = 2 everywhere, so the structural comparison with clustering was
not like for like.

**Design.** Exactly the structure-agreement design of Addendum F (20,000 customer pairs; 20
invoice-drop replicates; 20 customer bootstraps; same seeds), with methods C-fca, F-fca-core,
KM10, GMM10, FCM10 on all three datasets.

**Reported** (descriptive): mean and minimum agreement per method, and the number of
replicates in which F-fca-core exceeds each baseline, for robustness and for stability.

---

## Addendum H (2026-10-24): business value of targeting

Written and committed **before** any targeting result was computed. Datasets reused (disclosed);
methods unchanged.

**Question.** If a marketer contacts only the top-ranked customers, how much of the next 90 days'
revenue and how many buyers does each representation reach?

**Design.** Same origins, folds and tuned-regularisation models as before; out-of-fold scores for
C-fca, F-fca-core, F-ctx, logRFM, KM10, GMM10, FCM10 (out-of-fold predictions are saved this time).
- *Revenue captured at q %*: rank customers by predicted log spend; share of the horizon's total
  revenue (sum of spend) held by the top q % (q = 10, 20).
- *Response lift at q %*: rank by predicted purchase probability; purchase rate in the top q %
  divided by the overall rate (q = 10, 20).
- *Gain curves*: cumulative revenue share against share of customers contacted, 1 %–100 %.

**Tests.** Primary, per dataset, Holm over four: H1 F-fca-core − C-fca and H2 F-fca-core − FCM10,
each on revenue captured at 20 % and lift at 20 %; same paired customer bootstrap, mean over origins.
Descriptive: all other methods and q = 10 %.

---

## Addendum I (2026-10-24): interpretability proxies

Written and committed **before** any of these measures was computed. Descriptive only (no
hypothesis tests). Interpretability for people is not measured; these are structural stand-ins.

**Setting.** Full data of each dataset; methods C-fca, F-fca-core, KM10, GMM10, FCM10 (GMM and FCM
hard-assigned by largest membership; the full-data fits used in Addendum G).

**Segments and descriptions.**
- FCA: segments = frequent concepts (crisp: extent; fuzzy: core, i.e. degree 1); description =
  the intent (a term satisfied when the customer's membership is at least the intent's level).
- Clusters: description = for each of R, F, M, the shortest run of adjacent crisp quintile terms
  holding ≥ 80 % of the cluster's members; a dimension whose run spans all five terms is dropped.
  A customer satisfies it when their crisp quintiles fall in every run.

**Measures.**
1. *Description fidelity*: F1 between "satisfies the description" and "is a member", averaged over
   segments weighted by size (FCA is 1 by construction; computed anyway as a check).
2. *Description length*: number of constrained dimensions per segment (size-weighted mean).
3. *Number of segments*; *coverage* (share of customers in ≥ 1 segment); *overlap* (mean number of
   segments per covered customer).
4. *Rules* (FCA only): rules ≥ 0.60 along covers among segments (as in Addendum A), their number,
   mean confidence and share ≥ 0.80.
5. *Softness* (GMM, FCM): mean largest membership per customer.
6. *Boundary customers*: share of customers within 0.05 of a quintile cut point (rank scale) on at
   least one dimension, i.e. those whose crisp segment hinges on a near-arbitrary cut.

---

## Addendum J (2026-10-24): a summary view of K selected concepts

Written and committed **before** any result for the selected concepts. Motivated by Addendum I
(fuzzy RFM-FCA yields ~200 segments). Datasets reused (disclosed).

**Selection (unsupervised, fitted on training customers only).** Candidates = the frequent concepts
(crisp: support ≥ 0.04; fuzzy: core support ≥ 0.04). A customer's *explained mass* given a set of
selected concepts = the largest intent size (sum of intent degrees: a full term 1, a ½-term ½) among
selected concepts the customer is *fully* in (degree 1), or 0. Greedy: start empty; K times, add the
candidate with the largest gain in total explained mass (ties: larger core support, then lower index).
K = 10 and K = 20. Features = degrees in the selected concepts (crisp: 0/1).

**Methods.** `F-sel10`, `F-sel20` (fuzzy, Łukasiewicz), `C-sel10`, `C-sel20` (crisp), against KM10,
GMM10, FCM10 and the full F-fca-core / C-fca.

**Prediction** (tuned regularisation, same origins, folds, bootstrap). Primary, per dataset, Holm over
four: S1 F-sel10 − C-sel10 and S2 F-sel10 − FCM10, on AUC and R². Descriptive: all other pairs, K = 20.

**Structure agreement** as in Addendum G (20 + 20 replicates, same seeds), methods F-sel10, C-sel10,
F-sel20, C-sel20, KM10, GMM10, FCM10.

**Interpretability proxies** (full data) as in Addendum I, plus: coverage (share of customers fully in
≥ 1 selected concept) and mean explained mass / 3.
