"""Which Binance feed arrives first? Several public streams side by side, same host, same clock.

Opens one websocket per variant for `secs` seconds and stamps every message on arrival.
Trades are matched by trade id across connections carrying the same stream, so the
per-connection delay versus the first arrival is clock-free; E - T (push minus match time)
is the venue's own publish delay. Variants: spot raw vs combined vs a second raw connection
vs data-stream.binance.vision; USD-M /public @trade vs /market @aggTrade vs fstream-mm.
recv - E is the one-way Binance push -> our socket, valid only on a host with a synced clock
(chrony on the AWS Time Sync source), not on the research host.

    python3 latency/infra/binance_probe.py [secs]   (writes data/out/infra/binance_probe.json)"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import websockets

OUT = Path(__file__).resolve().parents[2] / "data/out/infra/binance_probe.json"
S, F = "wss://stream.binance.com:9443", "wss://fstream.binance.com"
VARIANTS = {  # name -> (group, url); a group shares trade ids
    **{f"spot_raw_{c}": ("spot", f"{S}/ws/btcusdt@trade") for c in "abcd"},
    "spot_combined": ("spot", f"{S}/stream?streams=btcusdt@trade/btcusdt@bookTicker"),
    "spot_vision": ("spot", "wss://data-stream.binance.vision/ws/btcusdt@trade"),
    **{f"perp_public_{c}": ("perp", f"{F}/public/ws/btcusdt@trade") for c in "abcd"},
    "perp_mm": ("perp_mm", "wss://fstream-mm.binance.com/ws/btcusdt@trade"),  # 403 when not whitelisted
    "perp_aggtrade": ("perp_agg", f"{F}/market/ws/btcusdt@aggTrade"),
    "perp_bookticker": ("perp_bt", f"{F}/public/ws/btcusdt@bookTicker"),
}


async def _read(name: str, url: str, until: float, rows: list, status: dict) -> None:
    try:
        async with websockets.connect(url, max_queue=None, compression=None, open_timeout=10) as ws:
            status[name] = "ok " + str(ws.remote_address[0])
            while time.time() < until:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=max(0.1, until - time.time()))
                except asyncio.TimeoutError:
                    break
                t = time.time_ns()
                d = json.loads(msg)
                d = d.get("data", d)
                if d.get("e") in ("trade", "aggTrade", "bookTicker"):
                    tid = d.get("t") if d["e"] == "trade" else d.get("l") if d["e"] == "aggTrade" else d.get("u")
                    rows.append((name, d["e"], tid, d.get("E"), d.get("T"), t, len(msg)))
    except Exception as e:  # endpoint refused or dropped: record and move on
        status[name] = repr(e)[:160]


def _q(x) -> dict:
    x = np.asarray(x, float)
    if not len(x):
        return {}
    return {"n": int(len(x)), **{f"p{p}": round(float(np.percentile(x, p)), 2) for p in (10, 50, 90, 99)}}


def main(secs: float = 120) -> None:
    rows: list = []
    status: dict = {}
    until = time.time() + secs

    async def go():
        await asyncio.gather(*[_read(n, u, until, rows, status) for n, (_, u) in VARIANTS.items()])
    asyncio.run(go())
    res: dict = {"secs": secs, "status": status, "publish_E_minus_T_ms": {}, "lag_vs_first_ms": {},
                 "recv_minus_E_ms_needs_synced_clock": {},
                 "msg_bytes_p50": {}, "first_share": {}}
    by = defaultdict(list)
    for r in rows:
        by[r[0]].append(r)
    for n, rs in by.items():
        et = [r[3] - r[4] for r in rs if r[3] is not None and r[4] is not None]
        res["publish_E_minus_T_ms"][n] = _q(et)
        res["recv_minus_E_ms_needs_synced_clock"][n] = _q([r[5] / 1e6 - r[3] for r in rs if r[3] is not None])
        res["msg_bytes_p50"][n] = int(np.median([r[6] for r in rs]))
    for grp in ("spot", "perp"):
        names = [n for n, (g, _) in VARIANTS.items() if g == grp and n in by]
        arr = defaultdict(dict)  # trade id -> name -> receipt ns
        for n in names:
            for r in by[n]:
                arr[r[2]].setdefault(n, r[5])
        full = [v for v in arr.values() if len(v) == len(names)]
        for n in names:
            res["lag_vs_first_ms"][n] = _q([(v[n] - min(v.values())) / 1e6 for v in full])
            res["first_share"][n] = round(float(np.mean([v[n] == min(v.values()) for v in full])), 3) if full else None
    pa = {r[2]: r[5] for r in by.get("perp_public_a", [])}
    agg = [(r[5] - pa[r[2]]) / 1e6 for r in by.get("perp_aggtrade", []) if r[2] in pa]
    res["aggtrade_last_id_lag_vs_raw_trade_ms"] = _q(agg)
    res["note"] = "Scaleway Paris host; lags are relative between connections, clock-free"
    print(json.dumps(res, indent=1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 120)
