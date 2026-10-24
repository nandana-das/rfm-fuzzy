"""Clustering baselines on log-RFM: K-means, Gaussian mixture and fuzzy C-means (Addendum F)."""
import numpy as np
from sklearn.cluster import KMeans, kmeans_plusplus
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

COLS = ["recency_days", "transaction_count", "amount"]
K_RANGE = range(2, 11)
SILHOUETTE_SAMPLE = 3000


def log_rfm(rfm):
    return np.log1p(rfm[COLS].to_numpy(float))


class FuzzyCMeans:
    """Fuzzy C-means (Bezdek) with fuzzifier m; memberships of new points from fitted centres."""

    def __init__(self, n_clusters, m=2.0, max_iter=300, tol=1e-5, seed=0):
        self.k, self.m, self.max_iter, self.tol, self.seed = n_clusters, m, max_iter, tol, seed

    def memberships(self, x):
        d = np.linalg.norm(x[:, None, :] - self.centers_[None, :, :], axis=2)
        d = np.fmax(d, 1e-12)
        inv = d ** (-2 / (self.m - 1))
        return inv / inv.sum(axis=1, keepdims=True)

    def fit(self, x):
        # k-means++ seeding: random initial memberships pull every centre to the mean.
        self.centers_, _ = kmeans_plusplus(x, self.k, random_state=self.seed)
        u = self.memberships(x)
        for _ in range(self.max_iter):
            w = u ** self.m
            self.centers_ = (w.T @ x) / w.sum(axis=0)[:, None]
            new = self.memberships(x)
            done = np.abs(new - u).max() < self.tol
            u = new
            if done:
                break
        return self


def choose_k(x, seed=0):
    """k in 2..10 with the best K-means silhouette on a sample of at most 3,000 points."""
    rng = np.random.default_rng(seed)
    sample = x[rng.choice(len(x), min(len(x), SILHOUETTE_SAMPLE), replace=False)]
    scores = {k: silhouette_score(sample, KMeans(k, n_init=10, random_state=seed).fit_predict(sample))
              for k in K_RANGE}
    return max(scores, key=scores.get)


def segment_features(method, train_rfm, test_rfm, k, seed=0):
    """Fit `method` (KM, GMM or FCM) on training customers; return (train, test) features."""
    scaler = StandardScaler().fit(log_rfm(train_rfm))
    x_tr, x_te = scaler.transform(log_rfm(train_rfm)), scaler.transform(log_rfm(test_rfm))
    if method == "KM":
        km = KMeans(k, n_init=10, random_state=seed).fit(x_tr)
        eye = np.eye(k)
        return eye[km.predict(x_tr)], eye[km.predict(x_te)]
    if method == "GMM":
        gm = GaussianMixture(k, covariance_type="full", n_init=3, random_state=seed).fit(x_tr)
        return gm.predict_proba(x_tr), gm.predict_proba(x_te)
    if method == "FCM":
        fcm = FuzzyCMeans(k, seed=seed).fit(x_tr)
        return fcm.memberships(x_tr), fcm.memberships(x_te)
    raise ValueError(method)
