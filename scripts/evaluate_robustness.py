"""H2: how much crisp vs fuzzy memberships move when 5 % of invoices are dropped.

Writes results/extension/robustness_*.csv (docs/EXTENSION_PLAN.md, H2).
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
N_REPLICATES, DROP_P, SEED = 20, 0.05, 0


def contexts(rfm):
    u = RankScaler().fit(rfm).transform(rfm)
    return {"crisp": crisp_context(u), "fuzzy": fuzzy_context(u, n_levels=3)}


def degrees_of(ctx, kind):
    """Context as membership degrees in [0, 1]."""
    return ctx.to_numpy(float) / (1 if kind == "crisp" else 2)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tx = clean_transactions(load_transactions())
    ref_date = tx["InvoiceDate"].max()
    base_rfm = compute_rfm(tx, ref_date)
    base_ctx = contexts(base_rfm)

    lattices = {}
    for method, (kind, n_levels, residuum) in LATTICE_SPECS.items():
        lat = FuzzyConceptLattice(base_ctx[kind], n_levels, residuum)
        intents = lat.intents[lat.frequent(MIN_SUPPORT)]
        lattices[method] = (kind, lat, intents, lat.degrees(base_ctx[kind].to_numpy(), intents))

    rng = np.random.default_rng(SEED)
    invoices = tx["InvoiceNo"].unique()
    rows = []
    for rep in range(N_REPLICATES):
        keep = set(invoices[rng.random(len(invoices)) >= DROP_P])
        rfm = compute_rfm(tx[tx["InvoiceNo"].isin(keep)], ref_date)
        common = base_rfm.index.intersection(rfm.index)
        ctx = contexts(rfm)
        row = {"replicate": rep, "customers": len(common)}
        for kind in ("crisp", "fuzzy"):
            a = degrees_of(base_ctx[kind].loc[common], kind)
            b = degrees_of(ctx[kind].loc[common], kind)
            # Total-variation distance per dimension, averaged over R, F, M:
            # 0 = unchanged, 1 = every dimension moved entirely to other terms.
            row[f"context_change_{kind}"] = np.abs(a - b).sum(axis=1).mean() / 6
            row[f"share_any_change_{kind}"] = (np.abs(a - b).sum(axis=1) > 0).mean()
        crisp_now = ctx["crisp"].loc[common].to_numpy()
        row["share_crisp_cell_changed"] = (crisp_now != base_ctx["crisp"].loc[common].to_numpy()).any(axis=1).mean()
        pos = base_rfm.index.get_indexer(common)
        for method, (kind, lat, intents, base_deg) in lattices.items():
            deg = lat.degrees(ctx[kind].loc[common].to_numpy(), intents)
            row[f"concept_change_{method}"] = np.abs(deg - base_deg[pos]).mean()
        rows.append(row)
        print(rep, {k: round(v, 4) for k, v in row.items() if k != "replicate"}, flush=True)

    reps = pd.DataFrame(rows)
    reps.to_csv(OUT / "robustness_replicates.csv", index=False)
    d = reps["context_change_fuzzy"] - reps["context_change_crisp"]
    summary = pd.DataFrame([{
        "context_change_crisp_mean": reps["context_change_crisp"].mean(),
        "context_change_fuzzy_mean": reps["context_change_fuzzy"].mean(),
        "diff_mean": d.mean(), "diff_min": d.min(), "diff_max": d.max(),
        "replicates_fuzzy_lower": int((d < 0).sum()), "n_replicates": len(d),
        "share_crisp_cell_changed_mean": reps["share_crisp_cell_changed"].mean(),
        **{f"{c}_mean": reps[c].mean() for c in reps.columns if c.startswith("concept_change")},
    }])
    summary.to_csv(OUT / "robustness_summary.csv", index=False)
    print(summary.T.round(5).to_string())


if __name__ == "__main__":
    main()
