"""Peers and followers of the BTC latency bots.

    python3 study/peers

Writes data/out/latency/peers_{speed,pairs,followers,lagcurve,followcurve,opcorr}.csv;
report.py turns them into data/out/latency/peers.md."""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from bursts import ROOT, burst_table, taker_frame
from ops import market_corr
from follow import follow_pnl_curve, follower_table
from speed import lag_curve, pair_order, wallet_speed

OUT = ROOT / "data" / "out" / "latency"
FAMILIES = ["btc-up-or-down-5m", "btc-up-or-down-15m", "btc-up-or-down-hourly",
            "btc-up-or-down-4h", "btc-up-or-down-daily"]


def main() -> None:
    w = pd.read_csv(OUT / "wallets.csv")
    out = {k: [] for k in ("speed", "pairs", "followers", "lagcurve", "followcurve", "opcorr")}
    for slug in FAMILIES:
        t = time.time()
        fam = w[w["series"] == slug].set_index("wallet")
        lat_w = set(fam.index[fam["latency_class"] != "none"])
        f = taker_frame(slug)
        lat, other = f[f["wallet"].isin(lat_w)], f[~f["wallet"].isin(lat_w)]
        bt = burst_table(lat)
        sp = wallet_speed(bt)
        sp = sp.join(fam[["latency_class", "pnl", "volume_usd", "n_markets"]], on="wallet")
        out["speed"].append(sp.assign(series=slug))
        big = sp.loc[sp["contested"] >= 100, "wallet"].tolist()
        out["pairs"].append(pair_order(bt, big).assign(series=slug))
        fo = follower_table(other, bt)
        fo = fo.join(fam[["latency_class"]], on="wallet")
        out["followers"].append(fo.assign(series=slug))
        out["lagcurve"].append(lag_curve(bt).assign(series=slug))
        out["followcurve"].append(follow_pnl_curve(other, bt).assign(series=slug))
        # operator test on every latency-style wallet that matters in this family
        cand = fam.index[(fam["latency_class"] != "none")
                         & ((fam["pnl"].abs() >= 300) | (fam["volume_usd"] >= 20000))]
        out["opcorr"].append(market_corr(slug, list(cand)))
        print(f"{slug}: {bt['burst'].nunique()} bursts, {len(sp)} speed rows, "
              f"{len(fo)} other wallets, {time.time() - t:.0f}s", flush=True)
        del f, lat, other, bt
    for k, v in out.items():
        pd.concat(v, ignore_index=True).to_csv(OUT / f"peers_{k}.csv", index=False,
                                               float_format="%.6g")


if __name__ == "__main__":
    np.seterr(all="ignore")
    main()
