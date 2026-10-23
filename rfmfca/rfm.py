"""RFM aggregation and quintile scoring (base paper Section 4.1)."""
import pandas as pd

DIMENSIONS = ("R", "F", "M")


def compute_rfm(tx, reference_date=None):
    """Per-customer recency (days), frequency (line items) and monetary value.

    Recency is the number of calendar days between the last purchase date and
    the reference date (the latest invoice date); counting calendar days rather
    than elapsed 24-hour periods matches the paper's concept sizes far better.
    Frequency counts transaction rows, as in the paper (its maximum is ~12,900,
    far above the number of invoices any customer has). Customers whose total
    spend is zero are dropped, which gives the paper's 5,878 customers.
    """
    if reference_date is None:
        reference_date = tx["InvoiceDate"].max()
    g = tx.groupby("CustomerID").agg(
        last_purchase=("InvoiceDate", "max"),
        transaction_count=("InvoiceNo", "size"),
        amount=("Total", "sum"),
    )
    g = g[g["amount"] > 0]
    g["recency_days"] = (reference_date.normalize() - g["last_purchase"].dt.normalize()).dt.days
    return g[["recency_days", "transaction_count", "amount"]]


def quintile_scores(rfm):
    """Score each dimension 1..5 by quintile; 5 is best (recent, frequent, big spender).

    Bins use quantile cut points (right-closed), so tied values share a score.
    """
    scores = pd.DataFrame(index=rfm.index)
    # Low recency is good, so its score order is reversed.
    scores["R"] = 5 - pd.qcut(rfm["recency_days"], 5, labels=False)
    scores["F"] = 1 + pd.qcut(rfm["transaction_count"], 5, labels=False)
    scores["M"] = 1 + pd.qcut(rfm["amount"], 5, labels=False)
    scores = scores.astype(int)
    scores["rfm_score"] = scores["R"].astype(str) + scores["F"].astype(str) + scores["M"].astype(str)
    return scores


def binary_context(scores):
    """One-hot the scores into the 15-attribute formal context R1..R5, F1..F5, M1..M5."""
    cols = {}
    for dim in DIMENSIONS:
        for level in range(1, 6):
            cols[f"{dim}{level}"] = scores[dim] == level
    return pd.DataFrame(cols, index=scores.index)
