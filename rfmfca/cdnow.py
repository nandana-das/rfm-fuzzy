"""Loading the CDNOW master dataset (Fader & Hardie) as a transaction table.

23,570 customers who first bought from CDNOW in Q1 1997, with every purchase up to
the end of June 1998 (69,659 rows: customer, date, number of CDs, dollar value).
"""
from pathlib import Path

import pandas as pd

from rfmfca.data import RAW_DIR

CDNOW_FILE = "CDNOW_master.txt"


def load_cdnow(raw_dir=RAW_DIR):
    """Return transactions with the columns the RFM code expects.

    Each row is one purchase occasion, so it plays the role of an invoice line:
    frequency is the number of purchase rows, monetary the summed dollar value.
    Rows with zero dollar value are kept (as zero-price rows are for Online Retail II);
    customers with zero total spend are dropped later by compute_rfm.
    """
    df = pd.read_csv(Path(raw_dir) / CDNOW_FILE, sep=r"\s+", header=None,
                     names=["CustomerID", "date", "Quantity", "Total"],
                     dtype={"CustomerID": str, "date": str, "Quantity": str, "Total": str})
    # Some mirrors add a header line; the original file has none.
    df = df[df["CustomerID"].str.isdigit()].copy()
    df["Quantity"] = df["Quantity"].astype(int)
    df["Total"] = df["Total"].astype(float)
    df["InvoiceDate"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df["InvoiceNo"] = df["CustomerID"] + "-" + df["date"] + "-" + df.groupby(["CustomerID", "date"]).cumcount().astype(str)
    df = df[(df["Quantity"] > 0) & (df["Total"] >= 0)]
    return df[["InvoiceNo", "Quantity", "InvoiceDate", "CustomerID", "Total"]].reset_index(drop=True)
