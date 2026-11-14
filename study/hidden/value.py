"""What is each trigger class worth? Markout of the leaders' taker buys by trigger class.

    nice -n 10 python3 study/hidden/value.py

Markout per $ = (Up-book mid of the side bought at tau + k s - price paid - taker fee at our 0%
tier) / price paid, k in {2, 10}. Classes as in account.py (Binance book trigger same / opposite /
split / none) crossed with move vs no-move (|spot 3 s| >= 0.2 bp). Also how the ask moves during Polymarket's 150 ms taker
hold and what they pay relative to the ask at send time. Writes data/out/hidden/value.md."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import series  # noqa: E402
from attrib import A, CACHE, ROOT  # noqa: E402


def marks(f: pd.DataFrame) -> pd.DataFrame:
    out = []
    for h, g in f.groupby("hour"):
        d = series.load(h + 1) if (CACHE / "prep" / f"{h + 1}.pkl").exists() else series.load(h)
        lag = float(np.nanmedian(d["prints"]["t"] - d["prints"]["ts"]))
        for cid, gg in g.groupby("market"):
            bt = series.book_tops(d, cid, lag)
            tau, dd = gg["ts"].to_numpy(), gg["d"].to_numpy()
            paid = np.where(dd > 0, gg["price_up"], 1 - gg["price_up"])
            r = {"paid": paid, "usd": paid * gg["size"].to_numpy(),
                 "ask_send": np.where(dd > 0, bt["ba"].at(tau - 0.27), 1 - bt["bb"].at(tau - 0.27)),
                 "ask_pre": np.where(dd > 0, bt["ba"].at(tau - 0.05), 1 - bt["bb"].at(tau - 0.05))}
            for k in (2, 10):
                mid = (bt["bb"].at(tau + k) + bt["ba"].at(tau + k)) / 2
                mk = np.where(dd > 0, mid, 1 - mid)
                r[f"pnl{k}"] = gg["size"].to_numpy() * (mk - paid - 0.07 * paid * (1 - paid))
            out.append(pd.DataFrame(r, index=gg.index))
    return f.join(pd.concat(out))


def main() -> None:
    f = pd.read_pickle(CACHE / "feat.pkl")
    f = f[f["perp_micro_trig"].notna()].copy()
    f = marks(f)
    f["who"] = np.where(f["wallet"] == A, "A", "B")
    p, s = np.sign(f["perp_micro_trig"]), np.sign(f["spot_micro_trig"].fillna(0))
    f["cls"] = np.select([(p * s < 0), (p + s) > 0, (p + s) < 0], ["split", "same", "opposite"], "none")
    f["move"] = np.where(f["spot_r3.0"].abs() < 0.2, "no-move", "move")
    t = f.groupby(["who", "move", "cls"]).agg(fills=("usd", "size"), usd=("usd", "sum"),
                                                pnl2=("pnl2", "sum"), pnl10=("pnl10", "sum"))
    t["c_per_usd_2s"] = 100 * t["pnl2"] / t["usd"]
    t["c_per_usd_10s"] = 100 * t["pnl10"] / t["usd"]
    lines = ["# Markout by trigger class (0% tier fee), c per $\n",
             "| who | move | Binance book trigger | fills | USD | c/$ at 2 s | c/$ at 10 s |",
             "|---|---|---|---|---|---|---|"]
    for (who, mv, cls), r in t.iterrows():
        lines.append(f"| {who} | {mv} | {cls} | {r.fills:.0f} | {r.usd:,.0f} | {r.c_per_usd_2s:+.2f} | "
                     f"{r.c_per_usd_10s:+.2f} |")
    lines += ["\n## The 150 ms hold: ask of the side bought at send time (print - 0.27 s) vs 50 ms before the print\n"]
    for who, g in f.groupby("who"):
        mv = 100 * (g["ask_pre"] - g["ask_send"])
        slip = 100 * (g["paid"] - g["ask_send"])
        lines.append(f"- {who}: ask moved >= 1 c against {np.mean(mv >= 0.99):.2f}, >= 1 c in favour "
                     f"{np.mean(mv <= -0.99):.2f}; paid minus ask at send: mean {slip.mean():+.2f} c, "
                     f"p10 / p50 / p90 {np.nanpercentile(slip, 10):+.0f} / {np.nanpercentile(slip, 50):+.0f} / "
                     f"{np.nanpercentile(slip, 90):+.0f} c")
    (ROOT / "data" / "out" / "hidden" / "value.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
