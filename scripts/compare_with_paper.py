"""Compare results/replication/ against the numbers printed in the base paper.

Writes results/replication/paper_comparison_concepts.csv and
paper_comparison_rules.csv. Run after replicate_base_paper.py.
"""
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "results" / "replication"

# Paper Tables 4 and 6 (concept -> number of customers).
PAPER_CONCEPTS = {
    "{M5}": 1176, "{M4}": 1174, "{M3}": 1172, "{M2}": 1175, "{M1}": 1181, "{F5}": 1175,
    "{F5, M5}": 842, "{F5, M4}": 256, "{F5, M3}": 74, "{F5, M2}": 3,
    "{F4, M5}": 237, "{F4, M4}": 576, "{F4, M3}": 238, "{F3, M3}": 577,
    "{F2, M2}": 603, "{F2, M1}": 262, "{F1, M1}": 813,
    "{R5, M5}": 533, "{R5, M4}": 287, "{R5, F5}": 546, "{R5, F5, M5}": 434,
    "{R4, M5}": 326, "{R4, M4}": 283, "{R4, M3}": 242, "{R4, F5}": 339, "{R4, F5, M5}": 241,
    "{R3, M4}": 320, "{R3, M3}": 262, "{R2, M3}": 282, "{R2, M2}": 338, "{R2, M1}": 296,
    "{R1, M2}": 334, "{R1, M1}": 517, "{R1, F1, M1}": 355,
}

# Paper Table 5: (premise, conclusion) -> (premise customers, rule customers, confidence).
PAPER_RULES = {
    ("R5 M5", "F5"): (533, 434, 0.81), ("R5 F5", "M5"): (546, 434, 0.79),
    ("R1 F1", "M1"): (475, 355, 0.75), ("R4 M5", "F5"): (326, 241, 0.74),
    ("R3 M1", "F1"): (168, 122, 0.73), ("R4 F1", "M1"): (122, 88, 0.72),
    ("F5", "M5"): (1175, 842, 0.72), ("M5", "F5"): (1176, 842, 0.72),
    ("R4 F5", "M5"): (339, 241, 0.71), ("M1", "F1"): (1178, 813, 0.69),
    ("R1 M1", "F1"): (515, 355, 0.69), ("R4 M1", "F1"): (128, 88, 0.69),
    ("F1", "M1"): (1189, 813, 0.68), ("R5 M1", "F1"): (71, 48, 0.68),
    ("R2 M1", "F1"): (296, 200, 0.68), ("R2 F1", "M1"): (305, 200, 0.66),
    ("R3 F5", "M5"): (182, 113, 0.62), ("R5 F1", "M1"): (80, 48, 0.60),
}


def main():
    ours = pd.read_csv(OUT / "concepts_all.csv").set_index("attributes")["customers"]
    concepts = pd.DataFrame(
        [(k, v, int(ours.get(k, 0))) for k, v in PAPER_CONCEPTS.items()],
        columns=["concept", "paper_customers", "replicated_customers"])
    concepts["difference"] = concepts.replicated_customers - concepts.paper_customers
    concepts.to_csv(OUT / "paper_comparison_concepts.csv", index=False)

    # Recompute every paper rule from our lattice, whether or not it passes 60 %.
    all_concepts = pd.read_csv(OUT / "concepts_all.csv").set_index("attributes")["customers"]

    def size(attrs):
        return int(all_concepts.get("{" + ", ".join(sorted(attrs, key=order)) + "}", 0))

    rows = []
    for (premise, conclusion), (n_p, n_r, conf) in PAPER_RULES.items():
        p = premise.split()
        q_size = size(p + conclusion.split())
        p_size = size(p)
        rows.append({"premise": premise, "conclusion": conclusion,
                     "paper_premise": n_p, "replicated_premise": p_size,
                     "paper_rule": n_r, "replicated_rule": q_size,
                     "paper_confidence": conf,
                     "replicated_confidence": round(q_size / p_size, 4) if p_size else None})
    rules = pd.DataFrame(rows)
    rules.to_csv(OUT / "paper_comparison_rules.csv", index=False)

    print(concepts.to_string(index=False))
    print(f"\nconcepts: mean |diff| = {concepts.difference.abs().mean():.2f}, "
          f"exact = {(concepts.difference == 0).sum()}/{len(concepts)}")
    print(rules.to_string(index=False))


def order(attr):
    return ("RFM".index(attr[0]), int(attr[1]))


if __name__ == "__main__":
    main()
