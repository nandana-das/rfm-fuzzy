# Results: interpretability proxies (plan addendum I)

Plan: [EXTENSION_PLAN.md, Addendum I](EXTENSION_PLAN.md#addendum-i-2026-10-24-interpretability-proxies),
committed before computing. Descriptive, full data, no tests. These are structural stand-ins;
interpretability for people was not measured. Run: `python scripts/evaluate_interpretability.py`.
Outputs: `results/interpretability/`.

## Measures (Retail II / CDNOW / dunnhumby)

| Method | Segments | Description fidelity (F1) | Description length (conditions) | Segments per customer | Rules ≥ 0.60 | Mean rule confidence |
|---|---|---|---|---|---|---|
| C-fca (base paper) | 51 / 54 / 49 | 1.00 / 1.00 / 1.00 | 1.47 / 1.60 / 1.50 | 5.3 / 6.2 / 5.5 | 10 / 19 / 18 | 0.73 / 0.84 / 0.81 |
| **F-fca-core (fuzzy RFM-FCA)** | 208 / 238 / 215 | 1.00 / 1.00 / 1.00 | 1.77 / 1.93 / 1.82 | 19.5 / 24.0 / 20.9 | 137 / 209 / 185 | 0.71 / 0.81 / 0.79 |
| K-means, k = 10 | 10 | 0.68 / 0.74 / 0.74 | 3.0 | 1 | — | — |
| GMM, k = 10 | 10 | 0.53 / 0.80 / 0.67 | 3.0 | 1 | — | — |
| FCM, k = 10 | 10 | 0.66 / 0.71 / 0.73 | 3.0 | 1 | — | — |

- **Boundary customers:** 74 % / 69 % / 73 % of customers lie within 0.05 of a quintile cut point
  on at least one dimension. For most customers, the crisp segment hinges on a near-arbitrary cut;
  fuzzy memberships represent that ambiguity, crisp scores and hard clusters do not.
- **Softness of soft clusters:** mean largest membership 0.69 / 0.96 / 0.80 (GMM), 0.50 / 0.66 / 0.55
  (FCM): fuzzy C-means memberships are diffuse, often with no dominant cluster.

## Reading

**Where FCA (crisp or fuzzy) wins**
- **Exact descriptions.** FCA segments *are* their descriptions (fidelity 1.0 by construction).
  Describing a cluster in R/F/M terms, even with the tightest ranges covering 80 % of members,
  misclassifies a lot: F1 0.53–0.80, i.e. 20–47 % of the description's customers or of the cluster's
  members disagree.
- **Shorter descriptions.** FCA segments need 1.5–1.9 conditions; every cluster needs all three
  dimensions constrained.
- **Rules.** Only FCA gives implication rules between segments.

**Where fuzzy RFM-FCA pays a price**
- **Many more segments.** 208–238 frequent concepts vs 49–54 crisp and 10 clusters; each customer
  sits in about 20 segments (crisp ~6). A marketer cannot read 200 segments; a usable deliverable
  needs a summary view (e.g. the top levels of the hierarchy, or a selected subset), which this
  project has not built.
- **Rule confidence is not higher on average.** Mean confidence is slightly *lower* than crisp
  (0.71 vs 0.73, 0.81 vs 0.84, 0.79 vs 0.81), with many more rules. Individual boundary-aware rules
  can be sharper (e.g. {R5, M5} ⇒ {R5, ½F5, M5} at 0.92 vs the crisp {R5, M5} ⇒ {R5, F5, M5} at
  0.81 on Retail II), but this does not hold for the rule set as a whole.

## Verdict

FCA's interpretability advantage over clustering is real and measurable: exact, short, rule-linked
segment descriptions. Fuzzy RFM-FCA keeps that advantage and adds explicit handling of the ~70 % of
customers who sit near a quintile boundary, but it produces about four times as many segments as
crisp FCA, and its rules are not more confident on average. The claim "more interpretable than
crisp FCA" is **not** supported by these proxies; "as exactly describable as crisp FCA, far more
than clustering, while representing boundary customers" is.
