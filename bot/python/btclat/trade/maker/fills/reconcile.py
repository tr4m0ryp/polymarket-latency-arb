"""The run's last word on fills (maker/run.py, live): after the final cancels, one more read of
our trades on the CLOB (GET /data/trades) through Settle.final, and the public Data API's TRADE
rows of our wallet as an independent check (it lags the match by a few blocks)."""
from __future__ import annotations

import asyncio


async def reconcile(st, venue, mgr, wait_s: float) -> dict:
    if mgr.n["inserts"]:
        await asyncio.sleep(wait_s)              # matches racing the last cancels reach the records
    try:
        trs = await asyncio.to_thread(venue.trades, int(st.t0) - 60)
    except Exception:  # logged as read_ok False
        trs = None
    funder = (venue.info() or {}).get("funder")
    try:
        pub = await asyncio.to_thread(public_trades, funder, int(st.t0) - 60) if funder else None
    except Exception:  # public API hiccup: the line says so
        pub = None
    return st.final(trs, pub)


def public_trades(user: str, start: int) -> dict:
    """Data API /activity TRADE rows of our wallet since `start`: count, shares, $."""
    from btclat.api.http import DATA, get
    rows = [r for r in get(DATA, "/activity", {"user": user, "start": start, "limit": 500, "type": "TRADE"}, retries=2)
            if str(r.get("type")).upper() == "TRADE"]
    return {"trades": len(rows), "shares": round(sum(float(r.get("size") or 0) for r in rows), 6),
            "usdc": round(sum(float(r.get("usdcSize") or 0) for r in rows), 6),
            "tx": sorted({r.get("transactionHash") for r in rows if r.get("transactionHash")})}
