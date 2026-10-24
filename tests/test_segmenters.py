import numpy as np
import pandas as pd

from rfmfca.evaluation import build_features
from rfmfca.segmenters import FuzzyCMeans, choose_k


def blobs(seed=0):
    rng = np.random.default_rng(seed)
    centres = np.array([[0, 0], [6, 0], [0, 6]])
    return np.vstack([c + rng.normal(size=(60, 2)) for c in centres])


def test_fcm_finds_separated_clusters():
    x = blobs()
    fcm = FuzzyCMeans(3).fit(x)
    u = fcm.memberships(x)
    assert np.allclose(u.sum(axis=1), 1)
    labels = u.argmax(axis=1)
    # Each true blob maps (at >= 95 %) to its own cluster.
    majority = [np.bincount(labels[60 * b:60 * (b + 1)], minlength=3).argmax() for b in range(3)]
    assert len(set(majority)) == 3
    for b in range(3):
        assert (labels[60 * b:60 * (b + 1)] == majority[b]).mean() >= 0.95


def test_choose_k_on_three_blobs():
    assert choose_k(blobs()) == 3


def test_build_features_clusterers():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"recency_days": rng.integers(0, 300, 400),
                       "transaction_count": rng.integers(1, 50, 400), "amount": rng.random(400) * 1000})
    out = build_features(df.iloc[:300], df.iloc[300:], ("KM", "GMM", "FCM", "KM10"))
    k = out["KM"][2]["k"]
    assert out["GMM"][2]["k"] == k and out["FCM"][2]["k"] == k
    assert out["KM"][1].shape == (100, k) and out["KM10"][1].shape == (100, 10)
    assert set(np.unique(out["KM"][0])) <= {0.0, 1.0}
    assert np.allclose(out["GMM"][1].sum(axis=1), 1) and np.allclose(out["FCM"][1].sum(axis=1), 1)
