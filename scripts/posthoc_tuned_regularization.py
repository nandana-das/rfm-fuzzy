"""POST HOC, EXPLORATORY (not in docs/EXTENSION_PLAN.md).

The planned H1 run used fixed regularisation (C = 1, alpha = 1). The Lukasiewicz
fuzzy lattice yields ~2,600 features for ~4,000 customers, so its poor result may
be overfitting rather than a lack of information. This re-runs H1 with the
regularisation strength chosen by inner 3-fold CV for every method, on the same
origins and outer folds.

Writes results/extension/posthoc_tuned_*.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegressionCV, RidgeCV
from sklearn.model_selection import KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from evaluate_prediction import CUTOFFS, N_FOLDS, SEED, TARGETS, origin_frame  # noqa: E402
from rfmfca.data import clean_transactions, load_transactions  # noqa: E402
from rfmfca.evaluation import METHODS, build_features, metric, paired_bootstrap  # noqa: E402

OUT = ROOT / "results" / "extension"
GRID = np.logspace(-4, 2, 7)


def model(target):
    if target == "buy":
        return make_pipeline(StandardScaler(), LogisticRegressionCV(Cs=GRID, cv=3, scoring="roc_auc",
                                                                    max_iter=5000))
    return make_pipeline(StandardScaler(), RidgeCV(alphas=1 / GRID))


def main():
    tx = clean_transactions(load_transactions())
    per_origin, oof_all, chosen = [], {t: [] for t in TARGETS.values()}, []
    for cutoff in CUTOFFS:
        data = origin_frame(tx, cutoff)
        oof = {t: pd.DataFrame({"y": data[t].to_numpy()}, index=data.index) for t in TARGETS.values()}
        for fold, (tr, te) in enumerate(KFold(N_FOLDS, shuffle=True, random_state=SEED).split(data)):
            train, test = data.iloc[tr], data.iloc[te]
            for m, (x_tr, x_te, _) in build_features(train, test).items():
                for t in TARGETS.values():
                    est = model(t).fit(x_tr, train[t])
                    last = est[-1]
                    chosen.append({"cutoff": cutoff, "fold": fold, "method": m, "target": t,
                                   "strength": float(last.C_[0]) if t == "buy" else float(1 / last.alpha_)})
                    oof[t].loc[test.index, m] = (est.predict_proba(x_te)[:, 1] if t == "buy"
                                                 else est.predict(x_te))
        for metric_name, t in TARGETS.items():
            oof_all[t].append(oof[t])
            for m in METHODS:
                per_origin.append({"cutoff": cutoff, "metric": metric_name, "method": m,
                                   "value": metric(metric_name, oof[t]["y"], oof[t][m])})
        print(cutoff, flush=True)

    per_origin = pd.DataFrame(per_origin)
    per_origin.to_csv(OUT / "posthoc_tuned_per_origin.csv", index=False)
    pd.DataFrame(chosen).to_csv(OUT / "posthoc_tuned_chosen_strength.csv", index=False)
    pairs = [("F-fca", "C-fca"), ("F-fca-G", "C-fca"), ("F-ctx", "C-ctx"), ("F-fca", "F-ctx"),
             ("C-fca", "C-ctx"), ("F-ctx", "logRFM")]
    comp = pd.DataFrame([paired_bootstrap(oof_all[t], mn, a, b)
                         for mn, t in TARGETS.items() for a, b in pairs])
    comp.to_csv(OUT / "posthoc_tuned_comparisons.csv", index=False)
    print(per_origin.pivot_table(index="method", columns="metric", values="value").round(4).to_string())
    print(comp[["a", "b", "metric", "pooled_diff", "ci_low", "ci_high", "p_value",
                "origins_a_better"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
