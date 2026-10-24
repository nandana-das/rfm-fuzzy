"""Plan addendum H: business value of targeting (revenue captured, response lift, gain curves).

Usage: python scripts/evaluate_business.py {retail|cdnow|dunnhumby}
Writes results/business/<dataset>_*.csv and saves the out-of-fold scores.
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

OUT = ROOT / "results" / "business"
METHODS = ("C-fca", "F-fca-core", "F-ctx", "logRFM", "KM10", "GMM10", "FCM10")
TARGET_OF = {"rev10": "log_spend", "rev20": "log_spend", "lift10": "buy", "lift20": "buy"}
TESTS = [("H1", "F-fca-core", "C-fca"), ("H2", "F-fca-core", "FCM10")]
PRIMARY_METRICS = ("rev20", "lift20")


def scores(name, tx, cutoffs):
    frames = {t: [] for t in ("buy", "log_spend")}
    for cutoff in cutoffs:
        data = planned.origin_frame(tx, cutoff)
        oof = {t: pd.DataFrame({"y": data[t].to_numpy()}, index=data.index) for t in frames}
        for tr, te in KFold(planned.N_FOLDS, shuffle=True, random_state=planned.SEED).split(data):
            train, test = data.iloc[tr], data.iloc[te]
            for m, (x_tr, x_te, _) in build_features(train, test, METHODS).items():
                for t in frames:
                    est = tuned.model(t).fit(x_tr, train[t])
                    oof[t].loc[test.index, m] = est.predict_proba(x_te)[:, 1] if t == "buy" else est.predict(x_te)
        for t in frames:
            frames[t].append(oof[t])
        print(name, "scores", cutoff, flush=True)
    for t, fs in frames.items():
        pd.concat(fs, keys=cutoffs, names=["cutoff", "CustomerID"]).to_csv(
            OUT / f"{name}_oof_{t}.csv.gz", float_format="%.6g")
    return frames


def main(name):
    OUT.mkdir(parents=True, exist_ok=True)
    tx, cutoffs = dataset(name)
    frames = scores(name, tx, cutoffs)

    rows = []
    for mn, t in TARGET_OF.items():
        for cutoff, d in zip(cutoffs, frames[t]):
            for m in METHODS:
                rows.append({"cutoff": cutoff, "metric": mn, "method": m, "value": metric(mn, d["y"], d[m])})
    per_origin = pd.DataFrame(rows)
    per_origin.to_csv(OUT / f"{name}_per_origin.csv", index=False)

    curve = []
    for cutoff, d in zip(cutoffs, frames["log_spend"]):
        for m in METHODS:
            for q in range(1, 101):
                curve.append({"cutoff": cutoff, "method": m, "pct_contacted": q,
                              "revenue_share": metric(f"rev{q}", d["y"], d[m])})
    curve = pd.DataFrame(curve).groupby(["method", "pct_contacted"], as_index=False)["revenue_share"].mean()
    curve.to_csv(OUT / f"{name}_gain_curve.csv", index=False)

    pairs = [(a, b) for _, a, b in TESTS] + [("F-fca-core", b) for b in ("F-ctx", "logRFM", "KM10", "GMM10")]
    comp = pd.DataFrame([paired_bootstrap(frames[TARGET_OF[mn]], mn, a, b)
                         for a, b in pairs for mn in TARGET_OF])
    comp.insert(0, "dataset", name)
    comp["test"] = ""
    for test, a, b in TESTS:
        comp.loc[(comp.a == a) & (comp.b == b) & comp.metric.isin(PRIMARY_METRICS), "test"] = test
    sel = comp.test != ""
    comp["p_holm"] = np.nan
    comp.loc[sel, "p_holm"] = holm(comp.loc[sel, "p_value"])
    comp.to_csv(OUT / f"{name}_comparisons.csv", index=False)
    print(per_origin.pivot_table(index="method", columns="metric", values="value").round(4).to_string())
    print(comp[["test", "a", "b", "metric", "pooled_diff", "ci_low", "ci_high", "p_value", "p_holm",
                "origins_a_better"]].round(4).to_string(index=False), flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
