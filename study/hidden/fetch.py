"""Pull the Data API taker fills of every recorded 5m BTC market (read-only).

    python3 study/hidden/fetch.py

One row per taker fill: tx hash, wallet, asset, side, size, price, second stamp. These carry the
wallet identity the CLOB websocket lacks; attrib.py joins them to the ms-stamped live prints.
Closed markets are cached on disk (btclat.api.http); throttled to ~5 req/s.
Also every fill (taker and maker) of the two leaders, for their position state.
Output: data/cache/hidden/taker_5m.pkl, own_5m.pkl"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "bot" / "python"))  # btclat.api lives under bot/python
sys.path.insert(0, str(ROOT / "latency" / "leadlag"))
from btclat.api import http  # noqa: E402
from btclat.api.data import market_trades  # noqa: E402
from btclat.api.http import DATA, get  # noqa: E402
import load  # noqa: E402

http.MIN_INTERVAL = 0.2
OUT = ROOT / "data" / "cache" / "hidden"
LEADERS = {"A": "0xc53375ff94e96100f2b30a4b5775db35218d69a9",
           "B": "0x3048d65321be3497164cdfc2996f94f98a2e7537"}
COLS = ["transactionHash", "proxyWallet", "asset", "side", "size", "price", "timestamp", "outcome"]


def main() -> None:
    mk = load.markets()
    mk = mk[(mk["fam"] == "5m") & (mk["end"] < time.time() + 12 - 300)]
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, m in enumerate(mk.itertuples()):
        tr = market_trades(m.condition_id, taker_only=True, cache=True)
        df = pd.DataFrame(tr)
        if len(df):
            df = df[COLS].assign(condition_id=m.condition_id, slug=m.slug)
            rows.append(df)
        if i % 20 == 0:
            print(i, len(mk), m.slug, len(df), flush=True)
    out = pd.concat(rows, ignore_index=True)
    out.to_pickle(OUT / "taker_5m.pkl")
    print("fills", len(out), "markets", out["condition_id"].nunique())
    own = []
    for m in mk.itertuples():
        for name, w in LEADERS.items():
            page = get(DATA, "/trades", {"market": m.condition_id, "user": w, "limit": 1000,
                                         "offset": 0, "takerOnly": "false"}, cache=True)
            if page:
                own.append(pd.DataFrame(page)[COLS].assign(condition_id=m.condition_id, who=name))
    own = pd.concat(own, ignore_index=True)
    own.to_pickle(OUT / "own_5m.pkl")
    print("leader fills (taker + maker)", own.groupby("who").size().to_dict())


if __name__ == "__main__":
    main()
