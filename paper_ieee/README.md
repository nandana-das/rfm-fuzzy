# IEEE version of the manuscript

`IEEEtran` (two-column, conference mode), ~2,500 words, 7 tables, 2 figures: about 6 pages.
For an IEEE journal, change the first line to `\documentclass[journal]{IEEEtran}`.

Tables come from `results/` via the generators:

```bash
python scripts/make_paper_tables.py && python scripts/make_ieee_tables.py
python scripts/make_paper_figures.py && cp paper/figures/{sensitivity,gain_curves}.pdf paper_ieee/figures/
```

Overleaf bundle: `cd paper_ieee && zip -r rfm-fuzzy-ieee-overleaf.zip main.tex refs.bib tables figures`.
