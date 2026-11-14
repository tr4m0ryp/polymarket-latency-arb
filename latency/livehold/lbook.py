"""Replay the books at the leaders' own matches (venue clock), one tape hour per worker.

Each leader fill is matched to the tape's `last_trade_price` by transaction hash (venue match
time). For each, the book of the bought token is read 250 ms before (about when a held taker
order was sent) and 1 ms before the match, and the mid 10 s after it.

    PYTHONPATH=. python3 -m latency.livehold.lbook   -> data/out/livehold/leaders_rows.pkl"""
from __future__ import annotations

import gzip
import json
from collections import defaultdict
from multiprocessing import Pool

import pandas as pd

from . import OUT, TAPE
from .replay import Replay, best

PAD = 20.0


def _events(h: int, txs: set[str]):
    """Per-token venue-time streams for hour h (+ PAD s of h+1) and the leader matches in it."""
    ev, hits = defaultdict(list), []
    for hh, cut in ((h, None), (h + 1, (h + 1) * 3600 + PAD)):
        p = TAPE / f"clob_5m-{hh}.tsv.gz"
        if not p.exists():
            continue
        with gzip.open(p, "rt") as fh:
            for line in fh:
                d = json.loads(line.split("\t", 1)[1])
                for e in (d if isinstance(d, list) else [d]):
                    k, ts = e.get("event_type"), e.get("timestamp")
                    if ts is None:
                        continue
                    t = int(ts) / 1000
                    if cut is not None and t > cut:
                        continue
                    if k == "book":
                        ev[e["asset_id"]].append((t, "book", (
                            {float(x["price"]): float(x["size"]) for x in e["bids"]},
                            {float(x["price"]): float(x["size"]) for x in e["asks"]})))
                    elif k == "price_change":
                        for c in e["price_changes"]:
                            ev[c["asset_id"]].append((t, "pc", (c["side"], float(c["price"]), float(c["size"]))))
                    elif k == "last_trade_price" and e.get("transaction_hash") in txs and cut is None:
                        hits.append((e["transaction_hash"], e["asset_id"], t, float(e["price"]), float(e["size"]), e["side"]))
    for v in ev.values():
        v.sort(key=lambda x: x[0])
    return ev, hits


def _hour(args):
    h, txs = args
    ev, hits = _events(h, txs)
    out = []
    by_tok = defaultdict(list)
    for x in hits:
        by_tok[x[1]].append(x)
    for tok, xs in by_tok.items():
        for tx, _, t, px, sz, side in sorted(xs, key=lambda x: x[2]):
            r = Replay(ev[tok])
            b250, a250 = best(*r.at(t - 0.250))
            ok250 = r.ok
            bids, asks = r.at(t - 0.001)
            b1, a1 = best(bids, asks)
            depth_at_px = sum(s for p, s in asks.items() if p <= px + 1e-9)
            bm, am = best(*r.at(t + 10.0))
            out.append({"tx": tx, "asset": tok, "t_match": t, "tape_px": px, "tape_size": sz, "tape_side": side,
                        "ok": ok250 and r.ok, "bb_250": b250, "ba_250": a250, "bb_1": b1, "ba_1": a1,
                        "ask_depth_le_px": depth_at_px,
                        "mid10": None if bm is None or am is None else (bm + am) / 2})
    return out


def main():
    tr = pd.read_pickle(OUT / "leaders_trades.pkl")
    txs = set(tr["transactionHash"])
    hours = sorted(int(p.stem.split("-")[1].split(".")[0]) for p in TAPE.glob("clob_5m-*.tsv.gz"))
    with Pool(3) as pool:
        rows = [r for part in pool.map(_hour, [(h, txs) for h in hours]) for r in part]
    df = pd.DataFrame(rows)
    df.to_pickle(OUT / "leaders_rows.pkl")
    print(len(df), df["ok"].mean())


if __name__ == "__main__":
    main()
