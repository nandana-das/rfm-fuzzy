"""Loading dunnhumby "The Complete Journey" transactions as a transaction table.

2,500 households, 711 days of grocery baskets. The raw file has day numbers, not
dates; they are mapped to dates from an arbitrary anchor, since only differences
between days are used. Not redistributed (see dunnhumby's terms of use).
"""
from pathlib import Path

import pandas as pd

from rfmfca.data import RAW_DIR

DUNNHUMBY_FILE = "dunnhumby_transaction_data.csv"
DAY_ZERO = pd.Timestamp("2000-01-01")   # arbitrary anchor; DAY 1 -> 2000-01-02


def day_to_date(day):
    return DAY_ZERO + pd.to_timedelta(day, unit="D")


def load_dunnhumby(raw_dir=RAW_DIR):
    """Return transactions with the columns the RFM code expects.

    One row per basket line: frequency = basket lines, monetary = summed sales value,
    as for the other datasets. Rows with quantity <= 0 or negative sales value are dropped.
    """
    df = pd.read_csv(Path(raw_dir) / DUNNHUMBY_FILE,
                     usecols=["household_key", "BASKET_ID", "DAY", "QUANTITY", "SALES_VALUE"],
                     dtype={"household_key": str, "BASKET_ID": str})
    df = df.rename(columns={"household_key": "CustomerID", "BASKET_ID": "InvoiceNo",
                            "QUANTITY": "Quantity", "SALES_VALUE": "Total"})
    df["InvoiceDate"] = day_to_date(df["DAY"])
    df = df[(df["Quantity"] > 0) & (df["Total"] >= 0)]
    return df[["InvoiceNo", "Quantity", "InvoiceDate", "CustomerID", "Total"]].reset_index(drop=True)
