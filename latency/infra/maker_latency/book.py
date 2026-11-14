"""When did the venue put our order on (take it off) its book? The CLOB market channel's
`price_change` carries the venue's own timestamp (ms): the first change at our token, price and
side BUY whose size steps by our size after our send is our insert (a decrease: our cancel).

That splits each round trip at the venue's book event (clock offset: the feed lag itself,
recv - venue stamp, is reported so the split can be read against it):
  in   = venue book stamp - t_send   (our client, the network in, Cloudflare, the venue's queue)
  out  = t_ack - venue book stamp    (the venue's response path back to us)"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

WINDOW_NS = 3_000_000_000


def _files(root: Path) -> list[Path]:
    return sorted((root / "raw").glob("*/clob_5m-*.tsv.gz"))


def stamp(root: Path, ops: pd.DataFrame, size: float = 5.0) -> pd.DataFrame:
    """ops + venue book stamp (s), feed receive time (ns) of that change, feed lag (ms)."""
    want: dict[str, list] = {}
    for i, r in ops.iterrows():
        want.setdefault(r["token"], []).append((r["t_send_ns"], i, f"{r['price']:g}", r["what"]))
    lo = min(ops["t_send_ns"]) - WINDOW_NS
    hi = max(ops["t_send_ns"]) + WINDOW_NS
    level: dict[tuple, float] = {}
    hit: dict[int, tuple] = {}
    for p in _files(root):
        with gzip.open(p, "rt") as fh:
            for line in fh:
                t = int(line[:19])
                if t < lo or t > hi or '"price_change"' not in line:
                    continue
                j = json.loads(line[20:])
                for x in (j if isinstance(j, list) else [j]):
                    for c in x.get("price_changes") or []:
                        a = c.get("asset_id")
                        if a not in want or c.get("side") != "BUY":
                            continue
                        key = (a, f"{float(c['price']):g}")
                        new = float(c["size"])
                        d = new - level.get(key, 0.0)
                        level[key] = new
                        for t_send, i, px, what in want[a]:
                            if i in hit or px != key[1] or not 0 <= t - t_send <= WINDOW_NS:
                                continue
                            if abs(d - (size if what == "insert" else -size)) < 1e-6:
                                hit[i] = (float(x["timestamp"]) / 1e3, t)
    out = ops.copy()
    out["t_book"] = [hit.get(i, (np.nan, 0))[0] for i in out.index]
    out["t_recv_ns"] = [hit.get(i, (0, np.nan))[1] for i in out.index]
    out["in_ms"] = (out["t_book"] - out["t_send_ns"] / 1e9) * 1e3
    out["out_ms"] = (out["t_ack_ns"] / 1e9 - out["t_book"]) * 1e3
    out["feed_lag"] = (out["t_recv_ns"] / 1e9 - out["t_book"]) * 1e3
    return out
