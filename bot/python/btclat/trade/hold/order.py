"""One hold-test order: sign, POST, then make its end state known before the next one.

- `delayed` ack (the venue's "marketable, subject to matching delay"): GET /data/order every
  `poll_s` until the status leaves delayed; `hold_ms` = send to the first non-delayed poll
  (an upper bound on when the hold ended, one poll interval coarse);
- a GTC / GTD that rests (live) is cancelled at once, then looked up so a partial fill made
  before the cancel is counted;
- the spend (fill cost + taker fee) comes from the lookup when there is one, else the ack.
A `matched` ack straight from the POST means the hold, if any, ran inside the POST round trip."""
from __future__ import annotations

import time

from ..risk.limits import VENUE_MIN_SHARES, fee
from ..venue import parse

RESTING = ("GTC", "GTD")
MAX_POLLS = 40


def _low(x) -> str:
    return str(x or "").lower()


def send(venue, token: str, price: float, otype: str, post_only: bool = False, expiration: int = 0,
         size: float = VENUE_MIN_SHARES, poll_s: float = 0.05, sleep=time.sleep) -> dict:
    s = venue.sign(token, price, size, "BUY", otype, post_only, expiration=expiration)
    if s.order_type != otype or s.price != price or s.size != size or s.side != "BUY":
        raise AssertionError(f"signed order differs from the request: {s.order_type} {s.price} {s.size} {s.side}")
    r = venue.post(s)
    o = parse.order(r)
    rec = {"type": otype, "price": price, "size": size, "post_only": post_only,
           "expiration": expiration, "sign_us": round(s.sign_us, 1), "t_send_ns": r.t_send_ns,
           "t_ack_ns": r.t_ack_ns, "ack_ms": round(r.ms, 3), "post": r.brief(), **o}
    oid, status = o["order_id"], _low(o["status"])
    rec["status_ack"] = status if o["ok"] else (o["err_kind"] or "rejected")
    if o["ok"] and oid and status == "delayed":
        polls = []
        for _ in range(MAX_POLLS):
            sleep(poll_s)
            g = venue.get_order(oid)
            q = parse.lookup(g)
            polls.append({"dt_ms": round((g.t_ack_ns - r.t_send_ns) / 1e6, 3), "status": _low(q["status"]),
                          "matched": q["fill_sh"]})
            if _low(q["status"]) not in ("delayed", ""):
                rec["hold_ms"] = polls[-1]["dt_ms"]
                rec.update(fill_sh=q["fill_sh"], fill_cost=q["fill_cost"], px=q["px"])
                status = _low(q["status"])
                break
        rec["polls"] = polls
    if o["ok"] and oid and otype in RESTING and status in ("live", "delayed"):
        c = venue.cancel(oid)
        rec["cancel"] = c.brief()
        rec["cancelled"] = parse.cancelled(c, oid)
        q = parse.lookup(venue.get_order(oid))
        rec["after_cancel"] = q
        rec.update(fill_sh=max(rec["fill_sh"], q["fill_sh"]), fill_cost=max(rec["fill_cost"], q["fill_cost"]))
        rec["px"] = rec["fill_cost"] / rec["fill_sh"] if rec["fill_sh"] > 0 else None
    rec["status_final"] = status if o["ok"] else rec["status_ack"]
    sh = float(rec["fill_sh"] or 0.0)
    rec["fee"] = fee(rec["fill_cost"] / sh, sh) if sh > 0 else 0.0
    rec["spent"] = float(rec["fill_cost"] or 0.0) + rec["fee"]
    return rec
