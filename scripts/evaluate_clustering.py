"""Plan addendum F: K-means, GMM and fuzzy C-means baselines against fuzzy RFM-FCA.

Usage: python scripts/evaluate_clustering.py {retail|cdnow|dunnhumby}
Writes results/clustering/<dataset>_*.csv.
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
from evaluate_hybrid import dataset  # noqa: E402
from rfmfca.evaluation import build_features, holm, metric, paired_bootstrap  # noqa: E402
from rfmfca.rfm import compute_rfm  # noqa: E402

OUT = ROOT / "results" / "clustering"
PRED_METHODS = ("C-fca", "F-ctx", "F-fca-core", "logRFM", "KM", "GMM", "FCM", "KM10", "GMM10", "FCM10")
STRUCT_METHODS = ("C-fca", "F-fca-core", "KM", "GMM", "FCM")
TESTS = [("F1", "F-fca-core", "FCM"), ("F2", "F-fca-core", "KM"), ("F3", "F-fca-core", "GMM")]
N_PAIRS, N_REPLICATES, N_BOOT, DROP_P, SEED = 20_000, 20, 20, 0.05, 0


def prediction(name, tx, cutoffs):
    per_origin, ks, oof_all = [], [], {t: [] for t in planned.TARGETS.values()}
    for cutoff in cutoffs:
        data = planned.origin_frame(tx, cutoff)
        oof = {t: pd.DataFrame({"y": data[t].to_numpy()}, index=data.index) for t in planned.TARGETS.values()}
        for fold, (tr, te) in enumerate(KFold(planned.N_FOLDS, shuffle=True, random_state=planned.SEED).split(data)):
            train, test = data.iloc[tr], data.iloc[te]
            for m, (x_tr, x_te, info) in build_features(train, test, PRED_METHODS).items():
                ks.append({"cutoff": cutoff, "fold": fold, "method": m, "n_features": x_tr.shape[1], **info})
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
    pd.DataFrame(ks).to_csv(OUT / f"{name}_feature_counts.csv", index=False)
    pairs = [(a, b) for _, a, b in TESTS]
    pairs += [(a, b) for a in ("F-ctx", "C-fca", "logRFM") for b in ("KM", "GMM", "FCM")]
    pairs += [("F-fca-core", b) for b in ("KM10", "GMM10", "FCM10")]
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


def pair_similarity(x, pairs):
    a, b = x[pairs[:, 0]], x[pairs[:, 1]]
    na, nb = np.linalg.norm(a, axis=1), np.linalg.norm(b, axis=1)
    denom = na * nb
    return np.where(denom > 0, (a * b).sum(axis=1) / np.where(denom > 0, denom, 1), 0.0)


def agreement(x_ref, x_new, rng):
    pairs = rng.integers(0, len(x_ref), size=(N_PAIRS, 2))
    pairs = pairs[pairs[:, 0] != pairs[:, 1]]
    s_ref, s_new = pair_similarity(x_ref, pairs), pair_similarity(x_new, pairs)
    if s_ref.std() == 0 or s_new.std() == 0:
        return float("nan")
    return float(np.corrcoef(s_ref, s_new)[0, 1])


def structure(name, tx):
    ref_date = tx["InvoiceDate"].max()
    rfm = compute_rfm(tx, ref_date)
    ref = {m: v[1] for m, v in build_features(rfm, rfm, STRUCT_METHODS).items()}
    ks = {m: v[2].get("k") for m, v in build_features(rfm, rfm, ("KM",)).items()}
    rng = np.random.default_rng(SEED)
    invoices = tx["InvoiceNo"].unique()
    rows = []
    for rep in range(N_REPLICATES):
        keep = set(invoices[rng.random(len(invoices)) >= DROP_P])
        pert = compute_rfm(tx[tx["InvoiceNo"].isin(keep)], ref_date)
        common = rfm.index.intersection(pert.index)
        pos = rfm.index.get_indexer(common)
        new = build_features(pert, pert.loc[common], STRUCT_METHODS)
        pair_rng = np.random.default_rng(SEED + rep)
        row = {"kind": "robustness", "replicate": rep}
        for m in STRUCT_METHODS:
            row[m] = agreement(ref[m][pos], new[m][1], np.random.default_rng(pair_rng.integers(1 << 31)))
        rows.append(row)
        print(name, "robustness", rep, flush=True)
    for b in range(N_BOOT):
        sample = rfm.iloc[rng.integers(0, len(rfm), len(rfm))]
        sample = sample.set_axis(np.arange(len(sample)))
        new = build_features(sample, rfm, STRUCT_METHODS)
        pair_rng = np.random.default_rng(10_000 + b)
        row = {"kind": "stability", "replicate": b}
        for m in STRUCT_METHODS:
            row[m] = agreement(ref[m], new[m][1], np.random.default_rng(pair_rng.integers(1 << 31)))
        rows.append(row)
        print(name, "stability", b, flush=True)
    out = pd.DataFrame(rows)
    out.insert(0, "dataset", name)
    out.to_csv(OUT / f"{name}_structure_agreement.csv", index=False)
    summary = out.groupby("kind")[list(STRUCT_METHODS)].agg(["mean", "min"]).round(4)
    print("full-data k:", ks, flush=True)
    print(summary.to_string(), flush=True)


def main(name):
    OUT.mkdir(parents=True, exist_ok=True)
    tx, cutoffs = dataset(name)
    structure(name, tx)
    prediction(name, tx, cutoffs)


if __name__ == "__main__":
    main(sys.argv[1])
