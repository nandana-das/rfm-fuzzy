"""Plan addendum A: fuzzy concepts filtered by core support (docs/EXTENSION_PLAN.md).

A1 prediction (fixed and tuned regularisation), A2 robustness, A3 structure.
Writes results/extension/core_*.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_prediction as planned  # noqa: E402
import posthoc_tuned_regularization as tuned  # noqa: E402
from rfmfca.data import clean_transactions, load_transactions  # noqa: E402
from rfmfca.evaluation import (CORE_METHODS, CORE_SPECS, MIN_SUPPORT, build_features, holm,  # noqa: E402
                               metric, paired_bootstrap)
from rfmfca.fuzzy import FuzzyConceptLattice, RankScaler, crisp_context, fuzzy_context  # noqa: E402
from rfmfca.rfm import compute_rfm  # noqa: E402

OUT = ROOT / "results" / "extension"
LATTICES = {"C-fca": ("crisp", 2, "lukasiewicz"), **CORE_SPECS}   # crisp core support == support
N_REPLICATES, DROP_P, N_BOOT, SEED = 20, 0.05, 50, 0


def contexts(rfm):
    u = RankScaler().fit(rfm).transform(rfm)
    return {"crisp": crisp_context(u), "fuzzy": fuzzy_context(u, n_levels=3)}


def core_lattice(ctx, method):
    kind, n_levels, residuum = LATTICES[method]
    lat = FuzzyConceptLattice(ctx[kind], n_levels, residuum)
    return lat, lat.frequent(MIN_SUPPORT, "core")


# -- A1 -----------------------------------------------------------------------

def a1_prediction(tx):
    settings = {"fixed": planned.model, "tuned": tuned.model}
    per_origin, oof_all, info_rows = [], {s: {t: [] for t in planned.TARGETS.values()} for s in settings}, []
    for cutoff in planned.CUTOFFS:
        data = planned.origin_frame(tx, cutoff)
        oof = {s: {t: pd.DataFrame({"y": data[t].to_numpy()}, index=data.index)
                   for t in planned.TARGETS.values()} for s in settings}
        folds = KFold(planned.N_FOLDS, shuffle=True, random_state=planned.SEED)
        for fold, (tr, te) in enumerate(folds.split(data)):
            train, test = data.iloc[tr], data.iloc[te]
            for m, (x_tr, x_te, info) in build_features(train, test, CORE_METHODS).items():
                info_rows.append({"cutoff": cutoff, "fold": fold, "method": m, "n_features": x_tr.shape[1], **info})
                for s, make in settings.items():
                    for t in planned.TARGETS.values():
                        est = make(t).fit(x_tr, train[t])
                        oof[s][t].loc[test.index, m] = (est.predict_proba(x_te)[:, 1] if t == "buy"
                                                        else est.predict(x_te))
        for s in settings:
            for metric_name, t in planned.TARGETS.items():
                oof_all[s][t].append(oof[s][t])
                for m in CORE_METHODS:
                    per_origin.append({"setting": s, "cutoff": cutoff, "metric": metric_name, "method": m,
                                       "value": metric(metric_name, oof[s][t]["y"], oof[s][t][m])})
        print("A1", cutoff, flush=True)

    pd.DataFrame(per_origin).to_csv(OUT / "core_prediction_per_origin.csv", index=False)
    pd.DataFrame(info_rows).to_csv(OUT / "core_prediction_feature_counts.csv", index=False)
    pairs = [("F-fca-core", "C-fca"), ("F-fca-core", "F-ctx"), ("F-fca-G-core", "C-fca"),
             ("F-fca-G-core", "F-ctx"), ("F-ctx", "C-ctx"), ("C-fca", "C-ctx")]
    rows = []
    for s in settings:
        for metric_name, t in planned.TARGETS.items():
            for a, b in pairs:
                rows.append({"setting": s, **paired_bootstrap(oof_all[s][t], metric_name, a, b)})
    comp = pd.DataFrame(rows)
    primary = (comp.setting == "fixed") & (comp.a == "F-fca-core") & (comp.b == "C-fca")
    comp["primary"] = primary
    comp["p_holm"] = np.nan
    comp.loc[primary, "p_holm"] = holm(comp.loc[primary, "p_value"])
    comp.to_csv(OUT / "core_prediction_comparisons.csv", index=False)
    print(pd.DataFrame(per_origin).pivot_table(index=["setting", "method"], columns="metric",
                                               values="value").round(4).to_string())
    print(comp[["setting", "a", "b", "metric", "pooled_diff", "ci_low", "ci_high", "p_value", "p_holm",
                "origins_a_better"]].round(4).to_string(index=False))


# -- A2 -----------------------------------------------------------------------

def a2_robustness(tx):
    ref_date = tx["InvoiceDate"].max()
    base_rfm = compute_rfm(tx, ref_date)
    base_ctx = contexts(base_rfm)
    base = {}
    for m in LATTICES:
        lat, idx = core_lattice(base_ctx, m)
        kind = LATTICES[m][0]
        base[m] = (kind, lat, lat.intents[idx], lat.degrees(base_ctx[kind].to_numpy(), lat.intents[idx]))
    rng = np.random.default_rng(SEED)
    invoices = tx["InvoiceNo"].unique()
    rows = []
    for rep in range(N_REPLICATES):
        keep = set(invoices[rng.random(len(invoices)) >= DROP_P])
        rfm = compute_rfm(tx[tx["InvoiceNo"].isin(keep)], ref_date)
        common = base_rfm.index.intersection(rfm.index)
        pos = base_rfm.index.get_indexer(common)
        ctx = contexts(rfm)
        row = {"replicate": rep}
        for m, (kind, lat, intents, base_deg) in base.items():
            deg = lat.degrees(ctx[kind].loc[common].to_numpy(), intents)
            row[f"concept_change_{m}"] = np.abs(deg - base_deg[pos]).mean()
        rows.append(row)
    reps = pd.DataFrame(rows)
    reps.to_csv(OUT / "core_robustness_replicates.csv", index=False)
    d = reps["concept_change_F-fca-core"] - reps["concept_change_C-fca"]
    print("A2", reps.mean().round(5).to_dict(), "fuzzy lower in", int((d < 0).sum()), "/", len(d), flush=True)


# -- A3 -----------------------------------------------------------------------

def a3_structure(tx):
    rfm = compute_rfm(tx)
    ctx = contexts(rfm)
    sizes, full_sets = [], {}
    for m in LATTICES:
        lat, idx = core_lattice(ctx, m)
        full_sets[m] = {tuple(r) for r in lat.intents[idx]}
        lat.table(idx).sort_values("core_support", ascending=False).to_csv(
            OUT / f"core_frequent_concepts_{m}.csv", index=False)
        rules = lat.induced_cover_rules(idx, 0.60)
        rules.to_csv(OUT / f"core_rules_conf60_{m}.csv", index=False)
        sizes.append({"method": m, "n_concepts": len(lat.intents), "n_core_frequent": len(idx),
                      "n_rules_conf60": len(rules),
                      "mean_intent_size": float((lat.intents[idx].sum(axis=1) / lat.top).mean()),
                      "share_intents_with_partial_term": float((lat.intents[idx] == 1).any(axis=1).mean())
                      if LATTICES[m][1] == 3 else 0.0})
    same = full_sets["F-fca-core"] == full_sets["F-fca-G-core"]
    for row in sizes:
        row["lukasiewicz_and_godel_core_sets_identical"] = same
    pd.DataFrame(sizes).to_csv(OUT / "core_structure_size.csv", index=False)
    print("A3", pd.DataFrame(sizes).to_string(index=False), flush=True)

    rng = np.random.default_rng(SEED)
    rows = []
    for b in range(N_BOOT):
        sample = rfm.iloc[rng.integers(0, len(rfm), len(rfm))]
        sample = sample.set_axis(np.arange(len(sample)))
        sctx = contexts(sample)
        row = {"bootstrap": b}
        for m in LATTICES:
            lat, idx = core_lattice(sctx, m)
            s = {tuple(r) for r in lat.intents[idx]}
            row[f"jaccard_{m}"] = len(s & full_sets[m]) / len(s | full_sets[m])
            row[f"n_core_frequent_{m}"] = len(s)
        rows.append(row)
    boots = pd.DataFrame(rows)
    boots.to_csv(OUT / "core_structure_bootstrap.csv", index=False)
    print("A3 bootstrap", boots.drop(columns="bootstrap").describe().round(4).to_string(), flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tx = clean_transactions(load_transactions())
    a3_structure(tx)
    a2_robustness(tx)
    a1_prediction(tx)


if __name__ == "__main__":
    main()
