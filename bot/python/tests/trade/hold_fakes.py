"""Offline venue, markets and fan-out for the hold and duplicate-send tests. No network."""
from __future__ import annotations

from .fakes import FakeVenue, resp

MKT = {"slug": "btc-updown-5m-1791800100", "up": "UP", "down": "DN", "start": 1791800100}
SERVER_NOW = 1791800150.0


class Markets:
    def current(self, now, margin=20.0):
        return MKT


class Clock:
    def __init__(self):
        self.t, self.slept = 1791800110.0, []

    def now(self):
        return self.t

    def sleep(self, s):
        self.slept.append(s)
        self.t += s


class HoldVenue(FakeVenue):
    """Up is the expensive side, Down the cheap one. The marketable answer depends on the
    order type: FAK matched, FOK killed, GTC delayed then live (partial 2 sh), GTD live."""

    def __init__(self, ask=0.05, fill_all=False, post_fn=None, **kw):
        super().__init__(**kw)
        self.books = {"UP": (0.94, 0.95), "DN": (ask - 0.01, ask)}
        self.fill_all, self.post_fn = fill_all, post_fn
        self.state: dict = {}

    def server_now(self):
        return SERVER_NOW

    def book(self, token):
        self.calls.append(("book", token))
        bb, ba = self.books[token]
        return {"bb": bb, "ba": ba, "resp": resp(path="/book")}

    def post(self, s):
        self.calls.append(("post", s))
        oid = f"0x{s.order_type}{next(self.ids)}"
        if self.post_fn:
            r = self.post_fn(s, oid)
            if r is not None:
                return r
        px = s.price
        if s.post_only:
            self.state[oid] = ("LIVE", 0.0, px)
            return resp(body={"success": True, "orderID": oid, "status": "live"}, ms=56.0)
        if self.fill_all or s.order_type == "FAK":
            return resp(body={"success": True, "orderID": oid, "status": "matched",
                              "makingAmount": f"{s.size * px:.4f}", "takingAmount": f"{s.size:g}"}, ms=270.0)
        if s.order_type == "FOK":
            return resp(code=400, body={"error": "order couldn't be fully filled. FOK orders are fully filled or killed."}, ms=275.0)
        if s.order_type == "GTC":
            self.state[oid] = ("DELAYED", 0.0, px)
            return resp(body={"success": True, "orderID": oid, "status": "delayed"}, ms=60.0)
        self.state[oid] = ("LIVE", 0.0, px)
        return resp(body={"success": True, "orderID": oid, "status": "live"}, ms=58.0)

    def get_order(self, oid):
        self.calls.append(("get_order", oid))
        st, sh, px = self.state.get(oid, ("MATCHED", 5.0, 0.05))
        if st == "DELAYED":                     # the hold ends on the second look: 2 sh matched, rest rests
            n = sum(1 for c in self.calls if c == ("get_order", oid))
            if n >= 2:
                self.state[oid] = ("LIVE", 2.0, px)
                st, sh = "LIVE", 2.0
        return resp(path="/data/order", body={"status": st, "size_matched": str(sh), "price": str(px)})

    def cancel(self, oid):
        r = super().cancel(oid)
        if oid in self.state:
            st, sh, px = self.state[oid]
            self.state[oid] = ("CANCELED", sh, px)
        return r


class FakeFanout:
    """k copies: the first accepted, the rest rejected as duplicates (or, `unsafe`, each its own order)."""

    def __init__(self, unsafe=False):
        self.unsafe, self.posts, self.closed, self.n = unsafe, [], False, 0

    def warm(self):
        return [25.0, 26.0, 27.0]

    def post(self, s, k):
        self.posts.append(k)
        out = []
        for i in range(k):
            self.n += 1
            if i == 0 or self.unsafe:
                out.append(resp(body={"success": True, "orderID": f"0xdup{self.n}", "status": "live"}, ms=55.0 + i))
            else:
                out.append(resp(code=400, body={"error": "order 0xdup is duplicated"}, ms=50.0 + i))
        return out

    def close(self):
        self.closed = True
