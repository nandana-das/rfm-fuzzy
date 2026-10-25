# Replication of the base paper

**Base paper:** Rungruang, C., Riyapan, P., Intarasit, A., Chuarkham, K., Muangprathub, J.
*RFM model customer segmentation based on hierarchical approach using FCA.* Expert Systems with Applications 237 (2024) 121449 (replicated from the preprint, SSRN 4416218).

**Data:** UCI Online Retail II, 1 Dec 2009 – 9 Dec 2011, 1,067,371 rows.

Reproduce:

```bash
python scripts/replicate_base_paper.py   # writes results/replication/
python scripts/compare_with_paper.py     # paper vs replication tables
```

## Pipeline (as implemented)

| Step | Paper | Here |
|---|---|---|
| Cleaning | Drop nulls, quantity/price <= 0 → 805,620 rows | Drop nulls, quantity <= 0, price < 0 → **805,620** (see note 1) |
| Customers | 5,878 | **5,878** (customers with zero total spend dropped) |
| Recency | Days since last purchase, reference = latest invoice date | Calendar days between dates (note 2) |
| Frequency | Number of transactions | Number of transaction rows (line items) |
| Monetary | Total spend | Sum of quantity × price; total **17,743,429.18** = paper Table 7 total |
| Scores | Quintiles, 5 = best | Quantile cut points (`pd.qcut`), recency reversed |
| Context | 15 binary attributes R1..M5 | same |
| Lattice | 208 concepts | **208** concepts |
| Frequent concepts | support >= 0.04 | 51 concepts, Hasse diagram in `hasse_frequent_concepts.png` |
| Rules | confidence >= 60 % | Rules along lattice covers (Luxenburger basis), 17 at >= 60 % |

## Agreement with the paper

- **Concept sizes** (`paper_comparison_concepts.csv`, all 34 concepts printed in Tables 4 and 6):
  20 exact, mean absolute difference 0.8 customers, maximum 5 (`{M1}`: 1,176 vs 1,181).
  Every frequency–monetary pair except the F1/F2 × M1 ones matches exactly.
- **Rules** (`paper_comparison_rules.csv`): all 18 rules of Table 5 recomputed; every
  confidence within 0.01 of the paper. Rule 18 (`R5 F1 => M1`) is 47/80 = 58.75 %
  here vs 48/80 = 60 % in the paper, so it falls just below the 60 % cut.
- **Purchase value** (`purchase_value_by_concept.csv`): `{M5}` holds 77.26 % of spend,
  `{F5}` 66.62 %, `{M1}` 1.09 %, the same as Table 7 to two decimals.
- **K-means / Ward baselines** (`clustering_validity.csv`): K-means silhouette 0.39 at
  k = 2 and 0.35 at k = 4 (paper 0.40, 0.33); Davies–Bouldin 0.99 at k = 2 (paper 1.04).
  Shape of both curves matches Figures 9–10 qualitatively, not exactly (note 3).

## Deviations and their causes

1. **Zero-price rows.** The text says rows with price <= 0 are removed, but 805,620 rows
   remain only if zero-price rows are kept (removing them leaves 805,549). The
   paper's count is followed. Three customers whose purchases are all zero-price
   then have zero spend; dropping them gives the paper's 5,878 customers.
2. **Recency unit.** Counting calendar days (date of last purchase to date of the
   latest invoice) instead of elapsed 24-hour periods cuts the total absolute error
   over the recency concepts from 84 to 11 customers, so the calendar-day version is used.
3. **Outlier removal for the baselines.** The paper reports 5,633 customers left after
   IQR filtering. The rule as written (1.5 × IQR on raw R, F, M) leaves 5,040; no variant
   tried (log scale, k = 2 or 3, invoice-count frequency) gives 5,633. The literal
   rule is used. The paper also does not say whether recency is scaled; here all three
   log-transformed features are min–max scaled.
4. **Quintile ties.** The paper's single-attribute counts (`{M1}` 1,181, `{M3}` 1,172) are
   not what quantile cut points on continuous spend give (1,176 each); the binning rule
   in the paper's R code is unknown. The effect is at most 5 customers per concept.

## Files in `results/replication/`

| File | Content |
|---|---|
| `summary.json` | Row and customer counts, concept and rule counts, score distributions |
| `rfm_scores.csv` | Per-customer R, F, M values and scores |
| `concepts_all.csv` | All 208 concepts (Table 4 extended) |
| `concepts_frequent.csv` | Concepts with support >= 0.04 (Table 6) |
| `rules_conf60.csv` | Rules with confidence >= 60 % (Table 5) |
| `purchase_value_by_concept.csv` | Table 7 |
| `clustering_validity.csv`, `.png` | Figures 9–10 |
| `cluster_profiles.csv` | Tables 8–9 (mean RFM per cluster, k = 4, 5, 6) |
| `hasse_frequent_concepts.png` | Figure 8 equivalent |
| `paper_comparison_*.csv` | Side-by-side with the paper's printed numbers |
