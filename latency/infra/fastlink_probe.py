"""Globalping ping/mtr probes for the Tokyo-Europe fast-link search (reports/fast-link.md).

Free, anonymous (200 probe-runs per hour). Each call appends one JSON line to
data/out/infra/fastlink/globalping_{ping,mtr}.jsonl.

    python3 latency/infra/fastlink_probe.py ping '{"target":"185.209.84.131","locs":[{"magic":"aws-ap-northeast-1"}],"limit":3,"proto":"ICMP"}'
    python3 latency/infra/fastlink_probe.py mtr  '{"target":"dynamodb.eu-west-2.amazonaws.com","locs":[{"city":"Khabarovsk","asn":210756}]}'
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

API = "https://api.globalping.io/v1/measurements"
OUT = Path(__file__).resolve().parents[2] / "data/out/infra/fastlink"


def _wait(mid: str) -> dict:
    for _ in range(90):
        time.sleep(2)
        m = httpx.get(f"{API}/{mid}", timeout=30).json()
        if m["status"] != "in-progress":
            return m
    return m


def _submit(kind: str, a: dict) -> dict:
    opts: dict = {"packets": a.get("packets", 4 if kind == "ping" else 3)}
    if a.get("proto", "TCP") == "TCP":
        opts.update(protocol="TCP", port=a.get("port", 443))
    body = {"type": kind, "target": a["target"], "limit": a.get("limit", 1 if kind == "mtr" else 50),
            "locations": a["locs"], "measurementOptions": opts}
    r = httpx.post(API, json=body, timeout=30)
    r.raise_for_status()
    return _wait(r.json()["id"])


def ping(a: dict) -> None:
    m = _submit("ping", a)
    rows = []
    for x in m["results"]:
        p, s = x["probe"], x["result"].get("stats") or {}
        rows.append(dict(city=p["city"], asn=p["asn"], net=p["network"], min=s.get("min"),
                         avg=s.get("avg"), loss=s.get("loss"), ip=x["result"].get("resolvedAddress")))
    rec = dict(when=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), id=m["id"], target=a["target"],
               locs=a["locs"], proto=a.get("proto", "TCP"), rows=rows, tag=a.get("tag", ""))
    with open(OUT / "globalping_ping.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")
    for r in sorted((r for r in rows if r["min"] is not None), key=lambda r: r["min"]):
        print(f"{r['min']:7.1f} {r['avg']:7.1f} AS{r['asn']} {r['net'][:28]} {r['city']}")


def mtr(a: dict) -> None:
    m = _submit("mtr", a)
    with open(OUT / "globalping_mtr.jsonl", "a") as f:
        f.write(json.dumps(dict(when=time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), m=m)) + "\n")
    for x in m["results"]:
        print(x["probe"]["city"], x["probe"]["network"])
        for h in x["result"]["hops"]:
            t = [t["rtt"] for t in h.get("timings", []) if t.get("rtt")]
            print(f"  {h.get('resolvedHostname') or ''} {h.get('resolvedAddress')} {min(t) if t else '*'}")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    {"ping": ping, "mtr": mtr}[sys.argv[1]](json.loads(sys.argv[2]))
