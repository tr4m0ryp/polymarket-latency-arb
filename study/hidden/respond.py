"""How strongly does a Binance book event trigger the leaders?

    nice -n 10 python3 study/hidden/respond.py      (needs hazard.py's grid.pkl)

(1) Dose-response: fire rate per 1,000 50 ms bins by the size of the perp microprice change in
the trigger window, and by favourite price given a strong trigger (>= 0.002 bp).
(2) Conversion: share of perp mid ticks in active markets (favourite < 0.90, > 30 s left) followed
by a same-side fill 0.15-0.45 s later, by time since the own last fill, spread, and the Polymarket
book move in the 100 ms after the tick. Writes data/out/hidden/respond.md."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "latency" / "leadlag"))
import load  # noqa: E402
import series  # noqa: E402
from attrib import A, B, CACHE, ROOT  # noqa: E402
from irf import events  # noqa: E402

SIZE = [-1, 1e-6, 1e-4, 5e-4, 2e-3, 1e-2, 5e-2, 0.2, 100]


def dose(lines: list[str]) -> None:
    g = pd.read_pickle(CACHE / "grid.pkl")
    g = g[g["perp_micro_trig"].notna()]
    b = pd.cut(g["perp_micro_trig"], SIZE)
    t = g.groupby(b, observed=True).agg(bins=("y_A", "size"), A=("y_A", "mean"), B=("y_B", "mean"))
    lines += ["## Fire rate per 1,000 bins by |perp microprice change| in the trigger window (bp)\n",
              "| change | bins | A | B |", "|---|---|---|---|"]
    lines += [f"| {k} | {r.bins:,} | {1000 * r.A:.1f} | {1000 * r.B:.1f} |" for k, r in t.iterrows()]
    m = g["perp_micro_trig"] >= 2e-3
    fav = pd.cut(g.loc[m, "fav"], [-0.01, 0.1, 0.2, 0.3, 0.4, 0.5])
    t = g[m].groupby(fav, observed=True)[["y_A", "y_B"]].mean() * 1000
    lines += ["\nstrong trigger (>= 0.002 bp), by |favourite - 0.5|:\n", "| fav | A | B |", "|---|---|---|"]
    lines += [f"| {k} | {r.y_A:.1f} | {r.y_B:.1f} |" for k, r in t.iterrows()]


def conversion(lines: list[str]) -> None:
    fl = pd.read_pickle(CACHE / "fills_5m.pkl")
    fl = fl[fl["buy"] == 1].sort_values("ts")
    mk = load.markets()
    mk = mk[mk["fam"] == "5m"]
    rows = []
    for h in sorted(int(p.stem) for p in (CACHE / "prep").glob("*.pkl")):
        d = series.load(h)
        if "perp_bk" not in d or not len(d["perp_bk"]):
            continue
        s = series.build(d)
        pb = d["perp_bk"][lambda x: (x["ts"] >= h * 3600) & (x["ts"] < (h + 1) * 3600)]
        et, es = events(pb["ts"].to_numpy(), 1e4 * np.log((pb["bid"] + pb["ask"]) / 2).to_numpy(), 1e-6)
        for m in mk[(mk["end"] > h * 3600) & (mk["start"] < (h + 1) * 3600)].itertuples():
            sel = (et > m.start + 5) & (et < m.end - 30)
            mf = fl[fl["market"] == m.condition_id]
            if not sel.any() or not len(mf):
                continue
            e, sg = et[sel], es[sel]
            bt = series.book_tops(d, m.condition_id, s["lag_clob"])
            mid0 = (bt["bb"].at(e) + bt["ba"].at(e)) / 2
            r = {"fav": np.abs(mid0 - 0.5), "spread": bt["ba"].at(e) - bt["bb"].at(e),
                 "book100": sg * 100 * ((bt["bb"].at(e + 0.1) + bt["ba"].at(e + 0.1)) / 2 - mid0)}
            for name, w in (("A", A), ("B", B)):
                x = mf[mf["wallet"] == w]
                ts, dd = x["ts"].to_numpy(), x["d"].to_numpy()
                lo, hi = np.searchsorted(ts, e + 0.15), np.searchsorted(ts, e + 0.45)
                r[f"resp_{name}"] = np.array([np.any(dd[a:b] == q) for a, b, q in zip(lo, hi, sg)])
                # first same-side fill -0.2..0.6 s around the tick: delay and perp imbalance at its send time
                lo2, hi2 = np.searchsorted(ts, e - 0.2), np.searchsorted(ts, e + 0.6)
                fd = np.full(len(e), np.nan)
                for j, (a, b, q) in enumerate(zip(lo2, hi2, sg)):
                    k = np.flatnonzero(dd[a:b] == q)
                    if len(k):
                        fd[j] = ts[a + k[0]] - e[j]
                r[f"delay_{name}"] = fd
                r[f"imb_send_{name}"] = sg * s["perp_imb"].at(e + np.nan_to_num(fd) - 0.27)
                r[f"since_{name}"] = e - np.r_[-np.inf, ts][np.searchsorted(ts, e)]
            r["imb_1s"] = sg * s["perp_imb"].at(e - 1.0)
            rows.append(pd.DataFrame(r))
    x = pd.concat(rows)
    x = x[x["fav"] < 0.4]
    lines += [f"\n## Conversion of perp mid ticks in active markets (n = {len(x):,})\n",
              f"same-side fill 0.15-0.45 s later: A {x['resp_A'].mean():.3f}, B {x['resp_B'].mean():.3f}, "
              f"either {(x['resp_A'] | x['resp_B']).mean():.3f}\n"]
    lines += ["perp imbalance in the tick's direction at the fill's send time (print - 0.27 s), by delay; "
              "fills < 150 ms after the tick were sent before it:\n", "| delay ms | A n | A imbalance | B n | B imbalance |",
              "|---|---|---|---|---|"]
    for a, b in ((-200, 0), (0, 150), (150, 250), (250, 350), (350, 600)):
        cells = []
        for w in "AB":
            m = (x[f"delay_{w}"] * 1000 >= a) & (x[f"delay_{w}"] * 1000 < b)
            cells += [f"{m.sum()}", f"{x.loc[m, f'imb_send_{w}'].mean():+.2f}"]
        lines.append(f"| {a} to {b} | " + " | ".join(cells) + " |")
    lines.append(f"\nbaseline: imbalance 1 s before any tick, in the tick's direction: {x['imb_1s'].mean():+.2f}\n")
    for col, bins in (("since_A", [0, 0.5, 1, 2, 4, 10, 30, 1e9]), ("spread", [0, 0.011, 0.021, 0.031, 1]),
                      ("book100", [-10, -0.5, 0.5, 1.5, 10])):
        t = x.groupby(pd.cut(x[col], bins), observed=True)[["resp_A", "resp_B"]].agg(["mean", "size"])
        lines += [f"| {col} | n | A | B |", "|---|---|---|---|"]
        lines += [f"| {k} | {r[('resp_A', 'size')]} | {r[('resp_A', 'mean')]:.3f} | {r[('resp_B', 'mean')]:.3f} |"
                  for k, r in t.iterrows()]
        lines.append("")


def main() -> None:
    lines = ["# Trigger strength and conversion\n"]
    dose(lines)
    conversion(lines)
    (ROOT / "data" / "out" / "hidden" / "respond.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
