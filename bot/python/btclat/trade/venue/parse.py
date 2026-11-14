"""CLOB responses -> flat records. Error kinds follow docs.polymarket.com/resources/error-codes
(messages matched case-insensitively); a BUY's `makingAmount` is pUSD paid and `takingAmount`
shares received (docs: trading/place-orders; whether V2's makingAmount includes the taker fee
is not documented: check the first real fill against GET /data/trades)."""
from __future__ import annotations

ERRORS = (
    ("fak_no_match", "no orders found to match"), ("fok_killed", "fok orders are"),
    ("min_size", "lower than the minimum"), ("min_notional", "marketable buy"),
    ("min_notional", "invalid amount"), ("balance", "not enough balance"),
    ("closed_only", "closed only"), ("banned", "banned"), ("post_only_crosses", "invalid post-only"),
    ("crosses_book", "crosses the book"), ("tick", "tick size"), ("duplicate", "duplicated"),
    ("not_ready", "not yet ready"), ("paused", "trading is currently disabled"),
    ("cancel_only", "cancel-only"), ("post_only_mode", "post-only mode"), ("timeout", "timed out"),
    ("geoblock", "restricted"), ("geoblock", "region"), ("geoblock", "geoblock"),
    ("payload", "invalid order payload"), ("auth", "unauthorized"), ("auth", "invalid api key"))
BY_CODE = {0: "transport", 401: "auth", 403: "forbidden", 425: "engine_restart", 429: "rate_limited"}


def _msg(body) -> str:
    if isinstance(body, dict):
        return str(body.get("errorMsg") or body.get("error") or body.get("message") or "")
    return "" if body is None else str(body)


def classify(code: int, body) -> str | None:
    msg = _msg(body).lower()
    if code == 200 and not msg:
        return None
    for kind, needle in ERRORS:
        if needle in msg:
            return kind
    return BY_CODE.get(code, f"http_{code}" if code != 200 else "error")


def _f(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def order(resp) -> dict:
    """status, order id and the immediate fill of a POST /order response."""
    b = resp.body if isinstance(resp.body, dict) else {}
    kind = classify(resp.code, resp.body)
    ok = resp.code == 200 and bool(b.get("success", b.get("ok", True))) and kind is None
    sh, cost = _f(b.get("takingAmount")), _f(b.get("makingAmount"))
    return {"ok": ok, "status": b.get("status") if ok else "rejected", "order_id": b.get("orderID") or None,
            "fill_sh": sh if ok else 0.0, "fill_cost": cost if ok else 0.0,
            "px": cost / sh if ok and sh > 0 else None, "trade_ids": b.get("tradeIDs") or [],
            "err": None if ok else _msg(resp.body)[:300] or resp.err, "err_kind": None if ok else kind}


def lookup(resp) -> dict:
    """GET /data/order/<id> (follow-up of a `delayed` order): matched size at the order price.

    `found` False: the venue answered 200 without the order (body null / empty). Its read side
    lags the matching engine: in the 2026-10-14 live hour it answered so for 21 of 35 orders
    that certainly existed (lookups 30-190 ms after the ack), and for a matched one. Never
    read a not-found answer as "0 matched"."""
    b = resp.body if isinstance(resp.body, dict) else {}
    sh, px = _f(b.get("size_matched")), _f(b.get("price"))
    return {"status": b.get("status"), "fill_sh": sh, "fill_cost": sh * px, "px": px if sh > 0 else None,
            "found": bool(b.get("status") or b.get("id"))}


def cancelled(resp, oid: str) -> bool:
    b = resp.body if isinstance(resp.body, dict) else {}
    return resp.code == 200 and oid in (b.get("canceled") or [])


GONE = ("can't be found", "cannot be found", "not found", "already canceled", "matched")


def gone(resp, oid: str) -> str | None:
    """The venue's reason when a cancel finds the order no longer on its book ("order can't be
    found - already canceled or matched"): it left the book, maybe by a fill. Else None."""
    b = resp.body if isinstance(resp.body, dict) else {}
    why = (b.get("not_canceled") or {}).get(oid) if resp.code == 200 else None
    return str(why) if why and any(g in str(why).lower() for g in GONE) else None


def best(resp) -> tuple[float, float]:
    """(best bid, best ask) of a GET /book response; nan for an empty side."""
    b = resp.body if isinstance(resp.body, dict) else {}
    bids = [_f(x["price"]) for x in b.get("bids") or [] if _f(x.get("size")) > 0]
    asks = [_f(x["price"]) for x in b.get("asks") or [] if _f(x.get("size")) > 0]
    return (max(bids) if bids else float("nan")), (min(asks) if asks else float("nan"))


def balance(resp) -> dict:
    """pUSD balance ($) and whether any exchange allowance is set (6-decimal base units)."""
    b = resp.body if isinstance(resp.body, dict) else {}
    al = b.get("allowances") or ({"_": b["allowance"]} if "allowance" in b else {})
    return {"balance": _f(b.get("balance")) / 1e6, "allowance_ok": any(_f(v) > 0 for v in al.values()),
            "code": resp.code}
