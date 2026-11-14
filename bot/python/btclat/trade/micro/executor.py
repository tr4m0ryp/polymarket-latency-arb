"""Live leg of micro mode: one real taker order per signal, exactly 5 shares, FAK, limit =
the arm's limit (seen ask + 2 c), on the side the arm chose; every cap in risk/ checked first.

Per signal one JSON line (`orders` stream, written once the live result, its 10 s mark and
the paper prediction are all in): receipt time of the trigger event and its venue / Binance
stamp, decision, sign, send and ack times (ns), venue status, fill size and price, fee
(0.07 p (1 - p) per share at our 0% tier), the book on our feed at ack + 10 s, and the paper
engine's predicted fill and 10 s markout for the same signal. Skipped signals are logged
with the cap that stopped them."""
from __future__ import annotations

import heapq
import itertools
import json
import time

from ..risk.book import Intent
from ..risk.limits import VENUE_MIN_SHARES, fee
from ..venue import parse

FATAL = ("geoblock", "closed_only", "banned", "auth", "forbidden")
PAPER_KEYS = ("fill_sh", "px", "cost", "fee", "mk3", "mk10", "gap", "levels", "seen_depth", "tm")


def make_send(venue, sleep=time.sleep):
    """The worker-thread half: sign, POST, parse; a `delayed` order is looked up until final."""
    def send(it: Intent) -> dict:
        s = venue.sign(it.token, it.price, it.size, "BUY", "FAK")
        r = venue.post(s)
        o = parse.order(r)
        out = dict(o, sign_us=s.sign_us, t_send_ns=r.t_send_ns, t_ack_ns=r.t_ack_ns, post=r.brief(), px_src="post")
        if o["ok"] and o["status"] == "delayed" and o["order_id"]:
            for _ in range(5):
                sleep(0.2)
                q = parse.lookup(venue.get_order(o["order_id"]))
                out.update(q, px_src="order_lookup")
                if q["status"] and q["status"].lower() not in ("delayed", "live"):
                    break
        return out
    return send


def cpd(sh, cost, fee_, mid) -> float | None:
    """10 s markout in c per $ spent."""
    if not sh or not cost or mid is None or mid != mid:
        return None
    return 100 * (sh * mid - cost - fee_) / cost


class LiveExec:
    def __init__(self, risk, worker, send, sink, now, post=None, note=None, size: float = VENUE_MIN_SHARES):
        self.risk, self.worker, self.send, self.sink, self.now = risk, worker, send, sink, now
        self.post = post or (lambda fn, *a: fn(*a))          # worker thread -> event loop
        self.note = note or (lambda kind, **kw: None)
        self.size = size
        self.pending: dict[str, dict] = {}
        self.paper: dict[str, dict] = {}
        self.jobs: list = []
        self.seq = itertools.count()
        self.stop_reason: str | None = None
        self.n = {"signals": 0, "sent": 0, "filled": 0, "skipped": 0, "written": 0}

    def on_signal(self, o: dict, m, src: str, t_venue: float, lat_us: float) -> None:
        t_dec = self.now()
        up = o["side"] > 0
        it = Intent(o["arm"], m.meta["slug"], m.meta["up"] if up else m.meta["down"], up,
                    round(min(o["limit"], 0.99), 2), self.size, m.end)
        rec = {"sig": o["sig"], "arm": o["arm"], "slug": it.slug, "side": o["side"], "token": it.token,
               "up": up, "t_signal": o["t"], "src": src, "t_event_venue": t_venue, "t_decision": t_dec,
               "lat_us": lat_us, "seen": o["seen"], "limit": it.price, "size": it.size, "value": o["value"],
               "edge": o["edge"], "start": m.start, "end": m.end, "bb0": m.book.bb, "ba0": m.book.ba}
        self.n["signals"] += 1
        reason = "tick" if abs(float(m.meta.get("tick", 0.01)) - 0.01) > 1e-9 else None
        reason = reason or (self.stop_reason and "stopped") or self.risk.check(it, t_dec)
        if reason is None and self.worker.busy:
            reason = "busy"
        self.pending[o["sig"]] = rec
        if reason is not None:
            rec.update(decision=f"skip:{reason}", live_done=True)
            self.n["skipped"] += 1
            self._maybe_final(o["sig"])
            return
        rec["decision"] = "sent"
        self.n["sent"] += 1
        self.risk.reserve(o["sig"], it, t_dec)
        self.worker.order(lambda: self.send(it), lambda res: self.post(self._ack, rec, it, m, res))

    def _ack(self, rec: dict, it: Intent, m, res: dict) -> None:
        self.risk.release(rec["sig"])
        rec.update(res)
        sh = float(res.get("fill_sh") or 0.0)
        if res.get("err_kind") in FATAL or "exc" in res:
            self.stop_reason = f"order error: {res.get('err_kind') or res.get('exc')}: {res.get('err')}"
        if sh > 0:
            self.n["filled"] += 1
            rec["fee"] = fee(res["fill_cost"] / sh, sh)
            self.risk.fill(it, sh, res["fill_cost"], rec["fee"])
            x = min(res["t_ack_ns"] / 1e9 + 10, m.end + 2)
            heapq.heappush(self.jobs, (x, next(self.seq), rec["sig"], m))
        else:
            rec["live_done"] = True
            self._maybe_final(rec["sig"])

    def advance(self, now: float) -> None:
        while self.jobs and self.jobs[0][0] <= now:
            _, _, sig, m = heapq.heappop(self.jobs)
            rec = self.pending.get(sig)
            if rec is None:
                continue
            mid = m.book.mid()
            v = (mid if rec["up"] else 1 - mid) if mid == mid else None
            rec.update(book10={"t": now, "bb": m.book.bb, "ba": m.book.ba, "mid_up": mid}, mk10_live=v,
                       live_done=True)
            self._maybe_final(sig)

    def on_paper_final(self, prec: dict) -> None:
        if prec.get("sig") in self.pending:
            self.paper[prec["sig"]] = prec
            self._maybe_final(prec["sig"])

    def _maybe_final(self, sig: str, force: bool = False) -> None:
        rec, p = self.pending.get(sig), self.paper.get(sig)
        if rec is None or (not force and (p is None or not rec.get("live_done"))):
            return
        if p is not None:
            rec["paper"] = {k: p.get(k) for k in PAPER_KEYS}
            rec["paper_mk10_cpd"] = cpd(p.get("fill_sh"), p.get("cost"), p.get("fee"), p.get("mk10"))
        rec["live_mk10_cpd"] = cpd(rec.get("fill_sh"), rec.get("fill_cost"), rec.get("fee", 0.0), rec.get("mk10_live"))
        rec["final"] = not force
        self.sink.write(int(rec["t_signal"] * 1e9), json.dumps(rec, default=_num))
        self.n["written"] += 1
        self.pending.pop(sig, None)
        self.paper.pop(sig, None)

    def flush(self) -> None:
        """Shutdown: write whatever every pending signal has (final = False)."""
        for sig in list(self.pending):
            self._maybe_final(sig, force=True)


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return str(x)
