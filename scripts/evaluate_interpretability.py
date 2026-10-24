"""Plan addendum I: structural interpretability proxies for FCA segments and clusters.

Usage: python scripts/evaluate_interpretability.py   (all three datasets)
Writes results/interpretability/*.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_hybrid import dataset  # noqa: E402
from rfmfca.evaluation import MIN_SUPPORT  # noqa: E402
from rfmfca.fuzzy import FuzzyConceptLattice, RankScaler, crisp_context, fuzzy_context  # noqa: E402
from rfmfca.rfm import compute_rfm  # noqa: E402
from rfmfca.segmenters import segment_features  # noqa: E402

OUT = ROOT / "results" / "interpretability"
DIMS = "RFM"
COVER = 0.80
CUTS = np.array([0.2, 0.4, 0.6, 0.8])


def f1(member, satisfies):
    tp = (member & satisfies).sum()
    return 2 * tp / (member.sum() + satisfies.sum()) if (member.sum() + satisfies.sum()) else 1.0


def fca_segments(ctx, n_levels, support_kind):
    lat = FuzzyConceptLattice(ctx, n_levels, "lukasiewicz")
    idx = lat.frequent(MIN_SUPPORT, support_kind)
    q = ctx.to_numpy()
    rows, members_all = [], []
    for i in idx:
        b = lat.intents[i]
        satisfies = (q >= b).all(axis=1)
        member = lat.degrees(q, b[None, :])[:, 0] >= 1
        dims = sum(int(b[5 * d:5 * d + 5].any()) for d in range(3))
        rows.append({"size": member.sum(), "f1": f1(member, satisfies), "length": dims})
        members_all.append(member)
    members = np.array(members_all)
    rules = lat.induced_cover_rules(idx, 0.60)
    return pd.DataFrame(rows), members, rules


def cluster_segments(labels, quint):
    rows = []
    for c in np.unique(labels):
        member = labels == c
        satisfies = np.ones(len(labels), bool)
        length = 0
        for d in range(3):
            counts = np.bincount(quint[member, d], minlength=5)
            best = None
            for width in range(1, 6):
                for lo in range(0, 6 - width):
                    share = counts[lo:lo + width].sum() / member.sum()
                    if share >= COVER and (best is None or counts[lo:lo + width].sum() > best[2]):
                        best = (lo, lo + width, counts[lo:lo + width].sum())
                if best is not None:
                    break
            lo, hi, _ = best
            if hi - lo < 5:
                length += 1
                satisfies &= (quint[:, d] >= lo) & (quint[:, d] < hi)
        rows.append({"size": member.sum(), "f1": f1(member, satisfies), "length": length})
    return pd.DataFrame(rows)


def weighted(df, col):
    return float(np.average(df[col], weights=df["size"])) if df["size"].sum() else float("nan")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary, rule_rows = [], []
    for name in ("retail", "cdnow", "dunnhumby"):
        tx, _ = dataset(name)
        rfm = compute_rfm(tx, tx["InvoiceDate"].max())
        u = RankScaler().fit(rfm).transform(rfm)
        crisp, fuzzy = crisp_context(u), fuzzy_context(u)
        quint = np.column_stack([crisp[[f"{d}{k}" for k in range(1, 6)]].to_numpy().argmax(axis=1) for d in DIMS])
        boundary = float((np.abs(u.to_numpy()[:, :, None] - CUTS).min(axis=2) <= 0.05).any(axis=1).mean())

        for method, ctx, n_levels, kind in (("C-fca", crisp, 2, "sigma"), ("F-fca-core", fuzzy, 3, "core")):
            seg, members, rules = fca_segments(ctx, n_levels, kind)
            covered = members.any(axis=0)
            summary.append({"dataset": name, "method": method, "n_segments": len(seg),
                            "fidelity_f1": weighted(seg, "f1"), "description_length": weighted(seg, "length"),
                            "coverage": float(covered.mean()),
                            "overlap": float(members[:, covered].sum(axis=0).mean()),
                            "n_rules_conf60": len(rules),
                            "rule_mean_confidence": float(rules.confidence.mean()) if len(rules) else np.nan,
                            "rule_share_conf80": float((rules.confidence >= 0.8).mean()) if len(rules) else np.nan,
                            "softness": np.nan, "boundary_customers": boundary})
            rules.insert(0, "method", method)
            rules.insert(0, "dataset", name)
            rule_rows.append(rules)

        for method, algo in (("KM10", "KM"), ("GMM10", "GMM"), ("FCM10", "FCM")):
            feats, _ = segment_features(algo, rfm, rfm, 10)
            labels = feats.argmax(axis=1)
            seg = cluster_segments(labels, quint)
            summary.append({"dataset": name, "method": method, "n_segments": len(seg),
                            "fidelity_f1": weighted(seg, "f1"), "description_length": weighted(seg, "length"),
                            "coverage": 1.0, "overlap": 1.0, "n_rules_conf60": 0,
                            "rule_mean_confidence": np.nan, "rule_share_conf80": np.nan,
                            "softness": float(feats.max(axis=1).mean()), "boundary_customers": boundary})
        print(name, "done", flush=True)

    out = pd.DataFrame(summary)
    out.to_csv(OUT / "summary.csv", index=False)
    pd.concat(rule_rows).to_csv(OUT / "rules.csv", index=False)
    print(out.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
