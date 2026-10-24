import pandas as pd

from rfmfca.rfm import binary_context, compute_rfm, quintile_scores


def test_rfm_and_scores():
    tx = pd.DataFrame({
        "CustomerID": [str(i) for i in range(10) for _ in range(i + 1)],
        "InvoiceNo": "x",
        "InvoiceDate": [pd.Timestamp("2020-01-01") + pd.Timedelta(days=i)
                        for i in range(10) for _ in range(i + 1)],
        "Total": 1.0,
    })
    rfm = compute_rfm(tx)
    assert rfm.loc["9", "recency_days"] == 0
    assert rfm.loc["0", "transaction_count"] == 1
    s = quintile_scores(rfm)
    assert s.loc["9", "rfm_score"] == "555"
    assert s.loc["0", "rfm_score"] == "111"
    ctx = binary_context(s)
    assert ctx.shape == (10, 15)
    assert (ctx.sum(axis=1) == 3).all()


def test_zero_spend_customer_dropped():
    tx = pd.DataFrame({"CustomerID": ["a", "b"], "InvoiceNo": "x",
                       "InvoiceDate": pd.Timestamp("2020-01-01"), "Total": [0.0, 5.0]})
    assert list(compute_rfm(tx).index) == ["b"]


def test_targeting_metrics():
    import numpy as np

    from rfmfca.evaluation import metric
    spend = np.array([100.0, 0, 0, 0, 0, 0, 0, 0, 0, 0])       # one customer holds all revenue
    y = np.log1p(spend)
    assert metric("rev10", y, spend) == 1.0                     # perfect ranking
    assert metric("rev10", y, -spend) == 0.0                    # worst ranking
    buy = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    assert metric("lift20", buy, buy) == 1.0 / 0.2              # all buyers in top 20 %: lift 5
