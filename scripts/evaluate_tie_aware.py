"""Plan addendum C: tie-aware fuzzy memberships, evaluated on CDNOW.

Also checks that the variant is a no-op on Online Retail II at every origin and fold.
Writes results/tie_aware/*.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import confirm_cdnow as cd  # noqa: E402
import evaluate_prediction as planned  # noqa: E402
import posthoc_tuned_regularization as tuned  # noqa: E402
from rfmfca.cdnow import load_cdnow  # noqa: E402
from rfmfca.data import clean_transactions, load_transactions  # noqa: E402
from rfmfca.evaluation import MIN_SUPPORT, build_features, holm, metric, paired_bootstrap  # noqa: E402
from rfmfca.fuzzy import (FuzzyConceptLattice, RankScaler, crisp_context, fuzzy_context,  # noqa: E402
                          tie_aware_fuzzy_context)
from rfmfca.rfm import compute_rfm  # noqa: E402

OUT = ROOT / "results" / "tie_aware"
METHODS = ("C-ctx", "C-fca", "F-ctx", "F-ctx-T", "F-fca-core", "F-fca-core-T", "F-fca-G-core-T", "logRFM")
LATTICES = {"C-fca": ("crisp", 2, "lukasiewicz"),
            "F-fca-core": ("fuzzy", 3, "lukasiewicz"),
            "F-fca-core-T": ("fuzzy-tie", 3, "lukasiewicz"),
            "F-fca-G-core-T": ("fuzzy-tie", 3, "godel")}
TESTS = [("C1a", "fixed", "F-ctx-T", "F-ctx", "auc"), ("C1b", "fixed", "F-ctx-T", "F-ctx", "r2"),
         ("C2a", "tuned", "F-fca-core-T", "F-fca-core", "auc"), ("C2b", "tuned", "F-fca-core-T", "F-fca-core", "r2")]
N_REPLICATES, DROP_P, N_BOOT, SEED = 20, 0.05, 50, 0
F_POSITIONS = range(5, 10)   # F1..F5 in the 15-attribute order


def contexts(rfm):
    sc = RankScaler().fit(rfm)
    u = sc.transform(rfm)
    return {"crisp": crisp_context(u), "fuzzy": fuzzy_context(u, n_levels=3),
            "fuzzy-tie": tie_aware_fuzzy_context(sc.transform_intervals(rfm), n_levels=3)}


def lattice(ctx, method):
    kind, n_levels, residuum = LATTICES[method]
    lat = FuzzyConceptLattice(ctx[kind], n_levels, residuum)
    return lat, lat.frequent(MIN_SUPPORT, "core")


def is_tie_artifact(row):
    """Consequent only raises one F term from 1/2 to 1, with (near-)certain confidence."""
    p = np.array(list(row.premise_levels), int)
    q = np.array(list(row.consequent_levels), int)
    diff = np.flatnonzero(p != q)
    return (len(diff) == 1 and diff[0] in F_POSITIONS and p[diff[0]] == 1 and q[diff[0]] == 2
            and row.confidence >= 0.999)


def retail_identity():
    tx = clean_transactions(load_transactions())
    rows = []
    for cutoff in planned.CUTOFFS:
        data = planned.origin_frame(tx, cutoff)
        for fold, (tr, te) in enumerate(KFold(planned.N_FOLDS, shuffle=True, random_state=planned.SEED).split(data)):
            train, test = data.iloc[tr], data.iloc[te]
            sc = RankScaler().fit(train)
            for part, frame in (("train", train), ("test", test)):
                plain = fuzzy_context(sc.transform(frame))
                tie = tie_aware_fuzzy_context(sc.transform_intervals(frame))
                rows.append({"cutoff": cutoff, "fold": fold, "part": part,
                             "share_customers_changed": float((plain != tie).any(axis=1).mean())})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "retail_identity_check.csv", index=False)
    print("retail identity: max share changed =", out.share_customers_changed.max(), flush=True)


def structure(tx):
    rfm = compute_rfm(tx)
    ctx = contexts(rfm)
    sizes, full_sets = [], {}
    for m in LATTICES:
        lat, idx = lattice(ctx, m)
        full_sets[m] = {tuple(r) for r in lat.intents[idx]}
        rules = lat.induced_cover_rules(idx, 0.60)
        rules["tie_artifact"] = rules.apply(is_tie_artifact, axis=1) if len(rules) else []
        rules.to_csv(OUT / f"rules_conf60_{m}.csv", index=False)
        lat.table(idx).sort_values("core_support", ascending=False).to_csv(OUT / f"frequent_concepts_{m}.csv",
                                                                         index=False)
        sizes.append({"method": m, "n_concepts": len(lat.intents), "n_frequent": len(idx),
                      "n_rules_conf60": len(rules), "n_tie_artifact_rules": int(rules["tie_artifact"].sum())})
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
        row = {"replicate": rep}
        for kind, scale in (("crisp", 1), ("fuzzy", 2), ("fuzzy-tie", 2)):
            a = base_ctx[kind].loc[common].to_numpy(float) / scale
            b = ctx[kind].loc[common].to_numpy(float) / scale
            row[f"context_change_{kind}"] = np.abs(a - b).sum(axis=1).mean() / 6
        for m, (kind, lat, intents, base_deg) in base.items():
            row[f"concept_change_{m}"] = np.abs(lat.degrees(ctx[kind].loc[common].to_numpy(), intents)
                                                - base_deg[pos]).mean()
        rows.append(row)
    reps = pd.DataFrame(rows)
    reps.to_csv(OUT / "robustness_replicates.csv", index=False)
    print(reps.mean().round(5).to_string(), flush=True)
    print("tie-aware context lower in", int((reps["context_change_fuzzy-tie"] < reps.context_change_fuzzy).sum()),
          "/ 20; concept lower in",
          int((reps["concept_change_F-fca-core-T"] < reps["concept_change_F-fca-core"]).sum()), "/ 20", flush=True)


def prediction(tx):
    settings = {"fixed": planned.model, "tuned": tuned.model}
    per_origin, info_rows = [], []
    oof_all = {s: {t: [] for t in planned.TARGETS.values()} for s in settings}
    for cutoff in cd.CUTOFFS:
        data = planned.origin_frame(tx, cutoff)
        oof = {s: {t: pd.DataFrame({"y": data[t].to_numpy()}, index=data.index)
                   for t in planned.TARGETS.values()} for s in settings}
        for fold, (tr, te) in enumerate(KFold(planned.N_FOLDS, shuffle=True, random_state=planned.SEED).split(data)):
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
                                       "value": metric(metric_name, oof[s][t]["y"], oof[s][t][m])})
        print("prediction", cutoff, flush=True)
    per_origin = pd.DataFrame(per_origin)
    per_origin.to_csv(OUT / "prediction_per_origin.csv", index=False)
    pd.DataFrame(info_rows).to_csv(OUT / "prediction_feature_counts.csv", index=False)
    pairs = [("F-ctx-T", "F-ctx"), ("F-fca-core-T", "F-fca-core"), ("F-fca-G-core-T", "F-fca-core"),
             ("F-ctx-T", "C-ctx"), ("F-fca-core-T", "C-fca"), ("F-fca-core-T", "F-ctx-T")]
    pairs += [(m, "logRFM") for m in METHODS if m != "logRFM"]
    comp = pd.DataFrame([{"setting": s, **paired_bootstrap(oof_all[s][t], mn, a, b)}
                         for s in settings for mn, t in planned.TARGETS.items() for a, b in pairs])
    comp["test"] = ""
    for name, s, a, b, mn in TESTS:
        comp.loc[(comp.setting == s) & (comp.a == a) & (comp.b == b) & (comp.metric == mn), "test"] = name
    sel = comp.test != ""
    comp["p_holm"] = np.nan
    comp.loc[sel, "p_holm"] = holm(comp.loc[sel, "p_value"])
    comp.to_csv(OUT / "prediction_comparisons.csv", index=False)
    print(per_origin.pivot_table(index=["setting", "method"], columns="metric", values="value").round(4).to_string())
    print(comp[["test", "setting", "a", "b", "metric", "pooled_diff", "ci_low", "ci_high", "p_value", "p_holm",
                "origins_a_better"]].round(4).to_string(index=False), flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    retail_identity()
    tx = load_cdnow()
    structure(tx)
    robustness(tx)
    prediction(tx)


if __name__ == "__main__":
    main()
