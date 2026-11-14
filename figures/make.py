"""Net result per dollar traded at each Polymarket taker-rebate tier.

net(r) = g - f * (1 - r),  f = 0.07 * (1 - p)
g: gross edge per dollar traded, p: price paid per share, r: share of the fee returned.
"""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

G = 2.44          # cents of gross edge per dollar traded (measured, 5-minute BTC markets)
P = 0.57          # typical price paid per share
TIERS = [0, 3, 8, 18, 32, 44, 50]           # percent of the taker fee returned
TOP_WEIGHTED = 10e6                          # weighted 30-day volume the 50% tier needs
F = 7.0 * (1 - P)                            # fee in cents per dollar traded
VOLUME = TOP_WEIGHTED / ((1 - P) / P * 2.3)  # dollars traded per 30 days at that weight


def net(r_pct):
    return G - F * (1 - r_pct / 100)


def main():
    be = 100 * (1 - G / F)
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=160)
    xs = [x / 10 for x in range(0, 501)]
    ax.plot(xs, [net(x) for x in xs], color="#888888", lw=1.2, zorder=1)
    for t in TIERS:
        n = net(t)
        c = "#1b7837" if n > 0 else "#b2182b"
        ax.scatter([t], [n], s=60, color=c, zorder=3)
        ax.annotate(f"{n:+.2f}", (t, n), textcoords="offset points", xytext=(0, 9),
                    ha="center", fontsize=9, color=c)
    ax.axhline(0, color="black", lw=0.8)
    ax.axvline(be, color="black", lw=0.8, ls=":")
    ax.annotate(f"break-even: {be:.0f}% returned", (be, net(0)), xytext=(4, 0),
                textcoords="offset points", fontsize=9, va="bottom")
    ax.set_xticks(TIERS)
    ax.set_xlabel("Share of the taker fee returned by the volume tier (%)")
    ax.set_ylabel("Net result (cents per dollar traded)")
    ax.set_title("The same trade loses at the entry tier and earns at the top tier",
                 fontsize=11, loc="left")
    ax2 = ax.twinx()
    lo, hi = ax.get_ylim()
    ax2.set_ylim(lo * VOLUME / 100 / 1000, hi * VOLUME / 100 / 1000)
    ax2.set_ylabel(f"Per 30 days at \\${VOLUME / 1e6:.1f}M traded (thousand \\$)")
    for s in ("top",):
        ax.spines[s].set_visible(False); ax2.spines[s].set_visible(False)
    fig.tight_layout()
    out = pathlib.Path(__file__).parent / "net_vs_rebate.png"
    fig.savefig(out)
    print(f"fee={F:.2f} c/$  volume=${VOLUME:,.0f}  break-even={be:.1f}%")
    for t in TIERS:
        print(f"tier {t:>2}%: net {net(t):+.3f} c/$  = ${net(t) / 100 * VOLUME:+,.0f} per 30 days")


if __name__ == "__main__":
    main()
