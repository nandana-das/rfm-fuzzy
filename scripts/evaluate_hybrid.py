"""Plan addendum E (exploratory): fuzzy concepts + log-RFM hybrids, tuned regularisation.

Usage: python scripts/evaluate_hybrid.py {retail|cdnow|dunnhumby}
Writes results/hybrid/<dataset>_*.csv.
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
from rfmfca.evaluation import build_features, holm, metric, paired_bootstrap  # noqa: E402

OUT = ROOT / "results" / "hybrid"
METHODS = ("logRFM", "F-fca-core", "HYB-fca", "HYB-ctx", "HYB-cfca")
TESTS = [("E1", "HYB-fca", "logRFM"), ("E2", "HYB-fca", "HYB-cfca"), ("E3", "HYB-fca", "HYB-ctx")]


def dataset(name):
    if name == "retail":
        from rfmfca.data import clean_transactions, load_transactions
        return clean_transactions(load_transactions()), planned.CUTOFFS
    if name == "cdnow":
        import confirm_cdnow
        from rfmfca.cdnow import load_cdnow
        return load_cdnow(), confirm_cdnow.CUTOFFS
    if name == "dunnhumby":
        from rfmfca.dunnhumby import day_to_date, load_dunnhumby
        return load_dunnhumby(), [str(day_to_date(d).date()) for d in (351, 441, 531, 621)]
    raise SystemExit(f"unknown dataset {name}")


def main(name):
    OUT.mkdir(parents=True, exist_ok=True)
    tx, cutoffs = dataset(name)
    per_origin, oof_all = [], {t: [] for t in planned.TARGETS.values()}
    for cutoff in cutoffs:
        data = planned.origin_frame(tx, cutoff)
        oof = {t: pd.DataFrame({"y": data[t].to_numpy()}, index=data.index) for t in planned.TARGETS.values()}
        for tr, te in KFold(planned.N_FOLDS, shuffle=True, random_state=planned.SEED).split(data):
            train, test = data.iloc[tr], data.iloc[te]
            for m, (x_tr, x_te, _) in build_features(train, test, METHODS).items():
                for t in planned.TARGETS.values():
                    est = tuned.model(t).fit(x_tr, train[t])
                    oof[t].loc[test.index, m] = est.predict_proba(x_te)[:, 1] if t == "buy" else est.predict(x_te)
        for mn, t in planned.TARGETS.items():
            oof_all[t].append(oof[t])
            for m in METHODS:
                per_origin.append({"dataset": name, "cutoff": cutoff, "metric": mn, "method": m,
                                   "value": metric(mn, oof[t]["y"], oof[t][m])})
        print(name, cutoff, flush=True)
    per_origin = pd.DataFrame(per_origin)
    per_origin.to_csv(OUT / f"{name}_per_origin.csv", index=False)
    rows = []
    for test, a, b in TESTS:
        for mn, t in planned.TARGETS.items():
            rows.append({"dataset": name, "test": test, **paired_bootstrap(oof_all[t], mn, a, b)})
    comp = pd.DataFrame(rows)
    comp["p_holm"] = holm(comp["p_value"])
    comp.to_csv(OUT / f"{name}_comparisons.csv", index=False)
    print(per_origin.pivot_table(index="method", columns="metric", values="value").round(4).to_string())
    print(comp[["test", "a", "b", "metric", "pooled_diff", "ci_low", "ci_high", "p_holm",
                "origins_a_better"]].round(4).to_string(index=False), flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
