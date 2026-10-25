# Manuscript

`main.tex` (Elsevier `elsarticle`, target: *Expert Systems with Applications*) with sections in
`sections/`, tables in `tables/` and figures in `figures/`.

Tables and figures are generated from `results/` — never edit them by hand:

```bash
python scripts/make_paper_tables.py
python scripts/make_paper_figures.py
```

Compile on Overleaf or locally (`latexmk -pdf main.tex`). A Word copy for reading/commenting:

```bash
cd paper && pandoc main.tex -f latex -t docx --citeproc --bibliography=refs.bib --metadata-file=docx-meta.yaml -o manuscript.docx
```

The propositions of `sections/method.tex` are checked numerically in `tests/test_theory.py`.

Still to do before submission:
competing-interests confirmation, cover letter, and a final language edit.
