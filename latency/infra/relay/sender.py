"""Tokyo relay: forward each first-arriving Binance perp update to receivers over UDP.

Packet (ascii): kind|id|E_ms|tokyo_recv_ns. Usage: sender.py SECS HOST:PORT [HOST:PORT ...]
"""
from __future__ import annotations

import asyncio
import json
import socket
import sys

import numpy as np

from feed import run


def main(secs: float, targets: list[str]) -> None:
    dst = [(h, int(p)) for h, p in (t.split(":") for t in targets)]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    lag = []

    def on_first(k, now, _i):
        pkt = f"{k[0]}|{k[1]}|{k[2]}|{now}".encode()
        for d in dst:
            sock.sendto(pkt, d)
        lag.append(now / 1e6 - k[2])

    asyncio.run(run(secs, on_first))
    a = np.array(lag)
    print("SENDER " + json.dumps({"n": len(a), "E_to_tokyo_ms": {q: round(float(np.percentile(a, q)), 2)
                                                                for q in (10, 50, 90, 99)}}), flush=True)


if __name__ == "__main__":
    main(float(sys.argv[1]), sys.argv[2:])
