"""Offline stand-ins for the CLOB client, market and sinks. No network anywhere."""
from __future__ import annotations

import itertools
import os
from types import SimpleNamespace

from btclat.trade.venue.http import Resp
from btclat.trade.venue.signer import Signed

KEY = "0x" + "ab" * 32
FUNDER = "0x" + "12" * 20


def resp(code=200, body=None, path="/order", ms=30.0, idle=0.5, hdr=None):
    t0 = 1_000_000_000_000
    return Resp("POST", path, code, body if body is not None else {}, t0, t0 + int(ms * 1e6), "HTTP/2", idle, hdr or {})


class FakeVenue:
    """Records every call. `post_body` / `cancel_ok` / `bb` steer its answers."""

    def __init__(self, bb=0.50, ba=0.52, post=None, cancel_ok=True, geo=None, version=2, balance=50.0):
        self.calls: list = []
        self.bb, self.ba = bb, ba
        self.post_resp = post
        self.cancel_ok = cancel_ok
        self.geo = geo if geo is not None else {"blocked": False, "country": "IE", "region": "D"}
        self.ver, self.bal = version, balance
        self.ids = itertools.count()
        self.closed = False
        self.lookups: list = []

    def ping(self):
        self.calls.append(("ping",))
        return resp(path="/time", ms=25.0)

    def geoblock(self):
        self.calls.append(("geoblock",))
        return self.geo

    def version(self):
        return self.ver

    def connect(self):
        self.calls.append(("connect",))

    def balance(self):
        return {"balance": self.bal, "allowance_ok": True, "code": 200}

    def book(self, token):
        self.calls.append(("book", token))
        return {"bb": self.bb, "ba": self.ba, "resp": resp(path="/book")}

    def sign(self, token, price, size, side="BUY", order_type="FAK", post_only=False, expiration=0):
        self.calls.append(("sign", token, price, size, side, order_type, post_only, expiration))
        return Signed("{}", 1400.0, token, price, size, side, order_type, post_only)

    def post(self, signed):
        self.calls.append(("post", signed))
        if self.post_resp is not None:
            return self.post_resp
        oid = f"0xorder{next(self.ids)}"
        return resp(body={"success": True, "orderID": oid, "status": "live", "makingAmount": "0", "takingAmount": "0"})

    def get_order(self, oid):
        self.calls.append(("get_order", oid))
        return self.lookups.pop(0) if self.lookups else resp(body={"status": "MATCHED", "size_matched": "5", "price": "0.5"})

    def cancel(self, oid):
        self.calls.append(("cancel", oid))
        return resp(body={"canceled": [oid] if self.cancel_ok else [], "not_canceled": {} if self.cancel_ok else {oid: "x"}})

    def cancel_all(self):
        self.calls.append(("cancel_all",))
        return resp(body={"canceled": [], "not_canceled": {}})

    def info(self):
        return {"address": FUNDER}

    def close(self):
        self.closed = True

    def n(self, name):
        return sum(1 for c in self.calls if c[0] == name)


class ListSink:
    def __init__(self):
        self.lines = []

    def write(self, t_ns, raw):
        self.lines.append((t_ns, raw))


class InlineWorker:
    busy = False

    def order(self, fn, done):
        done(fn())
        return True


class Book:
    def __init__(self, bb, ba):
        self.bb, self.ba = bb, ba

    def mid(self):
        return (self.bb + self.ba) / 200


def book(bb=48, ba=50):
    return Book(bb, ba)


def market(start=1000.0, bb=48, ba=50, tick=0.01):
    meta = {"slug": f"btc-updown-5m-{int(start)}", "up": "UP", "down": "DN", "start": start, "end": start + 300,
            "tick": tick}
    return SimpleNamespace(meta=meta, start=start, end=start + 300, book=book(bb, ba))


def write_creds(config, mode=0o600, **kw):
    config.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(config, 0o700)
    d = {"POLY_PRIVATE_KEY": KEY, "POLY_FUNDER": FUNDER, "POLY_SIGNATURE_TYPE": "3", **kw}
    p = config / "polymarket.env"
    p.write_text("".join(f"{k}={v}\n" for k, v in d.items() if v is not None))
    os.chmod(p, mode)
    return p
