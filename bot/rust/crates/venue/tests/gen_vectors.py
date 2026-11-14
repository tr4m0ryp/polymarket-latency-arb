"""Signing vectors for btl_venue, produced by the official py-clob-client-v2 on fixed inputs.

    python3 rust/crates/venue/tests/gen_vectors.py

Writes tests/fixtures/sign_vectors.json (orders, L1 and L2 headers) and
tests/fixtures/amount_vectors.json (get_order_amounts on a price x size grid, tick 0.01).
Salt and order timestamp are pinned by monkeypatching the builder; the key is a throwaway
test key (never funded)."""
from __future__ import annotations

import json
from pathlib import Path

import py_clob_client_v2.order_builder.builder as B
from py_clob_client_v2.clob_types import ApiCreds, CreateOrderOptions, OrderArgsV2, RequestArgs
from py_clob_client_v2.headers.headers import create_level_1_headers, create_level_2_headers
from py_clob_client_v2.order_utils.model.order_data_v2 import order_to_json_v2
from py_clob_client_v2.signer import Signer

OUT = Path(__file__).resolve().parent / "fixtures"
KEY = "0x4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f362318"
FUNDER = "0x6E0C80c90ea6C15917308F820Eac91Ce2724B5b5"
FUNDER_LC = "0x8ba1f109551bd432803012645ac136ddd64dba72"
TOKEN = "71321045679252212594626385532706912750332728571942532289631379312455583992563"
OWNER = "b6a1c7e2-3f4d-4a5b-9c8d-0e1f2a3b4c5d"
API = {"key": OWNER, "secret": "c2VjcmV0LXRlc3Qta2V5LWJ0bC12ZW51ZS0xMjM0NTY3OA==", "passphrase": "pass-phrase-test"}


class _Clock:
    """Stands in for the `time` module inside builder.py: a pinned time_ns."""
    ms = 0

    def time_ns(self):
        return self.ms * 1_000_000


class _Builder(B.ExchangeOrderBuilderV2):
    salt = "0"

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.generate_salt = lambda: _Builder.salt


B.time = _Clock()
B.ExchangeOrderBuilderV2 = _Builder


def order_vec(sig_type, funder, price, size, side, order_type, post_only, expiration, salt, ts_ms, token=TOKEN):
    _Builder.salt, B.time.ms = str(salt), ts_ms
    signer = Signer(KEY, 137)
    ob = B.OrderBuilder(signer, signature_type=sig_type, funder=funder)
    o = ob.build_order(OrderArgsV2(token_id=token, price=price, size=size, side=side, expiration=expiration),
                       CreateOrderOptions(tick_size="0.01", neg_risk=False), version=2)
    body = json.dumps(order_to_json_v2(o, OWNER, order_type, post_only, False), separators=(",", ":"),
                      ensure_ascii=False)
    return {"sig_type": sig_type, "funder": funder, "token_id": token, "price": price, "size": size,
            "side": side, "order_type": order_type, "post_only": post_only, "expiration": expiration,
            "owner": OWNER, "salt": salt, "timestamp_ms": ts_ms, "maker_amount": int(o.makerAmount),
            "taker_amount": int(o.takerAmount), "body": body}


def orders():
    out, n = [], 0
    cases = [(0.57, 5.0, "BUY", "FAK", False, 0), (0.43, 5.5, "SELL", "FAK", False, 0),
             (0.01, 21.0, "BUY", "FOK", False, 0), (0.99, 30.0, "SELL", "FOK", False, 0),
             (0.5, 60.0, "BUY", "GTC", True, 0), (0.07, 60.0, "SELL", "GTC", False, 0),
             (0.33, 12.345, "BUY", "GTD", False, 1760000000), (0.125, 7.77, "SELL", "GTD", True, 1760003600)]
    for st in (0, 1, 2, 3):
        for price, size, side, ot, po, exp in cases:
            n += 1
            salt = 1_000_003 * n + 977 * st
            ts = 1_760_000_000_000 + 1_234 * n
            out.append(order_vec(st, FUNDER, price, size, side, ot, po, exp, salt, ts))
    # lowercase funder (taken verbatim into the body), a short token id, salt near its max
    out.append(order_vec(1, FUNDER_LC, 0.62, 21.0, "BUY", "FAK", False, 0, 1_234_567_890_123, 1_760_000_123_456))
    out.append(order_vec(3, FUNDER_LC, 0.38, 5.0, "SELL", "FAK", False, 0, 42, 1_760_000_999_999))
    out.append(order_vec(0, FUNDER, 0.25, 10.0, "BUY", "GTC", False, 0, 7, 1_760_000_000_001, token="12345"))
    return out


def l1():
    s = Signer(KEY, 137)
    return [{"ts": ts, "nonce": nonce, "headers": create_level_1_headers(s, nonce=nonce, timestamp=ts)}
            for ts, nonce in ((1760000000, 0), (1760012345, 0), (1760099999, 7))]


def l2(order_body):
    s = Signer(KEY, 137)
    creds = ApiCreds(API["key"], API["secret"], API["passphrase"])
    out = []
    for method, path, body, ts in (("GET", "/balance-allowance", None, 1760000000),
                                   ("GET", "/data/trades", None, 1760000001),
                                   ("GET", "/data/order/0xabc123", None, 1760000002),
                                   ("DELETE", "/cancel-all", None, 1760000003),
                                   ("DELETE", "/order", '{"orderID":"0xdeadbeef"}', 1760000004),
                                   ("POST", "/order", order_body, 1760000005)):
        ra = RequestArgs(method=method, request_path=path, body=None, serialized_body=body)
        out.append({"method": method, "path": path, "body": body, "ts": ts,
                    "headers": create_level_2_headers(s, creds, ra, timestamp=ts)})
    return out


SIZES = [5, 5.5, 21, 30, 60, 0.01, 0.1, 1, 1.5, 2.37, 3.333, 7.77, 10, 12.345, 15.5, 19.99, 25, 33.33,
         45.67, 50, 75.25, 99.99, 100, 123.45, 250, 500.5, 1000, 4999.99]


def amounts():
    ob = B.OrderBuilder(Signer(KEY, 137))
    rc = B.ROUNDING_CONFIG["0.01"]
    rows = []
    grid = [(i / 100, s) for i in range(1, 100) for s in SIZES]
    grid += [(k / 1000, s) for k in range(10, 991) for s in (5, 5.5, 21, 30, 60)]
    for price, size in grid:
        for side in ("BUY", "SELL"):
            _, mk, tk = ob.get_order_amounts(side, float(size), price, rc)
            rows.append([price, float(size), side, mk, tk])
    return rows


def main():
    od = orders()
    vec = {"key": KEY, "address": Signer(KEY, 137).address(), "funder": FUNDER, "api": API,
           "orders": od, "l1": l1(), "l2": l2(od[0]["body"])}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sign_vectors.json").write_text(json.dumps(vec, indent=1) + "\n")
    (OUT / "amount_vectors.json").write_text(json.dumps(amounts(), separators=(",", ":")) + "\n")
    print(f"{len(od)} orders, {len(vec['l1'])} l1, {len(vec['l2'])} l2 -> {OUT}")


if __name__ == "__main__":
    main()
