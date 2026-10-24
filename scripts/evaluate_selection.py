"""Plan addendum J: summary view of K selected concepts.

Usage: python scripts/evaluate_selection.py {retail|cdnow|dunnhumby}
Writes results/selection/<dataset>_*.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_clustering as clu  # noqa: E402
import evaluate_prediction as planned  # noqa: E402
import posthoc_tuned_regularization as tuned  # noqa: E402
from evaluate_hybrid import dataset  # noqa: E402
from rfmfca.evaluation import MIN_SUPPORT, SELECTED, build_features, holm, metric, paired_bootstrap  # noqa: E402
from rfmfca.fuzzy import FuzzyConceptLattice, RankScaler, crisp_context, fuzzy_context, select_concepts  # noqa: E402
from rfmfca.rfm import compute_rfm  # noqa: E402

OUT = ROOT / "results" / "selection"
PRED_METHODS = ("F-sel10", "F-sel20", "C-sel10", "C-sel20", "KM10", "GMM10", "FCM10", "F-fca-core", "C-fca")
STRUCT_METHODS = ("F-sel10", "C-sel10", "F-sel20", "C-sel20", "KM10", "GMM10", "FCM10")
TESTS = [("S1", "F-sel10", "C-sel10"), ("S2", "F-sel10", "FCM10")]


def prediction(name, tx, cutoffs):
    per_origin, oof_all = [], {t: [] for t in planned.TARGETS.values()}
    for cutoff in cutoffs:
        data = planned.origin_frame(tx, cutoff)
        oof = {t: pd.DataFrame({"y": data[t].to_numpy()}, index=data.index) for t in planned.TARGETS.values()}
        for tr, te in KFold(planned.N_FOLDS, shuffle=True, random_state=planned.SEED).split(data):
            train, test = data.iloc[tr], data.iloc[te]
            for m, (x_tr, x_te, _) in build_features(train, test, PRED_METHODS).items():
                for t in planned.TARGETS.values():
                    est = tuned.model(t).fit(x_tr, train[t])
                    oof[t].loc[test.index, m] = est.predict_proba(x_te)[:, 1] if t == "buy" else est.predict(x_te)
        for mn, t in planned.TARGETS.items():
            oof_all[t].append(oof[t])
            for m in PRED_METHODS:
                per_origin.append({"cutoff": cutoff, "metric": mn, "method": m,
                                   "value": metric(mn, oof[t]["y"], oof[t][m])})
        print(name, "prediction", cutoff, flush=True)
    per_origin = pd.DataFrame(per_origin)
    per_origin.to_csv(OUT / f"{name}_prediction_per_origin.csv", index=False)
    pairs = [(a, b) for _, a, b in TESTS] + [("F-sel10", b) for b in ("KM10", "GMM10", "F-fca-core")]
    pairs += [("F-sel20", b) for b in ("C-sel20", "FCM10", "F-fca-core")]
    comp = pd.DataFrame([paired_bootstrap(oof_all[t], mn, a, b) for a, b in pairs for mn, t in planned.TARGETS.items()])
    comp.insert(0, "dataset", name)
    comp["test"] = ""
    for test, a, b in TESTS:
        comp.loc[(comp.a == a) & (comp.b == b), "test"] = test
    sel = comp.test != ""
    comp["p_holm"] = np.nan
    comp.loc[sel, "p_holm"] = holm(comp.loc[sel, "p_value"])
    comp.to_csv(OUT / f"{name}_prediction_comparisons.csv", index=False)
    print(per_origin.pivot_table(index="method", columns="metric", values="value").round(4).to_string())
    print(comp[["test", "a", "b", "metric", "pooled_diff", "ci_low", "ci_high", "p_holm",
                "origins_a_better"]].round(4).to_string(index=False), flush=True)


def summary_view(name, tx):
    """The selected concepts on the full data, with interpretability proxies."""
    rfm = compute_rfm(tx, tx["InvoiceDate"].max())
    u = RankScaler().fit(rfm).transform(rfm)
    ctxs = {"crisp": crisp_context(u), "fuzzy": fuzzy_context(u)}
    concept_rows, proxy_rows = [], []
    for method, (kind, n_levels, support_kind, k) in SELECTED.items():
        ctx = ctxs[kind]
        lat = FuzzyConceptLattice(ctx, n_levels, "lukasiewicz")
        chosen = select_concepts(lat, lat.frequent(MIN_SUPPORT, support_kind), k)
        q = ctx.to_numpy()
        full = lat.degrees(q, lat.intents[chosen]) >= 1
        mass = lat.intents[chosen].sum(axis=1) / lat.top
        explained = (full * mass).max(axis=1)
        spend = rfm["amount"].to_numpy()
        for rank, (i, col) in enumerate(zip(chosen, full.T), start=1):
            concept_rows.append({"method": method, "rank": rank, "intent": lat.label(lat.intents[i]),
                                 "core_share": float(col.mean()), "mean_spend_members": float(spend[col].mean()),
                                 "share_of_total_spend": float(spend[col].sum() / spend.sum())})
        covered = full.any(axis=1)
        proxy_rows.append({"method": method, "n_segments": len(chosen), "coverage": float(covered.mean()),
                           "overlap": float(full[covered].sum(axis=1).mean()),
                           "explained_mass_share": float(explained.mean() / 3),
                           "description_length": float(np.average(
                               [sum(int(lat.intents[i][5 * d:5 * d + 5].any()) for d in range(3)) for i in chosen],
                               weights=full.sum(axis=0) + 1e-12))})
    pd.DataFrame(concept_rows).to_csv(OUT / f"{name}_selected_concepts.csv", index=False)
    pd.DataFrame(proxy_rows).to_csv(OUT / f"{name}_proxies.csv", index=False)
    print(pd.DataFrame(proxy_rows).round(3).to_string(index=False), flush=True)


def main(name):
    OUT.mkdir(parents=True, exist_ok=True)
    tx, cutoffs = dataset(name)
    summary_view(name, tx)
    clu.OUT = OUT
    clu.structure(name, tx, STRUCT_METHODS, "_sel")
    prediction(name, tx, cutoffs)


if __name__ == "__main__":
    main(sys.argv[1])
