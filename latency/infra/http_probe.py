"""Warm-connection round trips to the Polymarket CLOB (read-only GETs, nothing is posted).

For HTTP/1.1 keep-alive and HTTP/2 (httpx), one connection each, interleaved: round-trip
time of GET /time (no origin work beyond a clock read) and GET /book (origin reads a book),
plus requests after 10 s and 60 s of idle to see whether the connection stays warm. Records
the Cloudflare POP (cf-ray suffix). Origin share = warm RTT minus the TCP RTT to the edge.

    python3 latency/infra/http_probe.py [n]     (writes data/out/infra/http_probe.json)"""
from __future__ import annotations

import json
import socket
import statistics as st
import sys
import time
from pathlib import Path

import httpx

OUT = Path(__file__).resolve().parents[2] / "data/out/infra/http_probe.json"
HOST = "https://clob.polymarket.com"


def _token() -> str:
    """Up token of the next 5m BTC market (open for the whole probe)."""
    slug = f"btc-updown-5m-{(int(time.time()) // 300 + 1) * 300}"
    m = httpx.get(f"https://gamma-api.polymarket.com/markets?slug={slug}", timeout=10).json()[0]
    return json.loads(m["clobTokenIds"])[0]


def _tcp_rtt(host: str = "clob.polymarket.com", n: int = 10) -> list[float]:
    out = []
    for _ in range(n):
        t = time.perf_counter()
        with socket.create_connection((host, 443), timeout=5):
            out.append((time.perf_counter() - t) * 1e3)
        time.sleep(0.1)
    return out


def _q(xs: list[float]) -> dict:
    xs = sorted(xs)
    return {"n": len(xs), "p10": round(xs[len(xs) // 10], 2), "p50": round(st.median(xs), 2),
            "p90": round(xs[int(len(xs) * 0.9)], 2), "min": round(xs[0], 2)}


def _one(c: httpx.Client, path: str) -> tuple[float, str]:
    t = time.perf_counter()
    r = c.get(HOST + path)
    dt = (time.perf_counter() - t) * 1e3
    r.raise_for_status()
    return dt, r.headers.get("cf-ray", "-").split("-")[-1]


def main(n: int = 60) -> None:
    clients = {"h1": httpx.Client(http2=False, timeout=10), "h2": httpx.Client(http2=True, timeout=10)}
    paths = {"time": "/time", "book": f"/book?token_id={_token()}"}
    res: dict = {"tcp_connect_ms": _q(_tcp_rtt())}
    samples = {f"{c}_{p}": [] for c in clients for p in paths}
    pops = set()
    for name, c in clients.items():  # open and warm each connection
        for _ in range(3):
            _one(c, "/time")
        res[f"{name}_http_version"] = c.get(HOST + "/time").http_version
    for _ in range(n):
        for name, c in clients.items():
            for pk, path in paths.items():
                dt, pop = _one(c, path)
                samples[f"{name}_{pk}"].append(dt)
                pops.add(pop)
                time.sleep(0.1)
    for k, v in samples.items():
        res[k] = _q(v)
    for idle in (10, 60):
        time.sleep(idle)
        res[f"after_idle_{idle}s"] = {name: round(_one(c, "/time")[0], 2) for name, c in clients.items()}
    gaps = {}  # warmth vs request spacing on the HTTP/2 connection
    for gap in (0.05, 0.25, 1.0, 2.0, 5.0, 15.0):
        xs = []
        for _ in range(8):
            time.sleep(gap)
            xs.append(_one(clients["h2"], "/time")[0])
        gaps[str(gap)] = _q(xs)
    res["h2_time_by_gap_s"] = gaps
    res["cloudflare_pops"] = sorted(pops)
    res["note"] = "measured from the Scaleway Paris research host; RTT in ms"
    print(json.dumps(res, indent=1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 60)
