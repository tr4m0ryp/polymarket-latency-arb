"""LiveClob wiring over an in-process HTTP mock (httpx.MockTransport): paths, auth headers,
exact signed body, cancel body, balance parsing, L2 derivation, transport errors. No network."""
import json

import httpx

from btclat.trade.gate.creds import Creds
from btclat.trade.venue import parse
from btclat.trade.venue.client import LiveClob
from btclat.trade.venue.http import Http
from btclat.trade.venue.signer import Signed

from .fakes import FUNDER, KEY


class StubSigner:
    address = FUNDER
    backend = "stub"

    def order(self, token, price, size, side, order_type, post_only, owner, expiration=0):
        body = json.dumps({"order": {"tokenId": token, "side": side}, "owner": owner, "orderType": order_type,
                           "postOnly": post_only}, separators=(",", ":"))
        return Signed(body, 10.0, token, price, size, side, order_type, post_only)

    def l1_headers(self, ts, nonce=0):
        return {"POLY_ADDRESS": FUNDER, "POLY_SIGNATURE": "l1", "POLY_TIMESTAMP": str(ts), "POLY_NONCE": "0"}

    def l2_headers(self, api, method, path, body, ts):
        return {"POLY_API_KEY": api["key"], "POLY_SIGNATURE": f"{method} {path} {body}", "POLY_TIMESTAMP": str(ts)}


def client(handler, l2=False):
    seen = []

    def h(req: httpx.Request):
        seen.append(req)
        return handler(req)
    http = Http()
    http.c = httpx.Client(transport=httpx.MockTransport(h))
    c = Creds(KEY, FUNDER, 3, *(("k", "s", "p") if l2 else (None, None, None)))
    return LiveClob(c, http=http, signer=StubSigner()), seen


def test_connect_derives_l2_and_posts_signed_body():
    def handler(req):
        p = req.url.path
        if p == "/time":
            return httpx.Response(200, json=1791800000)
        if p == "/auth/derive-api-key":
            return httpx.Response(200, json={"apiKey": "AK", "secret": "S", "passphrase": "P"})
        if p == "/order" and req.method == "POST":
            return httpx.Response(200, json={"success": True, "orderID": "0xo", "status": "matched",
                                             "makingAmount": "2.5", "takingAmount": "5"})
        if p == "/order" and req.method == "DELETE":
            return httpx.Response(200, json={"canceled": ["0xo"], "not_canceled": {}})
        if p == "/balance-allowance":
            return httpx.Response(200, json={"balance": "41500000", "allowances": {"0xE111": "1"}})
        return httpx.Response(404, json={"error": "nope"})
    v, seen = client(handler)
    v.connect()
    assert v.derived and v.api["key"] == "AK" and seen[1].headers["POLY_SIGNATURE"] == "l1"
    s = v.sign("TOK", 0.5, 5.0, "BUY", "FAK")
    r = v.post(s)
    req = seen[-1]
    assert req.content.decode() == s.body and req.headers["POLY_SIGNATURE"] == f"POST /order {s.body}"
    assert req.headers["content-type"] == "application/json" and json.loads(s.body)["owner"] == "AK"
    o = parse.order(r)
    assert o["ok"] and o["fill_sh"] == 5 and o["px"] == 0.5 and r.t_ack_ns >= r.t_send_ns
    c = v.cancel("0xo")
    assert json.loads(seen[-1].content) == {"orderID": "0xo"} and parse.cancelled(c, "0xo")
    b = v.balance()
    assert b == {"balance": 41.5, "allowance_ok": True, "code": 200}
    assert seen[-1].url.params["signature_type"] == "3" and seen[-1].url.params["asset_type"] == "COLLATERAL"


def test_errors_are_results_not_exceptions():
    def handler(req):
        raise httpx.ConnectError("down")
    v, _ = client(handler, l2=True)
    r = v.post(v.sign("TOK", 0.5, 5.0))
    assert r.code == 0 and "ConnectError" in r.err and parse.order(r)["err_kind"] == "transport"


def test_classify_documented_errors():
    cases = {"order 0x1 is invalid. Size (4) lower than the minimum: 5": "min_size",
             "not enough balance / allowance": "balance",
             "invalid post-only order: order crosses book": "post_only_crosses",
             "order couldn't be fully filled. FOK orders are fully filled or killed.": "fok_killed",
             "'0xab' address in closed only mode": "closed_only",
             "Trading is currently cancel-only. New orders are not accepted, but cancels are allowed.": "cancel_only"}
    for msg, kind in cases.items():
        assert parse.classify(400, {"error": msg}) == kind, msg
    assert parse.classify(429, "Too Many Requests") == "rate_limited"
    assert parse.classify(425, "") == "engine_restart"
    assert parse.classify(200, {"success": True}) is None


def test_trades_signed_on_bare_path_paginated_and_errors_raise():
    import pytest
    pages = {"MA==": {"data": [{"id": "t1"}], "next_cursor": "Mg=="}, "Mg==": {"data": [{"id": "t2"}], "next_cursor": "LTE="}}

    def handler(req):
        if req.url.path == "/data/trades":
            return httpx.Response(200, json=pages[req.url.params["next_cursor"]])
        return httpx.Response(404, json={"error": "nope"})
    v, seen = client(handler, l2=True)
    assert [t["id"] for t in v.trades(1791986000)] == ["t1", "t2"]
    assert all(r.headers["POLY_SIGNATURE"] == "GET /data/trades None" for r in seen)    # path without query
    assert seen[0].url.params["after"] == "1791986000" and "maker_address" not in seen[0].url.params
    v2, _ = client(lambda req: httpx.Response(401, json={"error": "Unauthorized"}), l2=True)
    with pytest.raises(RuntimeError):
        v2.trades(0)
