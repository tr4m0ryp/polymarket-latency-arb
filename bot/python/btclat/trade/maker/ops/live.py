"""Real order operations for the order manager: sign + hedged POST /order, hedged DELETE
/order, GET /data/order lookups. Each runs on a pool thread; its result is handed back to the
event loop (`post` = loop.call_soon_threadsafe), so the manager's state has one owner.

- insert: post-only GTD BUY (asserted on the signed order), first accepted copy wins. No copy
  accepted and none with a definite answer (all lost in transport, flagged duplicate or 5xx)
  -> `unknown`: the order may exist, so the manager stops (cancel-all) instead of guessing.
- cancel: confirmed when the first copy lists the order id under `canceled`; `gone` when no
  copy did and one says the order can't be found (already canceled or matched: it left the
  book, maybe filled; the manager frees the slot and fills/settle.py finds out).
- lookup: one at a time on the client's own session (size_matched = fills so far); a 200
  without the order (the read side lags) is `unknown`, never "0 matched".
- trades: GET /data/trades of our wallet since a time (fills/settle.py), on the lookup thread.
Times: `t_venue` = midpoint of send and first ack, our estimate of when the venue acted.
`insert_op` / `cancel_op` are shared with the sender process (maker/send/)."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from ...venue import parse
from .hedge import LATE, copies, when_all


def _mid_s(r) -> float:
    return (r.t_send_ns + r.t_ack_ns) / 2e9


def insert_op(venue, hedge, o) -> tuple[dict, list]:
    """Sign the quote (asserted post-only GTD BUY as quoted), hedged POST: (result, copies)."""
    s = venue.sign(o.token, o.price, o.size, "BUY", o.otype, True, expiration=o.expiration)
    if not (s.post_only and s.side == "BUY" and s.order_type == o.otype and s.price == o.price
            and s.size == o.size and s.token == o.token):
        raise AssertionError(f"signed order differs from the quote: {s.order_type} {s.price} {s.size} {s.side}")
    r, futs = hedge.send("POST", "/order", venue.post_headers(s), s.body, lambda x: parse.order(x)["ok"])
    p = parse.order(r)
    definite = [x for x in (f.result() for f in futs if f.done())
                if 0 < x.code < 500 and parse.classify(x.code, x.body) not in LATE]
    unknown = not p["ok"] and not definite        # no copy says what became of the order
    return ({**p, "unknown": unknown, "sign_us": round(s.sign_us, 1), "code": r.code, "ms": round(r.ms, 3),
             "t_send_ns": r.t_send_ns, "t_ack_ns": r.t_ack_ns, "t_venue": _mid_s(r), "k": hedge.k}, futs)


def cancel_op(venue, hedge, o) -> tuple[dict, list]:
    """Hedged DELETE: confirmed by the first copy listing the order as canceled, else `gone`."""
    body, headers = venue.cancel_req(o.oid)
    r, futs = hedge.send("DELETE", "/order", headers, body, lambda x: parse.cancelled(x, o.oid))
    ok = parse.cancelled(r, o.oid)
    gone = None if ok else next((g for g in (parse.gone(f.result(), o.oid) for f in futs if f.done()) if g), None)
    b = r.body if isinstance(r.body, dict) else {}
    return ({"confirmed": ok, "gone": gone, "code": r.code, "ms": round(r.ms, 3), "t_send_ns": r.t_send_ns,
             "t_ack_ns": r.t_ack_ns, "t_venue": _mid_s(r), "k": hedge.k, "not_canceled": b.get("not_canceled"),
             "err": r.err}, futs)


class LiveOps:
    settles_late = True       # a live order's fills are known only after it leaves the book
    def __init__(self, venue, hedge, post, note=None, workers: int = 6):
        self.venue, self.hedge = venue, hedge
        self.post = post
        self.note = note or (lambda kind, **kw: None)
        self.pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="maker-op")
        self.lk = ThreadPoolExecutor(max_workers=1, thread_name_prefix="maker-lookup")

    def server_now(self) -> float:
        return self.venue.server_now()

    def _go(self, pool, fn, o, cb) -> None:
        def job():
            try:
                res = fn(o)
            except Exception as e:  # a failed op is a result the manager acts on, not a dead thread
                res = {"ok": False, "confirmed": False, "unknown": True, "exc": repr(e)[:300]}
            self._post(cb, res)
        try:
            pool.submit(job)
        except RuntimeError:     # pool closed at shutdown: the session's cancel-all covers it
            pass

    def _post(self, fn, *a) -> None:
        try:
            self.post(fn, *a)
        except RuntimeError:     # loop already closed at shutdown: the session's cancel-all covers it
            pass

    def insert(self, o, cb) -> None:
        self._go(self.pool, self._insert, o, cb)

    def cancel(self, o, cb) -> None:
        self._go(self.pool, self._cancel, o, cb)

    def lookup(self, o, cb) -> None:
        self._go(self.lk, self._lookup, o, cb)

    def _copies(self, o, what: str, futs) -> None:
        when_all(futs, lambda rs: self.note("copies", what=what, cid=o.cid, oid=o.oid, copies=copies(rs)))

    def _insert(self, o) -> dict:
        res, futs = insert_op(self.venue, self.hedge, o)
        self._copies(o, "insert", futs)
        return res

    def _cancel(self, o) -> dict:
        res, futs = cancel_op(self.venue, self.hedge, o)
        self._copies(o, "cancel", futs)
        return res

    def _lookup(self, o) -> dict:
        r = self.venue.get_order(o.oid)
        q = parse.lookup(r)
        return {**q, "unknown": r.code != 200 or not q["found"], "code": r.code, "ms": round(r.ms, 3),
                "t_ack": r.t_ack_ns / 1e9, "t_ack_ns": r.t_ack_ns}

    def trades(self, after: int, cb) -> None:
        """Our wallet's trades since `after` (unix s) -> cb(list of trade objects, or None on error)."""
        def job():
            try:
                return self.venue.trades(after)
            except Exception:  # a failed poll is retried by the next one
                return None
        try:
            self.lk.submit(lambda: self._post(cb, job()))
        except RuntimeError:
            pass

    def balance(self) -> dict:
        return self.venue.balance()

    def keep_warm(self) -> list[float]:
        return self.hedge.warm()

    def close(self) -> None:
        self.pool.shutdown(wait=True)
        self.lk.shutdown(wait=True)
        self.hedge.close()
