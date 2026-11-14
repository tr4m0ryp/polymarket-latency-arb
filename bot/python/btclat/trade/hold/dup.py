"""Duplicate-send test (`holdtest --dup`): may one signed order go out on 2-3 connections at
once, first ack wins? Only if the venue keeps ONE order per order hash.

Per repetition: a fresh post-only GTC BUY 5 at 0.01 on the current market's Up token (>= 5
ticks under the bid: unfillable), the identical signed payload POSTed at the same instant on
k separate warm sessions (venue/fanout.py), k = 1 (baseline), 2, 3 in turn; every response
logged (code, ms, status, order id, error kind), then the order cancelled. More than one
DISTINCT accepted order id is the unsafe case: cancel each at once and stop the run."""
from __future__ import annotations

import time

from ..probe import run as probe
from ..risk.limits import HARD_DUP_REPS, VENUE_MIN_SHARES
from ..risk.session import Stop
from ..venue import parse

KS = (1, 2, 3)


def run(venue, session, log, a, fanout, now=time.time, sleep=time.sleep, markets=None) -> dict:
    markets = markets or probe.Markets()
    reps = max(1, min(int(getattr(a, "dup_reps", 5) or 5), HARD_DUP_REPS))
    every = max(float(a.every), 5.0)
    n = {"reps": 0, "orders": 0, "copies": 0, "distinct_gt1": 0}
    for k in KS:
        done = 0
        while done < reps:
            session.check()
            m = markets.current(now())
            bk = venue.book(m["up"]) if m else None
            price = probe.passive_price(bk["bb"]) if bk else None
            if price is None:
                log({"k": k, "decision": "skip:no_market" if m is None else "skip:book_too_low"})
                sleep(every)
                continue
            probe.assert_passive(price, bk["bb"])
            rec = {"k": k, "rep": done, "slug": m["slug"], "bb": bk["bb"], "decision": "sent",
                   "warm_ms": fanout.warm()}
            s = venue.sign(m["up"], price, VENUE_MIN_SHARES, "BUY", "GTC", True)
            if not (s.post_only and s.order_type == "GTC" and s.price == price):
                raise probe.Marketable(f"dup order not post-only GTC at {price}")
            rs = fanout.post(s, k)
            os_ = [parse.order(r) for r in rs]
            rec["copies"] = [{"code": r.code, "ms": round(r.ms, 3), "t_send_ns": r.t_send_ns, "t_ack_ns": r.t_ack_ns,
                              "pop": r.brief()["pop"], "status": o["status"], "order_id": o["order_id"],
                              "err_kind": o["err_kind"], "err": o["err"], "body": r.brief()["body"]}
                             for r, o in zip(rs, os_)]
            ids = sorted({o["order_id"] for o in os_ if o["ok"] and o["order_id"]})
            rec.update(accepted=sum(o["ok"] for o in os_), distinct_ids=ids,
                       first_ack_ms=round(min(r.ms for r in rs), 3), price=price)
            if any(o["fill_sh"] > 0 for o in os_):
                rec["stop"] = "dup order reported a fill: stopping (should be impossible)"
            rec["cancel"] = {}
            for oid in ids:
                c = venue.cancel(oid)
                rec["cancel"][oid] = {"ms": round(c.ms, 3), "ok": parse.cancelled(c, oid)}
            if len(ids) > 1:
                n["distinct_gt1"] += 1
                rec["stop"] = f"{len(ids)} distinct orders accepted from one signed payload: stopping"
            elif any(not v["ok"] for v in rec["cancel"].values()):
                rec["stop"] = "dup cancel not confirmed: stopping (cancel-all on exit)"
            n["reps"] += 1
            n["orders"] += len(ids)
            n["copies"] += k
            log(rec)
            if rec.get("stop"):
                raise Stop(rec["stop"])
            if any(o["err_kind"] in probe.FATAL for o in os_):
                raise Stop(f"dup test rejected: {[o['err_kind'] for o in os_]}")
            done += 1
            sleep(every)
    return n
