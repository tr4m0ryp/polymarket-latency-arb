"""Download every fill of the most recent resolved instances of a series.

Output per series in data/raw/<slug>/:
  markets.jsonl  one resolved binary market per line
  fills.csv.gz   one fill per line, tagged taker/maker
"""
from __future__ import annotations

import csv
import gzip
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from btclat.api import closed_events, market_trades, parse_market

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
FIELDS = ["condition_id", "wallet", "outcome_index", "side", "size", "price",
          "ts", "tx", "taker", "name", "pseudonym"]


def _ts(iso: str | None) -> int | None:
    if not iso:
        return None
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def _fills(mk: dict) -> list[dict]:
    cid = mk["condition_id"]
    taker = {(t["transactionHash"], t["proxyWallet"], t["asset"], t["side"])
             for t in market_trades(cid, taker_only=True)}
    rows = []
    for t in market_trades(cid, taker_only=False):
        rows.append({
            "condition_id": cid, "wallet": t["proxyWallet"].lower(),
            "outcome_index": t["outcomeIndex"], "side": t["side"],
            "size": t["size"], "price": t["price"], "ts": t["timestamp"],
            "tx": t["transactionHash"],
            "taker": int((t["transactionHash"], t["proxyWallet"], t["asset"], t["side"]) in taker),
            "name": t.get("name") or "", "pseudonym": t.get("pseudonym") or "",
        })
    return rows


def collect(series_id: str, slug: str, n_events: int, workers: int = 6,
            now: int | None = None) -> Path:
    out = RAW / slug
    out.mkdir(parents=True, exist_ok=True)
    markets, seen = [], set()
    for ev in closed_events(series_id, n_events):
        for m in ev.get("markets", []):
            mk = parse_market(m)
            if mk is None or mk["condition_id"] in seen:
                continue
            seen.add(mk["condition_id"])
            mk.update(event_slug=ev.get("slug"), series=slug,
                      start_ts=_ts(mk["window_start"]), end_ts=_ts(mk["window_end"]),
                      created_ts=_ts(mk["created"]))
            if now is None or (mk["end_ts"] or 0) < now:
                markets.append(mk)
    with open(out / "markets.jsonl", "w") as f:
        for mk in markets:
            f.write(json.dumps(mk) + "\n")
    with gzip.open(out / "fills.csv.gz", "wt", newline="") as f, \
            ThreadPoolExecutor(workers) as pool:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for i, rows in enumerate(pool.map(_fills, markets)):
            w.writerows(rows)
            if i % 50 == 0:
                print(f"[{slug}] {i}/{len(markets)} markets", flush=True)
    return out
