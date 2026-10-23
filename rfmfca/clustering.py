"""K-means and Ward hierarchical baselines (base paper Section 4.3)."""
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.preprocessing import MinMaxScaler

FEATURES = ["recency_days", "transaction_count", "amount"]


def iqr_filter(rfm, k=1.5):
    """Keep customers inside [Q1 - k*IQR, Q3 + k*IQR] on every RFM value.

    The paper reports 5,633 customers left; the rule as described (raw values,
    k = 1.5) leaves 5,040 here, and no tested variant reproduces 5,633.
    """
    x = rfm[FEATURES]
    q1, q3 = x.quantile(0.25), x.quantile(0.75)
    iqr = q3 - q1
    keep = ((x >= q1 - k * iqr) & (x <= q3 + k * iqr)).all(axis=1)
    return rfm[keep]


def prepare_features(rfm):
    """Log-transform (log1p, recency can be 0) then min-max scale all three to [0, 1]."""
    return MinMaxScaler().fit_transform(np.log1p(rfm[FEATURES].to_numpy(float)))


def fit_labels(method, x, k, seed=0):
    if method == "kmeans":
        return KMeans(n_clusters=k, n_init=10, random_state=seed).fit_predict(x)
    if method == "hierarchical":
        return AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(x)
    raise ValueError(method)


def validity_curve(x, ks=range(2, 11), seed=0):
    rows = []
    for method in ("kmeans", "hierarchical"):
        for k in ks:
            labels = fit_labels(method, x, k, seed)
            rows.append({"method": method, "k": k,
                         "silhouette": silhouette_score(x, labels),
                         "davies_bouldin": davies_bouldin_score(x, labels)})
    return pd.DataFrame(rows)


def cluster_profiles(rfm, labels):
    """Mean raw RFM and size per cluster (the paper's Tables 8 and 9)."""
    prof = rfm[FEATURES].groupby(labels).mean()
    prof["count"] = pd.Series(labels).value_counts().sort_index().to_numpy()
    return prof.rename_axis("cluster").reset_index()
