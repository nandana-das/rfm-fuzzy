"""Plan addendum B: confirmation of the Online Retail II findings on CDNOW.

Writes results/cdnow/*.csv.
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
from rfmfca.cdnow import load_cdnow  # noqa: E402
from rfmfca.evaluation import MIN_SUPPORT, build_features, holm, metric, paired_bootstrap  # noqa: E402
from rfmfca.fuzzy import ATTRIBUTES, FuzzyConceptLattice, RankScaler, crisp_context, fuzzy_context  # noqa: E402
from rfmfca.rfm import compute_rfm  # noqa: E402

OUT = ROOT / "results" / "cdnow"
CUTOFFS = ["1997-07-01", "1997-10-01", "1998-01-01", "1998-04-01"]
METHODS = ("C-ctx", "C-fca", "F-ctx", "F-fca-core", "F-fca-G-core", "logRFM")
LATTICES = {"C-fca": ("crisp", 2, "lukasiewicz", "sigma"),
            "F-fca-core": ("fuzzy", 3, "lukasiewicz", "core"),
            "F-fca-G-core": ("fuzzy", 3, "godel", "core")}
CONFIRMATORY = [("B1a", "fixed", "F-ctx", "C-ctx", "auc"), ("B1b", "fixed", "F-ctx", "C-ctx", "r2"),
                ("B2a", "tuned", "F-fca-core", "C-fca", "auc"), ("B2b", "tuned", "F-fca-core", "C-fca", "r2"),
                ("B3", "tuned", "F-fca-core", "F-ctx", "r2")]
N_REPLICATES, DROP_P, N_BOOT, SEED = 20, 0.05, 50, 0


def contexts(rfm):
    u = RankScaler().fit(rfm).transform(rfm)
    return {"crisp": crisp_context(u), "fuzzy": fuzzy_context(u, n_levels=3)}


def lattice(ctx, method):
    kind, n_levels, residuum, support = LATTICES[method]
    lat = FuzzyConceptLattice(ctx[kind], n_levels, residuum)
    return lat, lat.frequent(MIN_SUPPORT, support)


def prediction(tx):
    settings = {"fixed": planned.model, "tuned": tuned.model}
    per_origin, info_rows, occupancy = [], [], []
    oof_all = {s: {t: [] for t in planned.TARGETS.values()} for s in settings}
    for cutoff in CUTOFFS:
        data = planned.origin_frame(tx, cutoff)
        ctx = contexts(data)
        for kind, c in ctx.items():
            full = (c == (1 if kind == "crisp" else 2)).sum()
            part = (c == 1).sum() if kind == "fuzzy" else pd.Series(0, index=ATTRIBUTES)
            occupancy += [{"cutoff": cutoff, "context": kind, "attribute": a,
                           "full": int(full[a]), "partial": int(part[a])} for a in ATTRIBUTES]
        oof = {s: {t: pd.DataFrame({"y": data[t].to_numpy()}, index=data.index)
                   for t in planned.TARGETS.values()} for s in settings}
        folds = KFold(planned.N_FOLDS, shuffle=True, random_state=planned.SEED)
        for fold, (tr, te) in enumerate(folds.split(data)):
            train, test = data.iloc[tr], data.iloc[te]
            for m, (x_tr, x_te, info) in build_features(train, test, METHODS).items():
                info_rows.append({"cutoff": cutoff, "fold": fold, "method": m, "n_features": x_tr.shape[1], **info})
                for s, make in settings.items():
                    for t in planned.TARGETS.values():
                        est = make(t).fit(x_tr, train[t])
                        oof[s][t].loc[test.index, m] = (est.predict_proba(x_te)[:, 1] if t == "buy"
                                                        else est.predict(x_te))
        for s in settings:
            for metric_name, t in planned.TARGETS.items():
                oof_all[s][t].append(oof[s][t])
                for m in METHODS:
                    per_origin.append({"setting": s, "cutoff": cutoff, "metric": metric_name, "method": m,
                                       "value": metric(metric_name, oof[s][t]["y"], oof[s][t][m]),
                                       "n_customers": len(data), "positive_rate": data["buy"].mean()})
        print("prediction", cutoff, len(data), flush=True)

    pd.DataFrame(occupancy).to_csv(OUT / "band_occupancy.csv", index=False)
    pd.DataFrame(info_rows).to_csv(OUT / "prediction_feature_counts.csv", index=False)
    per_origin = pd.DataFrame(per_origin)
    per_origin.to_csv(OUT / "prediction_per_origin.csv", index=False)

    pairs = [("F-ctx", "C-ctx"), ("F-fca-core", "C-fca"), ("F-fca-core", "F-ctx"), ("F-fca-G-core", "C-fca"),
             ("F-fca-G-core", "F-ctx"), ("C-fca", "C-ctx")] + [(m, "logRFM") for m in METHODS if m != "logRFM"]
    rows = [{"setting": s, **paired_bootstrap(oof_all[s][t], mn, a, b)}
            for s in settings for mn, t in planned.TARGETS.items() for a, b in pairs]
    comp = pd.DataFrame(rows)
    comp["claim"] = ""
    for claim, s, a, b, mn in CONFIRMATORY:
        comp.loc[(comp.setting == s) & (comp.a == a) & (comp.b == b) & (comp.metric == mn), "claim"] = claim
    conf = comp.claim != ""
    comp["p_holm"] = np.nan
    comp.loc[conf, "p_holm"] = holm(comp.loc[conf, "p_value"])
    comp["replicates"] = np.where(conf, (comp.pooled_diff > 0) & (comp.p_holm < 0.05), np.nan)
    comp.to_csv(OUT / "prediction_comparisons.csv", index=False)
    print(per_origin.pivot_table(index=["setting", "method"], columns="metric", values="value").round(4).to_string())
    print(comp[["claim", "setting", "a", "b", "metric", "pooled_diff", "ci_low", "ci_high", "p_value",
                "p_holm", "origins_a_better", "replicates"]].round(4).to_string(index=False))


def robustness(tx):
    ref_date = tx["InvoiceDate"].max()
    base_rfm = compute_rfm(tx, ref_date)
    base_ctx = contexts(base_rfm)
    base = {}
    for m in LATTICES:
        lat, idx = lattice(base_ctx, m)
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
        row = {"replicate": rep, "customers": len(common)}
        for kind, scale in (("crisp", 1), ("fuzzy", 2)):
            a = base_ctx[kind].loc[common].to_numpy(float) / scale
            b = ctx[kind].loc[common].to_numpy(float) / scale
            row[f"context_change_{kind}"] = np.abs(a - b).sum(axis=1).mean() / 6
            row[f"share_any_change_{kind}"] = (np.abs(a - b).sum(axis=1) > 0).mean()
        for m, (kind, lat, intents, base_deg) in base.items():
            row[f"concept_change_{m}"] = np.abs(lat.degrees(ctx[kind].loc[common].to_numpy(), intents)
                                                - base_deg[pos]).mean()
        rows.append(row)
    reps = pd.DataFrame(rows)
    reps.to_csv(OUT / "robustness_replicates.csv", index=False)
    claims = pd.DataFrame([
        {"claim": "B4a", "measure": "context change F-ctx vs C-ctx",
         "fuzzy_mean": reps.context_change_fuzzy.mean(), "crisp_mean": reps.context_change_crisp.mean(),
         "replicates_fuzzy_lower": int((reps.context_change_fuzzy < reps.context_change_crisp).sum())},
        {"claim": "B4b", "measure": "concept change F-fca-core vs C-fca",
         "fuzzy_mean": reps["concept_change_F-fca-core"].mean(), "crisp_mean": reps["concept_change_C-fca"].mean(),
         "replicates_fuzzy_lower": int((reps["concept_change_F-fca-core"] < reps["concept_change_C-fca"]).sum())},
    ])
    claims["n_replicates"] = len(reps)
    claims["replicates"] = claims.replicates_fuzzy_lower == len(reps)
    claims.to_csv(OUT / "robustness_claims.csv", index=False)
    print(reps.mean().round(5).to_string())
    print(claims.to_string(index=False), flush=True)


def structure(tx):
    rfm = compute_rfm(tx)
    ctx = contexts(rfm)
    sizes, full_sets = [], {}
    for m in LATTICES:
        lat, idx = lattice(ctx, m)
        full_sets[m] = {tuple(r) for r in lat.intents[idx]}
        lat.table(idx).sort_values("core_support", ascending=False).to_csv(OUT / f"frequent_concepts_{m}.csv",
                                                                         index=False)
        rules = lat.induced_cover_rules(idx, 0.60)
        rules.to_csv(OUT / f"rules_conf60_{m}.csv", index=False)
        sizes.append({"method": m, "n_concepts": len(lat.intents), "n_frequent": len(idx),
                      "n_rules_conf60": len(rules),
                      "mean_intent_size": float((lat.intents[idx].sum(axis=1) / lat.top).mean())})
    pd.DataFrame(sizes).to_csv(OUT / "structure_size.csv", index=False)
    print(pd.DataFrame(sizes).to_string(index=False), flush=True)
    rng = np.random.default_rng(SEED)
    rows = []
    for b in range(N_BOOT):
        sample = rfm.iloc[rng.integers(0, len(rfm), len(rfm))]
        sample = sample.set_axis(np.arange(len(sample)))
        sctx = contexts(sample)
        row = {"bootstrap": b}
        for m in LATTICES:
            lat, idx = lattice(sctx, m)
            s = {tuple(r) for r in lat.intents[idx]}
            row[f"jaccard_{m}"] = len(s & full_sets[m]) / len(s | full_sets[m])
        rows.append(row)
    boots = pd.DataFrame(rows)
    boots.to_csv(OUT / "structure_bootstrap.csv", index=False)
    print(boots.drop(columns="bootstrap").describe().round(4).to_string(), flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tx = load_cdnow()
    structure(tx)
    robustness(tx)
    prediction(tx)


if __name__ == "__main__":
    main()
