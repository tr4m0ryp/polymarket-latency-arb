"""Polymarket 5m CLOB market channel -> best ask per token (kind 1 = Up ask, 3 = Down ask).

key2 = the market's start (unix s), px = best ask in USD; token ids come from events-pm.jsonl."""
from __future__ import annotations

import json


def _tokens(st: dict) -> dict:
    if "tok" not in st:
        st["tok"] = {}
        f = st["run"] / "events-pm.jsonl"
        for ln in f.read_text().splitlines() if f.exists() else ():
            e = json.loads(ln)
            if e.get("kind") == "market":
                st["tok"][e["up"]] = (1, e["start"])
                st["tok"][e["down"]] = (3, e["start"])
    return st["tok"]


def pm(m, out: list, st: dict) -> None:
    tok = _tokens(st)
    for x in m if isinstance(m, list) else [m]:
        if not isinstance(x, dict):
            continue
        if x.get("event_type") == "book" and x.get("asset_id") in tok and x.get("asks"):
            k, s = tok[x["asset_id"]]
            out.append((k, -1, s, min(float(a["price"]) for a in x["asks"]), _ts(x), -1))
        for c in x.get("price_changes") or ([x] if x.get("event_type") == "best_bid_ask" else []):
            if c.get("asset_id") in tok and c.get("best_ask"):
                k, s = tok[c["asset_id"]]
                out.append((k, -1, s, float(c["best_ask"]), _ts(x), -1))


def _ts(x: dict) -> int:
    t = x.get("timestamp")
    return int(t) * 1000 if t else -1
