"""Accounting of the leaders' no-move fills: how many does each candidate driver claim?

    python3 study/hidden/account.py

No fitting. Order of attribution: (1) Binance book trigger (sign of perp + spot microprice change
0.21-0.33 s before the print) agrees with the side; (2) it points the other way; (3) perp and spot
disagree; (4) no Binance book change, then: repeat of the own last side within 0.6 s (burst), Polymarket book moved toward
the side at send time, or nothing. Also the inventory test: does the side balance the own position
(taker + maker fills, ms-stamped via the print of the same transaction)? And the A-after-B check.
Writes data/out/hidden/account.md."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from attrib import A, CACHE, ROOT, prints  # noqa: E402


def position_before(f: pd.DataFrame) -> np.ndarray:
    """Own net Up shares (taker + maker fills) strictly before each fill."""
    own = pd.read_pickle(CACHE / "own_5m.pkl")
    pr = prints()[["tx", "ts"]]
    own = own.merge(pr, left_on="transactionHash", right_on="tx", how="inner")
    own["q"] = np.where(own["outcome"] == "Up", 1, -1) * np.where(own["side"] == "BUY", 1, -1) * own["size"]
    own["wallet"] = np.where(own["who"] == "A", A, "B")
    out = np.full(len(f), np.nan)
    for (w, m), idx in f.groupby(["wallet_k", "market"]).groups.items():
        o = own[(own["wallet"] == w) & (own["condition_id"] == m)].sort_values("ts")
        c = np.r_[0, np.cumsum(o["q"].to_numpy())]
        i = np.searchsorted(o["ts"].to_numpy(), f.loc[idx, "ts"].to_numpy(), "left")
        out[f.index.get_indexer(idx)] = c[i]
    return out


def main() -> None:
    f = pd.read_pickle(CACHE / "feat.pkl")
    f = f[f["perp_micro_trig"].notna()].sort_values("ts").copy()
    f["who"] = np.where(f["wallet"] == A, "A", "B")
    f["wallet_k"] = np.where(f["who"] == "A", A, "B")
    grp = f.groupby(["who", "market"])
    f["gap"] = f["ts"] - grp["ts"].shift()
    f["same_prev"] = grp["d"].shift() == f["d"]
    comb = np.sign(f["perp_micro_trig"]) + np.sign(f["spot_micro_trig"].fillna(0))
    f["pos"] = position_before(f)
    lines = [f"# Who claims the no-move fills (|spot 3 s| < 0.2 bp, ms resolution, {f['hour'].nunique()} h with perp)\n",
             "| class | A | B |", "|---|---|---|"]
    cls = {}
    for who, g in f.groupby("who"):
        nm = g[g["spot_r3.0"].abs() < 0.2]
        c = comb.loc[nm.index]
        dis = np.sign(nm["perp_micro_trig"]) * np.sign(nm["spot_micro_trig"].fillna(0)) < 0
        none = nm[(c == 0) & ~dis]
        burst = (none["gap"] < 0.6) & none["same_prev"]
        book = ~burst & (none["book_r0.25"] > 0)
        cls[who] = {"no-move fills": len(nm),
                    "Binance book trigger, same side": (c > 0).mean(),
                    "Binance book trigger, opposite side": (c < 0).mean(),
                    "perp and spot book disagree": dis.mean(),
                    "  of which the side follows the perp": (nm.loc[dis, "perp_micro_trig"] > 0).mean(),
                    "no Binance book change: burst repeat (< 0.6 s, same side)": burst.sum() / len(nm),
                    "no Binance book change: Polymarket book moved their way": book.sum() / len(nm),
                    "no Binance book change: nothing found": (~burst & ~book).sum() / len(nm)}
        pos = nm["pos"] * nm["d"]
        cls[who]["inventory: side reduces the own imbalance"] = (pos[pos != 0] < 0).mean()
    for k in cls["A"]:
        a, b = cls["A"][k], cls["B"][k]
        fmt = (lambda v: f"{v:,}") if k == "no-move fills" else (lambda v: f"{v:.3f}")
        lines.append(f"| {k} | {fmt(a)} | {fmt(b)} |")
    out = ROOT / "data" / "out" / "hidden" / "account.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
