"""Download the datasets into data/raw/.

- UCI Online Retail II (id 502), written as two yearly CSVs.
  CC BY 4.0: Chen, D. (2019), https://doi.org/10.24432/C5CG6D.
- CDNOW master (Fader & Hardie), from brucehardie.com, falling back to the copy
  shipped with the `lifetimes` package on GitHub.
"""
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rfmfca.cdnow import CDNOW_FILE  # noqa: E402
from rfmfca.data import CSV_FILES, RAW_DIR  # noqa: E402

URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
SHEETS = ("Year 2009-2010", "Year 2010-2011")
CDNOW_URLS = (
    "https://www.brucehardie.com/datasets/CDNOW_master.zip",
    "https://raw.githubusercontent.com/CamDavidsonPilon/lifetimes/master/lifetimes/datasets/CDNOW_master.txt",
)


def fetch_cdnow():
    for url in CDNOW_URLS:
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                payload = resp.read()
        except OSError as exc:
            print(f"skip {url}: {exc}")
            continue
        if url.endswith(".zip"):
            archive = zipfile.ZipFile(io.BytesIO(payload))
            payload = archive.read(next(n for n in archive.namelist() if n.endswith(".txt")))
        (RAW_DIR / CDNOW_FILE).write_bytes(payload)
        print(f"wrote {RAW_DIR / CDNOW_FILE} from {url}")
        return
    raise SystemExit("could not download CDNOW")


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    fetch_cdnow()
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
