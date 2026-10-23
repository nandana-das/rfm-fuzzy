"""Replicate Rungruang et al., "RFM Model Customer Segmentation Based on
Hierarchical Approach Using FCA", on UCI Online Retail II.

Writes tables and figures to results/replication/.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rfmfca import clustering  # noqa: E402
from rfmfca.data import clean_transactions, load_transactions  # noqa: E402
from rfmfca.fca import ConceptLattice  # noqa: E402
from rfmfca.rfm import binary_context, compute_rfm, quintile_scores  # noqa: E402

OUT = ROOT / "results" / "replication"
MIN_SUPPORT = 0.04      # paper Section 5: concepts with support > 0.04
MIN_CONFIDENCE = 0.60   # paper Table 5
MAIN_CONCEPTS = ["M1", "M2", "M3", "M4", "M5", "F5"]  # paper Table 7


def draw_hasse(lattice, concepts, path):
    edges = lattice.induced_covers(concepts)
    levels = {}
    for c in concepts:
        levels.setdefault(bin(c.intent).count("1"), []).append(c)
    pos = {}
    for depth, row in levels.items():
        row.sort(key=lambda c: lattice.label(c.intent))
        for i, c in enumerate(row):
            # Stagger crowded rows so labels do not overlap.
            stagger = 0.35 * (i % 2) if len(row) > 16 else 0.0
            pos[c.intent] = ((i + 1) / (len(row) + 1), -depth - stagger)
    widest = max(len(row) for row in levels.values())
    fig, ax = plt.subplots(figsize=(max(14, widest * 0.75), 9))
    for lo, hi in edges:
        (x0, y0), (x1, y1) = pos[lo], pos[hi]
        ax.plot([x0, x1], [y0, y1], color="0.6", lw=0.8, zorder=1)
    for c in concepts:
        x, y = pos[c.intent]
        ax.text(x, y, f"{lattice.label(c.intent)}\n{c.extent_size} / {c.extent_size / lattice.n_objects:.0%}",
                ha="center", va="center", fontsize=7,
                bbox=dict(boxstyle="round", fc="white", ec="0.3"), zorder=2)
    ax.set_axis_off()
    ax.set_title(f"RFM concepts with support >= {MIN_SUPPORT}")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def draw_validity(curve, path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for metric, ax in zip(["silhouette", "davies_bouldin"], axes):
        for method, grp in curve.groupby("method"):
            ax.plot(grp["k"], grp[metric], marker="o", label=method)
        ax.set_xlabel("number of clusters")
        ax.set_ylabel(metric.replace("_", "-"))
        ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # Step 1: preprocessing and RFM.
    raw = load_transactions()
    tx = clean_transactions(raw)
    rfm = compute_rfm(tx)
    scores = quintile_scores(rfm)
    customers = rfm.join(scores)
    customers.to_csv(OUT / "rfm_scores.csv")

    # Step 2: FCA knowledge structure.
    context = binary_context(scores)
    lattice = ConceptLattice(context)
    lattice.table().to_csv(OUT / "concepts_all.csv", index=False)
    frequent = lattice.frequent(MIN_SUPPORT)
    freq_table = lattice.table()
    freq_table = freq_table[(freq_table.support >= MIN_SUPPORT) & (freq_table.attributes != "{}")]
    freq_table.to_csv(OUT / "concepts_frequent.csv", index=False)
    rules = lattice.association_rules(MIN_CONFIDENCE)
    rules.to_csv(OUT / "rules_conf60.csv", index=False)
    draw_hasse(lattice, frequent, OUT / "hasse_frequent_concepts.png")

    total_spend = customers["amount"].sum()
    value_rows = []
    for attr in MAIN_CONCEPTS:
        dim, level = attr[0], int(attr[1])
        members = customers[customers[dim] == level]
        value_rows.append({"concept": "{" + attr + "}",
                           "total_purchase_value": members["amount"].sum(),
                           "pct_purchase_value": members["amount"].sum() / total_spend,
                           "pct_customers": len(members) / len(customers)})
    pd.DataFrame(value_rows).to_csv(OUT / "purchase_value_by_concept.csv", index=False)

    # Step 3: traditional clustering baselines.
    trimmed = clustering.iqr_filter(rfm)
    x = clustering.prepare_features(trimmed)
    curve = clustering.validity_curve(x)
    curve.to_csv(OUT / "clustering_validity.csv", index=False)
    draw_validity(curve, OUT / "clustering_validity.png")
    profiles = []
    for method in ("kmeans", "hierarchical"):
        for k in (4, 5, 6):
            prof = clustering.cluster_profiles(trimmed, clustering.fit_labels(method, x, k))
            prof.insert(0, "k", k)
            prof.insert(0, "method", method)
            profiles.append(prof)
    pd.concat(profiles).to_csv(OUT / "cluster_profiles.csv", index=False)

    summary = {
        "raw_rows": len(raw),
        "clean_rows": len(tx),
        "customers": len(rfm),
        "total_purchase_value": round(float(total_spend), 2),
        "customers_after_iqr": len(trimmed),
        "n_concepts": len(lattice.concepts),
        "n_frequent_concepts": len(frequent),
        "n_rules_conf60": len(rules),
        "score_counts": {d: scores[d].value_counts().sort_index().to_dict() for d in "RFM"},
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=int))
    print(json.dumps(summary, indent=2, default=int))


if __name__ == "__main__":
    main()
