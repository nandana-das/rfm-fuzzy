"""Generate the LaTeX tables of paper/ from the result CSVs, so every number in the
manuscript comes straight from results/.  Usage: python scripts/make_paper_tables.py"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
R = ROOT / "results"
T = ROOT / "paper" / "tables"
DS = ("retail", "cdnow", "dunnhumby")
DS_NAME = {"retail": "Online Retail II", "cdnow": "CDNOW", "dunnhumby": "dunnhumby"}
NAMES = {"C-ctx": "Crisp scores (C-ctx)", "C-fca": "Crisp RFM-FCA (C-fca)", "F-ctx": "Fuzzy memberships (F-ctx)",
         "F-fca-core": "Fuzzy RFM-FCA (F-fca-core)", "logRFM": "log-RFM", "KM10": "K-means, $k{=}10$",
         "GMM10": "GMM, $k{=}10$", "FCM10": "FCM, $k{=}10$", "F-sel10": "Fuzzy summary, $K{=}10$",
         "C-sel10": "Crisp summary, $K{=}10$"}


def means(path, extra=None):
    d = pd.read_csv(path)
    if extra:
        d = d.query(extra)
    return d.groupby(["method", "metric"]).value.mean()


def write(name, body):
    (T / name).write_text(body)
    print("wrote", name)


def prediction_table():
    rows = ["C-ctx", "C-fca", "F-ctx", "F-fca-core", "logRFM", "KM10", "GMM10", "FCM10"]
    vals = {}
    for d in DS:
        m = means(R / "clustering" / f"{d}_prediction_per_origin.csv")
        core = pd.read_csv(R / ("extension/core_prediction_per_origin.csv" if d == "retail"
                                else f"{d}/prediction_per_origin.csv"))
        core = core.query("setting == 'tuned'").groupby(["method", "metric"]).value.mean()
        for meth in rows:
            for met in ("auc", "r2"):
                v = m.get((meth, met), core.get((meth, met)))
                if meth == "logRFM" and d == "retail":
                    v = m.get((meth, met))
                vals[(meth, met, d)] = v
    best = {(met, d): max(vals[(r, met, d)] for r in rows) for met in ("auc", "r2") for d in DS}
    lines = []
    for r in rows:
        cells = []
        for met in ("auc", "r2"):
            for d in DS:
                v = vals[(r, met, d)]
                s = f"{v:.3f}"
                cells.append(f"\\textbf{{{s}}}" if abs(v - best[(met, d)]) < 1e-12 else s)
        lines.append(f"{NAMES[r]} & " + " & ".join(cells) + r" \\")
    write("prediction.tex", r"""\begin{table}[t]
\centering\small
\caption{Out-of-sample prediction of the next 90 days (means over four cutoffs; regularisation tuned by inner cross-validation). Best value per column in bold.}
\label{tab:prediction}
\begin{tabular}{lcccccc}
\toprule
 & \multicolumn{3}{c}{ROC AUC (purchase)} & \multicolumn{3}{c}{$R^2$ (log spend)} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}
Representation & Retail II & CDNOW & dunnhumby & Retail II & CDNOW & dunnhumby \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def comparisons_table():
    """Key paired comparisons with CIs, tuned regularisation."""
    def get(path, a, b, metric, setting=None):
        d = pd.read_csv(path)
        q = (d.a == a) & (d.b == b) & (d.metric == metric)
        if setting is not None and "setting" in d:
            q &= d.setting == setting
        r = d[q].iloc[0]
        star = "$^{*}$" if (r.ci_low > 0 or r.ci_high < 0) else ""
        return f"{r.pooled_diff:+.4f}{star}"
    specs = [
        ("F-ctx", "C-ctx", "Fuzzification (memberships)"),
        ("F-fca-core", "C-fca", "Fuzzy vs crisp RFM-FCA"),
        ("F-fca-core", "F-ctx", "Lattice beyond memberships"),
        ("F-fca-core", "KM10", "vs K-means, $k{=}10$"),
        ("F-fca-core", "GMM10", "vs GMM, $k{=}10$"),
        ("F-fca-core", "FCM10", "vs FCM, $k{=}10$"),
    ]
    paths = {"retail": R / "extension/core_prediction_comparisons.csv",
             "cdnow": R / "cdnow/prediction_comparisons.csv",
             "dunnhumby": R / "dunnhumby/prediction_comparisons.csv"}
    lines = []
    for a, b, label in specs:
        cells = []
        for met in ("auc", "r2"):
            for d in DS:
                if b.endswith("10"):
                    path, setting = R / f"clustering/{d}_prediction_comparisons.csv", None
                else:
                    path, setting = paths[d], "tuned"
                    if a == "F-ctx" and d == "retail":
                        path = R / "extension/core_prediction_comparisons.csv"
                cells.append(get(path, a, b, met, setting))
        lines.append(f"{label} & " + " & ".join(cells) + r" \\")
    write("comparisons.tex", r"""\begin{table}[t]
\centering\small
\caption{Paired differences (first minus second representation), tuned regularisation, pooled over four cutoffs. $^{*}$: 95\,\% customer-bootstrap interval excludes zero.}
\label{tab:comparisons}
\begin{tabular}{lcccccc}
\toprule
 & \multicolumn{3}{c}{$\Delta$ AUC} & \multicolumn{3}{c}{$\Delta R^2$} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}
Comparison & Retail II & CDNOW & dunnhumby & Retail II & CDNOW & dunnhumby \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def structure_table():
    lines = []
    for m in ("C-fca", "F-fca-core", "KM10", "GMM10", "FCM10"):
        cells = []
        for kind in ("robustness", "stability"):
            for d in DS:
                s = pd.read_csv(R / f"clustering/{d}_structure_agreement_k10.csv").query("kind == @kind")
                cells.append(f"{s[m].mean():.3f}")
        lines.append(f"{NAMES[m]} & " + " & ".join(cells) + r" \\")
    write("structure.tex", r"""\begin{table}[t]
\centering\small
\caption{Structural agreement (correlation of customer-pair similarities between a reference fit and a perturbed fit; 1 = identical), mean over 20 replicates. Robustness: 5\,\% of invoices dropped. Stability: bootstrap resample of customers.}
\label{tab:structure}
\begin{tabular}{lcccccc}
\toprule
 & \multicolumn{3}{c}{Robustness} & \multicolumn{3}{c}{Stability} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}
Representation & Retail II & CDNOW & dunnhumby & Retail II & CDNOW & dunnhumby \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def targeting_table():
    lines = []
    for m in ("C-fca", "F-fca-core", "F-ctx", "logRFM", "KM10", "GMM10", "FCM10"):
        cells = []
        for met in ("rev10", "rev20"):
            for d in DS:
                v = means(R / f"business/{d}_per_origin.csv")[(m, met)]
                cells.append(f"{100 * v:.1f}")
        lines.append(f"{NAMES[m]} & " + " & ".join(cells) + r" \\")
    write("targeting.tex", r"""\begin{table}[t]
\centering\small
\caption{Share of next-90-day revenue (\%) held by the top 10\,\% and 20\,\% of customers ranked by predicted spend (means over four cutoffs).}
\label{tab:targeting}
\begin{tabular}{lcccccc}
\toprule
 & \multicolumn{3}{c}{Top 10\,\%} & \multicolumn{3}{c}{Top 20\,\%} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}
Representation & Retail II & CDNOW & dunnhumby & Retail II & CDNOW & dunnhumby \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def interpretability_table():
    s = pd.read_csv(R / "interpretability/summary.csv")
    lines = []
    for m in ("C-fca", "F-fca-core", "KM10", "GMM10", "FCM10"):
        g = s[s.method == m].set_index("dataset").loc[list(DS)]
        fmt = lambda col, f: " / ".join(f.format(v) for v in g[col])  # noqa: E731
        lines.append(f"{NAMES[m]} & {fmt('n_segments', '{:.0f}')} & {fmt('fidelity_f1', '{:.2f}')} & "
                     f"{fmt('description_length', '{:.1f}')} & {fmt('overlap', '{:.1f}')}" + r" \\")
    write("interpretability.tex", r"""\begin{table}[t]
\centering\small
\caption{Structural interpretability proxies on the full data (Retail II / CDNOW / dunnhumby). Fidelity: F1 between ``satisfies the segment's R/F/M description'' and ``is a member''. Conditions: constrained dimensions per description.}
\label{tab:interpretability}
\begin{tabular}{lcccc}
\toprule
Representation & Segments & Fidelity (F1) & Conditions & Segments per customer \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def summary_view_table():
    s = pd.read_csv(R / "selection/retail_selected_concepts.csv").query("method == 'F-sel10'")
    def tex(intent):
        return intent.replace("0.5/", r"$\tfrac12$").replace("{", r"\{").replace("}", r"\}")
    lines = [f"{r['rank']} & {tex(r.intent)} & {100 * r.core_share:.1f} & {100 * r.share_of_total_spend:.1f}" + r" \\"
             for _, r in s.iterrows()]
    write("summary_view.tex", r"""\begin{table}[t]
\centering\small
\caption{The 10-concept fuzzy summary of Online Retail II (greedy description-coverage selection, full data). $\tfrac12$X: partly in term X.}
\label{tab:summaryview}
\begin{tabular}{rlrr}
\toprule
\# & Intent & Customers fully in (\%) & Share of spend (\%) \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def sensitivity_table():
    d = pd.concat([pd.read_csv(R / f"sensitivity/{n}_sensitivity.csv").assign(dataset=n) for n in DS])
    d["cmp"] = d.a + " - " + d.b
    rows = []
    for cmp, label in (("F-fca-core - C-fca", "Fuzzy vs crisp RFM-FCA"), ("F-ctx - C-ctx", "Fuzzy vs crisp memberships")):
        g = d[d.cmp == cmp]
        rows.append(f"{label} & {int((g.ci_low > 0).sum())} / {len(g)} & {int((g.ci_high < 0).sum())}" + r" \\")
    g = d[d.cmp.str.startswith("F-sel")]
    rows.append(f"Fuzzy vs crisp summary ($K = 5, 10, 20, 30$) & {int((g.ci_low > 0).sum())} / {len(g)} & "
                f"{int((g.ci_high < 0).sum())}" + r" \\")
    write("sensitivity.tex", r"""\begin{table}[t]
\centering\small
\caption{Sensitivity analysis: number of setting $\times$ dataset $\times$ metric cells in which the fuzzy variant is significantly better (95\,\% interval above zero) and significantly worse. Settings: support 0.02/0.04/0.06, membership half-width 0.15/0.20/0.25, horizon 60/90/180 days.}
\label{tab:sensitivity}
\begin{tabular}{lcc}
\toprule
Comparison & Fuzzy significantly better & Significantly worse \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def main():
    T.mkdir(parents=True, exist_ok=True)
    prediction_table(); comparisons_table(); structure_table(); targeting_table()
    interpretability_table(); summary_view_table(); sensitivity_table()


if __name__ == "__main__":
    main()
