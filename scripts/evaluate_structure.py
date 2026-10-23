"""H3: size and bootstrap stability of crisp vs fuzzy concept structures, plus the
full-data fuzzy concepts and rules (docs/EXTENSION_PLAN.md, H3).

Writes results/extension/structure_*.csv and fuzzy concept / rule tables.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rfmfca.data import clean_transactions, load_transactions  # noqa: E402
from rfmfca.evaluation import LATTICE_SPECS, MIN_SUPPORT  # noqa: E402
from rfmfca.fuzzy import FuzzyConceptLattice, RankScaler, crisp_context, fuzzy_context  # noqa: E402
from rfmfca.rfm import compute_rfm  # noqa: E402

OUT = ROOT / "results" / "extension"
N_BOOT, SEED, MIN_CONFIDENCE = 50, 0, 0.60


def lattice_for(rfm, method):
    kind, n_levels, residuum = LATTICE_SPECS[method]
    u = RankScaler().fit(rfm).transform(rfm)
    ctx = crisp_context(u) if kind == "crisp" else fuzzy_context(u, n_levels=3)
    return FuzzyConceptLattice(ctx, n_levels, residuum), ctx


def frequent_set(lat):
    return {tuple(r) for r in lat.intents[lat.frequent(MIN_SUPPORT)]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tx = clean_transactions(load_transactions())
    rfm = compute_rfm(tx)

    size_rows, full_sets = [], {}
    for method in LATTICE_SPECS:
        lat, ctx = lattice_for(rfm, method)
        idx = lat.frequent(MIN_SUPPORT)
        rules = lat.association_rules(MIN_CONFIDENCE)
        full_sets[method] = frequent_set(lat)
        table = lat.table(idx).sort_values("support", ascending=False)
        table.to_csv(OUT / f"structure_frequent_concepts_{method}.csv", index=False)
        rules.to_csv(OUT / f"structure_rules_conf60_{method}.csv", index=False)
        size_rows.append({
            "method": method, "n_concepts": len(lat.intents), "n_frequent": len(idx),
            "n_rules_conf60": len(rules),
            "mean_intent_size_frequent": float(table["intent_size"].mean()),
            "share_customers_partial_membership":
                float((ctx.to_numpy() == 1).any(axis=1).mean()) if method != "C-fca" else 0.0,
        })
        print(size_rows[-1], flush=True)
    pd.DataFrame(size_rows).to_csv(OUT / "structure_size.csv", index=False)

    rng = np.random.default_rng(SEED)
    boot_rows = []
    for b in range(N_BOOT):
        sample = rfm.iloc[rng.integers(0, len(rfm), len(rfm))]
        sample = sample.set_axis(np.arange(len(sample)))     # duplicates become distinct objects
        row = {"bootstrap": b}
        for method in LATTICE_SPECS:
            s = frequent_set(lattice_for(sample, method)[0])
            full = full_sets[method]
            row[f"jaccard_{method}"] = len(s & full) / len(s | full)
            row[f"n_frequent_{method}"] = len(s)
        boot_rows.append(row)
        print(b, row, flush=True)
    boots = pd.DataFrame(boot_rows)
    boots.to_csv(OUT / "structure_bootstrap.csv", index=False)
    print(boots.drop(columns="bootstrap").describe().round(4).to_string())


if __name__ == "__main__":
    main()
