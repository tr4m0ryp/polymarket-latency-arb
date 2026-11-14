"""figures/bounds.png: net dollars per 30 days by fee-refund tier when orders must survive
the venue's taker delay. Reads backrun/results.json (python -m backrun.report.run)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

HERE = Path(__file__).resolve().parent
B = json.loads((HERE.parent / "backrun" / "results.json").read_text())["bounds"]
BLUE, ORANGE, GREEN, GREY = "#0072B2", "#D55E00", "#009E73", "#555555"   # Okabe-Ito


def series(key):
    d = B[key]["net_30d_by_tier_pct"]
    x = np.array(sorted(int(k) for k in d))
    return x, np.array([d[str(k)] for k in x]) / 1e3


def main():
    x, up = series("upper")
    _, mid = series("central_shifted")
    _, raw = series("central_raw")
    _, low = series("lower")
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=160)
    ax.fill_between(x, np.minimum.reduce([mid, low, up]), np.maximum.reduce([mid, low, up]),
                    color=BLUE, alpha=0.10, lw=0)
    ax.axhline(0, color="black", lw=0.8)
    f = lambda k: 100 * B[k]["fill_rate_dollars"]   # noqa: E731
    ax.plot(x, up, color=BLUE, lw=2, marker="o", ms=4,
            label="every order fills, edge 2.44 c/\\$ (upper)")
    ax.plot(x, low, color=GREEN, lw=2, marker="s", ms=4,
            label=f"live run: {f('lower'):.0f}% of dollars fill, edge {B['lower']['gross_edge_cpd']:.1f} c/\\$".replace("-0.0", "0.0"))
    ax.plot(x, mid, color=ORANGE, lw=2, marker="^", ms=4,
            label=f"replay at 165 ms: {f('central_shifted'):.0f}% fill, edge {B['central_shifted']['gross_edge_cpd']:+.1f} c/\\$")
    ax.plot(x, raw, color=GREY, lw=1.2, ls="--",
            label=f"replay at 165 ms, unscaled: edge {B['central_raw']['gross_edge_cpd']:+.1f} c/\\$")
    for y, c, dy in ((up[-1], BLUE, 6), (low[-1], GREEN, -13), (mid[-1], ORANGE, 6)):
        ax.annotate(f"{'+' if y > 0 else '-'}\\${abs(y):.1f}k", (x[-1], y), xytext=(-2, dy),
                    textcoords="offset points", ha="right", fontsize=8.5, color=c, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{k}%" for k in x])
    ax.set_xlim(-2, 52)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{'-' if v < 0 else ''}\\${abs(v):.0f}k"))
    ax.set_xlabel("share of the taker fee returned (tier)")
    ax.set_ylabel("net per 30 days at the \\$5.76M order flow")
    ax.set_title("Once orders must survive the taker delay, no refund tier is profitable:\n"
                 "the orders that still fill earn about 0 c/\\$ before fees",
                 loc="left", fontsize=10.5, fontweight="bold")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#dddddd", lw=0.6)
    ax.set_axisbelow(True)
    ax.set_ylim(top=95)
    ax.legend(loc="upper left", fontsize=7.8, frameon=False, borderaxespad=0.2)
    fig.tight_layout()
    fig.savefig(HERE / "bounds.png", dpi=160)


if __name__ == "__main__":
    main()
