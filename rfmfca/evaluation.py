"""Feature construction and paired-bootstrap tests for comparing crisp and fuzzy RFM-FCA.

Everything that is learned from data (rank scale, lattice, frequent concepts)
is fitted on the training customers only and then applied to the test customers.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, roc_auc_score

from rfmfca.fuzzy import (FuzzyConceptLattice, RankScaler, crisp_context, fuzzy_context,
                          tie_aware_fuzzy_context)

MIN_SUPPORT = 0.04
METHODS = ("C-ctx", "C-fca", "F-ctx", "F-fca", "F-fca-G", "logRFM")
LATTICE_SPECS = {          # method -> (context kind, n_levels, residuum)
    "C-fca": ("crisp", 2, "lukasiewicz"),
    "F-fca": ("fuzzy", 3, "lukasiewicz"),
    "F-fca-G": ("fuzzy", 3, "godel"),
}
# Plan addendum A: same lattices, filtered by core support instead of sigma-count.
CORE_SPECS = {
    "F-fca-core": ("fuzzy", 3, "lukasiewicz"),
    "F-fca-G-core": ("fuzzy", 3, "godel"),
}
CORE_METHODS = ("C-ctx", "C-fca", "F-ctx", "F-fca-core", "F-fca-G-core")
# Plan addendum C: tie-aware fuzzy context (tied blocks averaged over their rank interval).
TIE_SPECS = {
    "F-fca-core-T": ("fuzzy-tie", 3, "lukasiewicz"),
    "F-fca-G-core-T": ("fuzzy-tie", 3, "godel"),
}
# Plan addendum E: hybrid = segment features + log-RFM.
HYBRIDS = {"HYB-fca": "F-fca-core", "HYB-ctx": "F-ctx", "HYB-cfca": "C-fca"}


def _context(kind, ranks, intervals=None):
    if kind == "crisp":
        return crisp_context(ranks)
    if kind == "fuzzy-tie":
        return tie_aware_fuzzy_context(intervals, n_levels=3)
    return fuzzy_context(ranks, n_levels=3)


def build_features(train_rfm, test_rfm, methods=METHODS, min_support=MIN_SUPPORT):
    """Return {method: (X_train, X_test, info)} with info holding e.g. the concept count."""
    scaler = RankScaler().fit(train_rfm)
    u_tr, u_te = scaler.transform(train_rfm), scaler.transform(test_rfm)
    needs_ties = any(m == "F-ctx-T" or m in TIE_SPECS for m in methods)
    iv_tr = scaler.transform_intervals(train_rfm) if needs_ties else None
    iv_te = scaler.transform_intervals(test_rfm) if needs_ties else None
    out = {}
    for m in methods:
        if m == "C-ctx":
            out[m] = (crisp_context(u_tr).to_numpy(float), crisp_context(u_te).to_numpy(float), {})
        elif m == "F-ctx":
            out[m] = (fuzzy_context(u_tr).to_numpy(float) / 2, fuzzy_context(u_te).to_numpy(float) / 2, {})
        elif m == "F-ctx-T":
            out[m] = (tie_aware_fuzzy_context(iv_tr).to_numpy(float) / 2,
                      tie_aware_fuzzy_context(iv_te).to_numpy(float) / 2, {})
        elif m == "logRFM":
            cols = ["recency_days", "transaction_count", "amount"]
            out[m] = (np.log1p(train_rfm[cols].to_numpy(float)),
                      np.log1p(test_rfm[cols].to_numpy(float)), {})
        elif m in HYBRIDS:
            # Plan addendum E: segment features plus the three log-RFM values.
            parts = build_features(train_rfm, test_rfm, (HYBRIDS[m], "logRFM"), min_support)
            seg, log = parts[HYBRIDS[m]], parts["logRFM"]
            out[m] = (np.hstack([seg[0], log[0]]), np.hstack([seg[1], log[1]]), seg[2])
        else:
            support_kind = "core" if (m in CORE_SPECS or m in TIE_SPECS) else "sigma"
            kind, n_levels, residuum = {**LATTICE_SPECS, **CORE_SPECS, **TIE_SPECS}[m]
            ctx_tr, ctx_te = _context(kind, u_tr, iv_tr), _context(kind, u_te, iv_te)
            lat = FuzzyConceptLattice(ctx_tr, n_levels, residuum)
            idx = lat.frequent(min_support, support_kind)
            intents = lat.intents[idx]
            out[m] = (lat.degrees(ctx_tr.to_numpy(), intents), lat.degrees(ctx_te.to_numpy(), intents),
                      {"n_concepts": len(lat.intents), "n_frequent": len(idx)})
    return out


def metric(name, y, pred):
    return roc_auc_score(y, pred) if name == "auc" else r2_score(y, pred)


def paired_bootstrap(origins, metric_name, a, b, n_boot=1000, seed=0):
    """Mean over origins of metric(a) - metric(b), with a customer-level bootstrap.

    `origins` is a list of DataFrames holding the target column "y" and one
    out-of-fold prediction column per method. Customers are resampled within
    each origin; the pooled statistic is the unweighted mean over origins.
    """
    rng = np.random.default_rng(seed)
    point = [metric(metric_name, d["y"], d[a]) - metric(metric_name, d["y"], d[b]) for d in origins]
    boots = np.empty((n_boot, len(origins)))
    for k, d in enumerate(origins):
        y, pa, pb = d["y"].to_numpy(), d[a].to_numpy(), d[b].to_numpy()
        n = len(y)
        for i in range(n_boot):
            s = rng.integers(0, n, n)
            boots[i, k] = metric(metric_name, y[s], pa[s]) - metric(metric_name, y[s], pb[s])
    pooled = boots.mean(axis=1)
    p = 2 * min((pooled <= 0).mean(), (pooled >= 0).mean())
    return {
        "a": a, "b": b, "metric": metric_name,
        "pooled_diff": float(np.mean(point)),
        "ci_low": float(np.quantile(pooled, 0.025)),
        "ci_high": float(np.quantile(pooled, 0.975)),
        "p_value": float(max(p, 1 / n_boot)),
        "origins_a_better": int(sum(x > 0 for x in point)),
        "n_origins": len(origins),
        "per_origin_diff": ";".join(f"{x:.4f}" for x in point),
    }


def holm(pvalues):
    """Holm-adjusted p-values, in the input order."""
    p = np.asarray(pvalues, float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(p) - rank) * p[i])
        adj[i] = min(running, 1.0)
    return adj
