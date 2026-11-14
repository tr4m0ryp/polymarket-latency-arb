"""Europe receiver: the same Binance updates via the Tokyo relay (UDP) and direct (websocket).

Compares both paths per update id on one clock (clock-free), plus E-to-arrival on synced clocks.
Usage: receiver.py SECS PORT
"""
from __future__ import annotations

import asyncio
import json
import sys
import time

import numpy as np

from feed import run


class Relay(asyncio.DatagramProtocol):
    def __init__(self, got: dict):
        self.got = got

    def datagram_received(self, data, addr):
        now = time.time_ns()
        kind, i, e, tok = data.decode().split("|")
        self.got.setdefault((kind, int(i)), now)
        self.got[("E", kind, int(i))] = (int(e), int(tok))


def _q(a) -> dict:
    a = np.asarray(a, float)
    return {"n": int(a.size), **{f"p{q}": round(float(np.percentile(a, q)), 2) for q in (10, 50, 90, 99)}} if a.size else {"n": 0}


async def go(secs: float, port: int) -> dict:
    relay, direct = {}, {}
    t0 = time.time_ns() + 10 * 10**9  # skip connection warm-up
    loop = asyncio.get_running_loop()
    tr, _ = await loop.create_datagram_endpoint(lambda: Relay(relay), local_addr=("0.0.0.0", port))
    await run(secs, lambda k, now, _i: direct.setdefault((k[0], k[1]), (now, k[2])))
    await asyncio.sleep(1.0)
    tr.close()
    out = {}
    for kind in ("B", "T"):
        keys = [k for k in direct if k[0] == kind and k in relay and direct[k][0] > t0]
        diff = [(relay[k] - direct[k][0]) / 1e6 for k in keys]
        e_dir = [direct[k][0] / 1e6 - direct[k][1] for k in keys]
        e_rel = [relay[k] / 1e6 - direct[k][1] for k in keys]
        best = [min(relay[k], direct[k][0]) / 1e6 - direct[k][1] for k in keys]
        out[kind] = {"matched": len(keys), "relay_minus_direct_ms": _q(diff),
                     "relay_first_share": round(float(np.mean(np.array(diff) < 0)), 3) if diff else None,
                     "E_to_direct_ms": _q(e_dir), "E_to_relay_ms": _q(e_rel), "E_to_best_ms": _q(best)}
    return out


if __name__ == "__main__":
    print("RELAY " + json.dumps(asyncio.run(go(float(sys.argv[1]), int(sys.argv[2])))), flush=True)
