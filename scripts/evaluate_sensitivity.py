"""Plan addendum K: one-at-a-time sensitivity of the main comparisons.

Usage: python scripts/evaluate_sensitivity.py {retail|cdnow|dunnhumby}
Writes results/sensitivity/<dataset>_*.csv.
"""
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import KFold

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import evaluate_prediction as planned  # noqa: E402
import posthoc_tuned_regularization as tuned  # noqa: E402
import rfmfca.evaluation as ev  # noqa: E402
import rfmfca.fuzzy as fz  # noqa: E402
from evaluate_hybrid import dataset  # noqa: E402

OUT = ROOT / "results" / "sensitivity"
CTX_FCA = ("C-ctx", "F-ctx", "C-fca", "F-fca-core")
SETTINGS = (
    [("support", s, ("C-fca", "F-fca-core"), [("F-fca-core", "C-fca")]) for s in (0.02, 0.04, 0.06)]
    + [("half_width", w, CTX_FCA, [("F-ctx", "C-ctx"), ("F-fca-core", "C-fca")]) for w in (0.15, 0.20, 0.25)]
    + [("horizon", h, CTX_FCA, [("F-ctx", "C-ctx"), ("F-fca-core", "C-fca")]) for h in (60, 180)]
    + [("K", k, (f"F-sel{k}", f"C-sel{k}"), [(f"F-sel{k}", f"C-sel{k}")]) for k in (5, 10, 20, 30)]
)
for k in (5, 30):
    ev.SELECTED[f"F-sel{k}"] = ("fuzzy", 3, "core", k)
    ev.SELECTED[f"C-sel{k}"] = ("crisp", 2, "sigma", k)


def run_setting(tx, cutoffs, factor, value, methods, pairs):
    support, width, horizon = 0.04, 0.20, 90
    if factor == "support":
        support = value
    elif factor == "half_width":
        width = value
    elif factor == "horizon":
        horizon = value
    fz.HALF_WIDTH = width
    planned.HORIZON = pd.Timedelta(days=horizon)
    end = tx["InvoiceDate"].max() + pd.Timedelta(days=1)
    usable = [c for c in cutoffs if pd.Timestamp(c) + planned.HORIZON <= end]
    oof_all, counts = {t: [] for t in planned.TARGETS.values()}, []
    for cutoff in usable:
        data = planned.origin_frame(tx, cutoff)
        oof = {t: pd.DataFrame({"y": data[t].to_numpy()}, index=data.index) for t in planned.TARGETS.values()}
        for tr, te in KFold(planned.N_FOLDS, shuffle=True, random_state=planned.SEED).split(data):
            train, test = data.iloc[tr], data.iloc[te]
            for m, (x_tr, x_te, info) in ev.build_features(train, test, methods, min_support=support).items():
                counts.append({"method": m, "n_features": x_tr.shape[1]})
                for t in planned.TARGETS.values():
                    est = tuned.model(t).fit(x_tr, train[t])
                    oof[t].loc[test.index, m] = est.predict_proba(x_te)[:, 1] if t == "buy" else est.predict(x_te)
        for t in planned.TARGETS.values():
            oof_all[t].append(oof[t])
    rows = []
    for a, b in pairs:
        for mn, t in planned.TARGETS.items():
            r = ev.paired_bootstrap(oof_all[t], mn, a, b)
            r["value_a"] = sum(ev.metric(mn, d["y"], d[a]) for d in oof_all[t]) / len(usable)
            r["value_b"] = sum(ev.metric(mn, d["y"], d[b]) for d in oof_all[t]) / len(usable)
            rows.append(r)
    feats = pd.DataFrame(counts).groupby("method").n_features.mean().to_dict()
    for r in rows:
        r.update({"factor": factor, "value": value, "n_origins_used": len(usable),
                  "features_a": feats[r["a"]], "features_b": feats[r["b"]]})
    fz.HALF_WIDTH, planned.HORIZON = 0.20, pd.Timedelta(days=90)
    return rows


def main(name):
    OUT.mkdir(parents=True, exist_ok=True)
    tx, cutoffs = dataset(name)
    rows = []
    for factor, value, methods, pairs in SETTINGS:
        rows += run_setting(tx, cutoffs, factor, value, methods, pairs)
        pd.DataFrame(rows).to_csv(OUT / f"{name}_sensitivity.csv", index=False)
        print(name, factor, value, flush=True)
    out = pd.DataFrame(rows)
    out["holds"] = (out.ci_low > 0)
    out.to_csv(OUT / f"{name}_sensitivity.csv", index=False)
    print(out[["factor", "value", "a", "b", "metric", "pooled_diff", "ci_low", "ci_high", "origins_a_better",
               "n_origins_used", "holds"]].round(4).to_string(index=False), flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
