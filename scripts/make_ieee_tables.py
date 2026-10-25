"""IEEE (two-column) versions of the paper tables: run make_paper_tables.py first.
Wide tables become table*, fonts \\footnotesize.  Usage: python scripts/make_ieee_tables.py"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, DST = ROOT / "paper" / "tables", ROOT / "paper_ieee" / "tables"
WIDE = {"prediction", "comparisons", "structure", "targeting", "interpretability"}
NARROW = {"sensitivity"}


def main():
    DST.mkdir(parents=True, exist_ok=True)
    for name in WIDE | NARROW:
        t = (SRC / f"{name}.tex").read_text().replace(r"\small", r"\footnotesize")
        if name in WIDE:
            t = t.replace(r"\begin{table}[t]", r"\begin{table*}[t]").replace(r"\end{table}", r"\end{table*}")
        else:
            t = t.replace(r"\begin{table}[t]", r"\begin{table}[t]").replace(r"\begin{tabular}{lcc}", r"\begin{tabular}{p{3.3cm}cc}")
            t = t.replace(r"\begin{tabular}{lcccc}", r"\setlength{\tabcolsep}{3pt}\begin{tabular}{p{2.1cm}cccc}")
            t = t.replace("Segments per customer", "Segs./cust.").replace("Fidelity (F1)", "Fidelity")
        # IEEE puts table captions above; already so. Shorten long row labels.
        t = t.replace("Crisp scores (C-ctx)", "C-ctx").replace("Crisp RFM-FCA (C-fca)", "C-fca (base)")
        t = t.replace("Fuzzy memberships (F-ctx)", "F-ctx").replace("Fuzzy RFM-FCA (F-fca-core)", "F-fca-core (ours)")
        (DST / f"{name}.tex").write_text(t)
        print("wrote", name)


if __name__ == "__main__":
    main()
