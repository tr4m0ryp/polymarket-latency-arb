"""Find every latency-style wallet in the BTC up/down families.

    python3 study/fingerprint.py [family ...]

Writes data/out/latency/wallets.csv (one row per wallet x family, every
wallet with >= 10 markets in the family, fingerprint columns + class),
data/out/latency/wallet_rollup.csv (latency wallets summed over families) and
data/out/latency/family_baseline.csv (family-wide taker alignment, so a
wallet's align3 can be read against what an average taker shows).
Classification rules live in classify.py."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from aggregate import _w, wallet_table
from classify import classify, write
from features import family_frame

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "out" / "latency"
FAMILIES = ["btc-up-or-down-5m", "btc-up-or-down-15m", "btc-up-or-down-hourly",
            "btc-up-or-down-4h", "btc-up-or-down-daily"]


def baseline(f: pd.DataFrame) -> dict:
    tk = f[f["taker"] == 1]
    return {"series": f["series"].iloc[0], "n_fills": len(f), "taker_usd": tk["usd"].sum(),
            "taker_align1": _w(tk, "r1"), "taker_align3": _w(tk, "r3"),
            "taker_align10": _w(tk, "r10"), "taker_align_post": _w(tk, "rf10"),
            "spot_outcome_agree": f.attrs.get("spot_outcome_agree", np.nan)}


def main(families: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tabs, base = [], []
    for slug in families:
        t0 = time.time()
        f, mk = family_frame(slug)
        base.append(baseline(f))
        tabs.append(wallet_table(f, len(mk)))
        print(f"{slug}: {len(mk)} markets, {len(tabs[-1])} wallets, "
              f"{time.time() - t0:.0f}s", flush=True)
        del f
    w = pd.concat(tabs, ignore_index=True)
    sc = pd.read_csv(ROOT / "data" / "out" / "wallet_scores.csv",
                     usecols=["wallet", "series", "copy_keep2", "copy_keep10",
                              "copy_keep60", "t_event", "t_A", "t_B", "q", "style"])
    w = w.merge(sc, on=["wallet", "series"], how="left")
    w = write(classify(w), OUT)
    pd.DataFrame(base).to_csv(OUT / "family_baseline.csv", index=False, float_format="%.6g")
    print(w["latency_class"].value_counts().to_string())


if __name__ == "__main__":
    main(sys.argv[1:] or FAMILIES)
