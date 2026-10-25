"""Figures for paper/ from results/.  Usage: python scripts/make_paper_figures.py"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
R, F = ROOT / "results", ROOT / "paper" / "figures"
DS = ("retail", "cdnow", "dunnhumby")
DS_NAME = {"retail": "Online Retail II", "cdnow": "CDNOW", "dunnhumby": "dunnhumby"}
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False})


def gain_curves():
    series = [("F-fca-core", "Fuzzy RFM-FCA", BLUE, "-"), ("C-fca", "Crisp RFM-FCA", ORANGE, "--"),
              ("FCM10", "FCM, k = 10", AQUA, "-."), ("KM10", "K-means, k = 10", YELLOW, ":")]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6), sharey=False)
    for ax, d in zip(axes, DS):
        g = pd.read_csv(R / f"business/{d}_gain_curve.csv").query("pct_contacted <= 40")
        ax.plot([0, 40], [0, 0.4], color=MUTED, lw=1, ls=(0, (1, 2)), label="Random")
        for m, label, color, ls in series:
            s = g[g.method == m]
            ax.plot(s.pct_contacted, s.revenue_share, color=color, lw=2, ls=ls, label=label)
        ax.set_title(DS_NAME[d], fontsize=9, color=INK)
        ax.set_xlabel("Customers contacted (%)")
        ax.set_xlim(0, 40)
        ax.set_ylim(0, 1)
    axes[0].set_ylabel("Share of next-90-day revenue")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, fontsize=7.5, bbox_to_anchor=(0.5, 0))
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(F / "gain_curves.pdf")
    fig.savefig(F / "gain_curves.png", dpi=200)
    plt.close(fig)


def sensitivity_forest():
    d = pd.concat([pd.read_csv(R / f"sensitivity/{n}_sensitivity.csv").assign(dataset=n) for n in DS])
    d = d[(d.a == "F-fca-core") & (d.b == "C-fca")]
    label = {("support", 0.02): "support 0.02", ("support", 0.04): "support 0.04 (default)",
             ("support", 0.06): "support 0.06", ("half_width", 0.15): "half-width 0.15",
             ("half_width", 0.25): "half-width 0.25", ("horizon", 60): "horizon 60 d", ("horizon", 180): "horizon 180 d"}
    order = list(label)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
    styles = {"retail": (BLUE, "o"), "cdnow": (ORANGE, "s"), "dunnhumby": (AQUA, "D")}
    for ax, met, title in zip(axes, ("auc", "r2"), ("Δ ROC AUC", "Δ R²")):
        ax.axvline(0, color=MUTED, lw=1)
        for k, ds in enumerate(DS):
            color, marker = styles[ds]
            for i, key in enumerate(order):
                r = d[(d.dataset == ds) & (d.metric == met) & (d.factor == key[0]) & (d.value == key[1])]
                if r.empty:
                    continue
                r = r.iloc[0]
                y = i + (k - 1) * 0.22
                ax.plot([r.ci_low, r.ci_high], [y, y], color=color, lw=1.5)
                ax.plot(r.pooled_diff, y, marker=marker, color=color, ms=5, ls="none",
                        label=DS_NAME[ds] if i == 0 else None)
        ax.set_title(title, fontsize=9, color=INK)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels([label[k] for k in order])
        ax.grid(axis="y", visible=False)
        ax.margins(x=0.06)
    axes[0].invert_yaxis()   # shared y: invert once
    axes[0].set_xlabel("Fuzzy minus crisp RFM-FCA")
    axes[1].set_xlabel("Fuzzy minus crisp RFM-FCA")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=7.5, bbox_to_anchor=(0.5, 0))
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(F / "sensitivity.pdf")
    fig.savefig(F / "sensitivity.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    F.mkdir(parents=True, exist_ok=True)
    gain_curves()
    sensitivity_forest()
    print("figures written")
