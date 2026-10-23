"""Plan addendum D: confirmation on dunnhumby "The Complete Journey".

Same analysis as scripts/confirm_cdnow.py (addendum B), with the dunnhumby data,
cutoffs and claim labels. Writes results/dunnhumby/*.csv (aggregate results only).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import confirm_cdnow as cd  # noqa: E402
from rfmfca.dunnhumby import day_to_date, load_dunnhumby  # noqa: E402

cd.OUT = ROOT / "results" / "dunnhumby"
cd.CUTOFFS = [str(day_to_date(d).date()) for d in (351, 441, 531, 621)]
cd.CONFIRMATORY = [(claim.replace("B", "D"), *rest) for claim, *rest in cd.CONFIRMATORY]
cd.load_cdnow = load_dunnhumby
ROBUSTNESS_LABELS = {"B4a": "D4a", "B4b": "D4b"}


def main():
    cd.OUT.mkdir(parents=True, exist_ok=True)
    tx = load_dunnhumby()
    cd.structure(tx)
    cd.robustness(tx)
    claims_path = cd.OUT / "robustness_claims.csv"
    text = claims_path.read_text()
    for old, new in ROBUSTNESS_LABELS.items():
        text = text.replace(old, new)
    claims_path.write_text(text)
    cd.prediction(tx)


if __name__ == "__main__":
    main()
