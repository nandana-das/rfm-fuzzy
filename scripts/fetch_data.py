"""Download UCI Online Retail II (id 502) and write the two yearly CSVs to data/raw/.

The dataset is CC BY 4.0: Chen, D. (2019), https://doi.org/10.24432/C5CG6D.
"""
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rfmfca.data import CSV_FILES, RAW_DIR  # noqa: E402

URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
SHEETS = ("Year 2009-2010", "Year 2010-2011")


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(URL) as resp:
        archive = zipfile.ZipFile(io.BytesIO(resp.read()))
    xlsx = next(n for n in archive.namelist() if n.endswith(".xlsx"))
    book = pd.read_excel(io.BytesIO(archive.read(xlsx)), sheet_name=list(SHEETS),
                         dtype={"Invoice": str, "StockCode": str})
    for sheet, name in zip(SHEETS, CSV_FILES):
        book[sheet].to_csv(RAW_DIR / name, index=False)
        print(f"wrote {RAW_DIR / name} ({len(book[sheet])} rows)")


if __name__ == "__main__":
    main()
