"""Free remote probes from inside AWS Tokyo, Dublin and London (Globalping, no account).

Globalping (api.globalping.io, jsDelivr) runs ping/http/mtr from volunteer and cloud-hosted
probes; some are tagged by AWS region. This answers, before renting anything:
  - TCP RTT from each AWS region to the Binance spot and USD-M stream gateways
  - TCP RTT across the AWS backbone (to a regional AWS API endpoint in the other region)
  - HTTPS timings to clob.polymarket.com (Cloudflare POP + origin), TTFB on a fresh connection
Read-only; anonymous quota is a few hundred probe-runs per hour, this uses ~40.

    python3 latency/infra/globalping.py     (writes data/out/infra/globalping.json)"""
from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

API = "https://api.globalping.io/v1/measurements"
OUT = Path(__file__).resolve().parents[2] / "data/out/infra/globalping.json"
REGIONS = {"tokyo": "aws-ap-northeast-1", "dublin": "aws-eu-west-1", "london": "aws-eu-west-2"}
PROBES = 2  # probes per region (only 1-2 exist in eu-west-1/2)

TCP_TARGETS = {
    "binance_spot": ("stream.binance.com", 9443),
    "binance_perp": ("fstream.binance.com", 443),
    "clob_edge": ("clob.polymarket.com", 443),
    "aws_api_tokyo": ("dynamodb.ap-northeast-1.amazonaws.com", 443),
    "aws_api_dublin": ("dynamodb.eu-west-1.amazonaws.com", 443),
    "aws_api_london": ("dynamodb.eu-west-2.amazonaws.com", 443),
}


def _run(body: dict) -> dict:
    r = httpx.post(API, json=body, timeout=30)
    r.raise_for_status()
    mid = r.json()["id"]
    for _ in range(60):
        time.sleep(2)
        m = httpx.get(f"{API}/{mid}", timeout=30).json()
        if m["status"] != "in-progress":
            return m
    return m


def _probe(res: dict) -> dict:
    p = res["probe"]
    return {"city": p["city"], "asn": p["asn"], "tags": [t for t in p.get("tags", []) if t.startswith("aws")]}


def tcp_ping(region: str, host: str, port: int) -> list[dict]:
    m = _run({"type": "ping", "target": host, "limit": PROBES,
              "locations": [{"magic": REGIONS[region]}],
              "measurementOptions": {"packets": 12, "protocol": "TCP", "port": port}})
    out = []
    for r in m.get("results", []):
        s = r["result"].get("stats") or {}
        out.append({**_probe(r), "min": s.get("min"), "avg": s.get("avg"), "max": s.get("max"),
                    "loss": s.get("loss"), "ip": r["result"].get("resolvedAddress")})
    return out


def https_get(region: str, host: str = "clob.polymarket.com", path: str = "/time") -> list[dict]:
    m = _run({"type": "http", "target": host, "limit": PROBES,
              "locations": [{"magic": REGIONS[region]}],
              "measurementOptions": {"protocol": "HTTPS", "request": {"method": "GET", "path": path}}})
    out = []
    for r in m.get("results", []):
        res = r["result"]
        hdr = {k.lower(): v for k, v in (res.get("headers") or {}).items()}
        out.append({**_probe(r), "timings": res.get("timings"), "status": res.get("statusCode"),
                    "cf_pop": str(hdr.get("cf-ray", "-")).split("-")[-1]})
    return out


def main() -> None:
    res: dict = {"when_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()), "tcp": {}, "https": {}}
    for region in REGIONS:
        res["tcp"][region] = {k: tcp_ping(region, h, p) for k, (h, p) in TCP_TARGETS.items()}
        res["https"][region] = https_get(region)
        print(region, json.dumps(res["tcp"][region]["binance_perp"]), json.dumps(res["https"][region]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
