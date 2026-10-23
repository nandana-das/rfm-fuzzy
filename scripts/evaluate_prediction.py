"""H1: rolling-origin prediction of next-90-day purchase and spend (docs/EXTENSION_PLAN.md).

Writes results/extension/prediction_*.csv.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import KFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rfmfca.data import clean_transactions, load_transactions  # noqa: E402
from rfmfca.evaluation import METHODS, build_features, holm, metric, paired_bootstrap  # noqa: E402
from rfmfca.rfm import compute_rfm  # noqa: E402

OUT = ROOT / "results" / "extension"
CUTOFFS = ["2010-12-01", "2011-03-01", "2011-06-01", "2011-09-01"]
HORIZON = pd.Timedelta(days=90)
N_FOLDS, SEED = 5, 0
TARGETS = {"auc": "buy", "r2": "log_spend"}


def origin_frame(tx, cutoff):
    cutoff = pd.Timestamp(cutoff)
    hist = tx[tx["InvoiceDate"] < cutoff]
    rfm = compute_rfm(hist)
    fut = tx[(tx["InvoiceDate"] >= cutoff) & (tx["InvoiceDate"] < cutoff + HORIZON)]
    spend = fut.groupby("CustomerID")["Total"].sum().reindex(rfm.index, fill_value=0.0)
    rfm["buy"] = (fut.groupby("CustomerID").size().reindex(rfm.index, fill_value=0) > 0).astype(int)
    rfm["log_spend"] = np.log1p(spend.clip(lower=0))
    return rfm


def model(target):
    if target == "buy":
        return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=5000))
    return make_pipeline(StandardScaler(), Ridge(alpha=1.0))


def run_origin(data):
    oof = {t: pd.DataFrame({"y": data[t].to_numpy()}, index=data.index) for t in TARGETS.values()}
    info_rows = []
    folds = KFold(N_FOLDS, shuffle=True, random_state=SEED)
    for fold, (tr, te) in enumerate(folds.split(data)):
        train, test = data.iloc[tr], data.iloc[te]
        feats = build_features(train, test)
        for m, (x_tr, x_te, info) in feats.items():
            info_rows.append({"fold": fold, "method": m, "n_features": x_tr.shape[1], **info})
            for t in TARGETS.values():
                est = model(t).fit(x_tr, train[t])
                pred = est.predict_proba(x_te)[:, 1] if t == "buy" else est.predict(x_te)
                oof[t].loc[test.index, m] = pred
    return oof, pd.DataFrame(info_rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tx = clean_transactions(load_transactions())
    per_origin, infos, oof_all = [], [], {t: [] for t in TARGETS.values()}
    for cutoff in CUTOFFS:
        t0 = time.time()
        data = origin_frame(tx, cutoff)
        oof, info = run_origin(data)
        info.insert(0, "cutoff", cutoff)
        infos.append(info)
        for metric_name, t in TARGETS.items():
            oof_all[t].append(oof[t])
            for m in METHODS:
                per_origin.append({"cutoff": cutoff, "metric": metric_name, "method": m,
                                   "value": metric(metric_name, oof[t]["y"], oof[t][m]),
                                   "n_customers": len(data), "positive_rate": data["buy"].mean()})
        print(f"{cutoff}: {len(data)} customers, {time.time() - t0:.0f}s", flush=True)

    per_origin = pd.DataFrame(per_origin)
    per_origin.to_csv(OUT / "prediction_per_origin.csv", index=False)
    pd.concat(infos).to_csv(OUT / "prediction_feature_counts.csv", index=False)
    for t, frames in oof_all.items():
        pd.concat(frames, keys=CUTOFFS, names=["cutoff", "CustomerID"]).to_csv(
            OUT / f"prediction_oof_{t}.csv.gz", float_format="%.6g")

    pairs = [("F-fca", "C-fca"), ("F-ctx", "C-ctx"), ("F-fca-G", "F-fca"), ("F-fca-G", "C-fca")]
    pairs += [(m, "logRFM") for m in METHODS if m != "logRFM"]
    rows = []
    for metric_name, t in TARGETS.items():
        for a, b in pairs:
            rows.append(paired_bootstrap(oof_all[t], metric_name, a, b))
    comp = pd.DataFrame(rows)
    primary = (comp.a == "F-fca") & (comp.b == "C-fca")
    comp["primary"] = primary
    comp["p_holm"] = np.nan
    comp.loc[primary, "p_holm"] = holm(comp.loc[primary, "p_value"])
    comp.to_csv(OUT / "prediction_comparisons.csv", index=False)

    summary = per_origin.pivot_table(index="method", columns="metric", values="value", aggfunc="mean")
    print(summary.loc[list(METHODS)].round(4).to_string())
    print(comp[["a", "b", "metric", "pooled_diff", "ci_low", "ci_high", "p_value", "p_holm",
                "origins_a_better"]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
