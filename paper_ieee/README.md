# IEEE version of the manuscript

`IEEEtran` (two-column, conference mode), ~2,000 words, 6 tables, 1 figure: about 5–6 pages.
For an IEEE journal, change the first line to `\documentclass[journal]{IEEEtran}`.

Tables come from `results/` via the generators:

```bash
python scripts/make_paper_tables.py && python scripts/make_ieee_tables.py
python scripts/make_paper_figures.py && cp paper/figures/sensitivity.pdf paper_ieee/figures/
```

Overleaf bundle: `cd paper_ieee && zip -r rfm-fuzzy-ieee-overleaf.zip main.tex refs.bib tables figures`.
