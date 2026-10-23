"""Loading and cleaning the UCI Online Retail II transactions."""
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
CSV_FILES = ("online_retail_09_10.csv", "online_retail_10_11.csv")

# The two sheets of the UCI workbook use different headers; normalise to these.
COLUMN_MAP = {
    "Invoice": "InvoiceNo",
    "Price": "UnitPrice",
    "Customer ID": "CustomerID",
}


def load_transactions(raw_dir=RAW_DIR):
    """Read both years of Online Retail II as one DataFrame (1,067,371 rows)."""
    frames = []
    for name in CSV_FILES:
        frame = pd.read_csv(
            Path(raw_dir) / name,
            encoding="utf-8-sig",
            dtype={"InvoiceNo": str, "Invoice": str, "StockCode": str,
                   "CustomerID": str, "Customer ID": str},
        )
        frames.append(frame.rename(columns=COLUMN_MAP))
    df = pd.concat(frames, ignore_index=True)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], format="mixed")
    df["CustomerID"] = df["CustomerID"].str.replace(r"\.0$", "", regex=True)
    return df


def clean_transactions(df, drop_zero_price=False):
    """Apply the base paper's cleaning (Section 4.1).

    The paper says it drops rows with null values and quantity or price <= 0,
    and reports 805,620 rows left. That count is only reached when zero-price
    rows are *kept* (dropping them gives 805,549), so the default keeps them.
    """
    cols = ["InvoiceNo", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID"]
    out = df[cols].dropna()
    price_ok = out["UnitPrice"] > 0 if drop_zero_price else out["UnitPrice"] >= 0
    out = out[(out["Quantity"] > 0) & price_ok].copy()
    out["Total"] = out["Quantity"] * out["UnitPrice"]
    return out
