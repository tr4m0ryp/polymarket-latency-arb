"""Hold test: is the venue's taker hold (~250 ms; FAK acks 270-296 ms p50 live vs 56 ms for
a resting insert) applied to every marketable order type, or only to FAK / FOK?

Each cycle on the current BTC 5m market reads both books and takes the outcome whose best
ask lies in the band (default 0.02-0.08), then sends
- a marketable BUY AT that ask of max(5, ceil(1.05 / ask)) shares, just over the venue's $1
  minimum for a marketable BUY (micro logged 87 skips under it; 0.05 -> 21 sh, $1.05), the
  order type rotating FAK, FOK, GTC, GTD
  (GTD expiring server-now + 70 s; the venue wants >= 60 s); a resting remainder is
  cancelled at once and looked up (hold/order.py);
- a control: post-only GTC BUY 5 at 0.01 on the other outcome, >= 5 ticks under its bid
  (the probe's ~56 ms baseline), cancelled at once.
Which of the two goes first alternates by cycle. Caps (risk/limits.py): spend (fills + fees)
<= $5 per run, checked against the worst case of the next order before it is sent (about 4
fills); <= $1.60 per marketable order; <= 40 marketable orders and cycles; ask <= 0.30. A
fill on a control, an unconfirmed cancel, a region / auth rejection, or a minimum-notional
rejection stops the run; the session sends cancel-all on any exit."""
from __future__ import annotations

import math
import time

from ..probe import run as probe
from ..risk.limits import (HARD_HOLD_BUDGET, HARD_HOLD_CYCLES, HARD_HOLD_MARKETABLE, HARD_HOLD_MAX_ASK,
                           HARD_HOLD_MAX_NOTIONAL, HARD_MIN_PROBE_EVERY, VENUE_MIN_SHARES, fee)
from ..risk.session import Stop
from . import order

TYPES = ("FAK", "FOK", "GTC", "GTD")
GTD_S = 70
BAND = (0.02, 0.08)
TARGET_NOTIONAL = 1.05          # $: just over the venue's $1 minimum for a marketable BUY


def size_for(ask: float) -> float:
    """Whole shares with notional just over $1 (never under the 5-share minimum)."""
    sh = float(max(VENUE_MIN_SHARES, math.ceil(round(TARGET_NOTIONAL / ask, 6))))
    if sh * ask > HARD_HOLD_MAX_NOTIONAL + 1e-9:
        raise SystemExit(f"refusing: {sh:g} sh at {ask} = ${sh * ask:.2f} > ${HARD_HOLD_MAX_NOTIONAL}")
    return sh


def band(text: str | None) -> tuple[float, float]:
    lo, hi = BAND if not text else (float(x) for x in text.split(","))
    if not (0.01 < lo <= hi <= HARD_HOLD_MAX_ASK):
        raise SystemExit(f"refusing: ask band {lo},{hi} outside (0.01, {HARD_HOLD_MAX_ASK}]")
    return round(lo, 2), round(hi, 2)


def pick(books: dict, lo: float, hi: float) -> str | None:
    """Token whose best ask is in [lo, hi] (the cheaper one if both are)."""
    ok = [(b["ba"], t) for t, b in books.items() if b["ba"] == b["ba"] and lo - 1e-9 <= b["ba"] <= hi + 1e-9]
    return min(ok)[1] if ok else None


def run(venue, session, log, a, now=time.time, sleep=time.sleep, markets=None) -> dict:
    markets = markets or probe.Markets()
    lo, hi = band(getattr(a, "ask_band", None))
    want = min(a.n or 24, HARD_HOLD_CYCLES)
    every = max(float(a.every), HARD_MIN_PROBE_EVERY)
    t_end = now() + (a.hours or 1.0) * 3600
    clock = getattr(venue, "server_now", now)
    n = {"cycles": 0, "marketable": 0, "controls": 0, "skipped": 0, "spent": 0.0, "filled": 0}
    while n["cycles"] < want and now() < t_end:
        session.check()
        t0 = now()
        m = markets.current(t0)
        books = {tok: venue.book(tok) for tok in (m["up"], m["down"])} if m else {}
        tok = pick(books, lo, hi) if m else None
        if tok is None:
            n["skipped"] += 1
            log({"cycle": n["cycles"], "role": "skip", "decision": "skip:no_market" if m is None else "skip:no_cheap_side",
                 "asks": {("up" if t == m["up"] else "down"): b["ba"] for t, b in books.items()} if m else None})
            sleep(every)
            continue
        ask = round(books[tok]["ba"], 2)
        other = m["down"] if tok == m["up"] else m["up"]
        size = size_for(ask)
        worst = size * ask + fee(ask, size)
        if n["spent"] + worst > HARD_HOLD_BUDGET or n["marketable"] >= HARD_HOLD_MARKETABLE:
            log({"cycle": n["cycles"], "role": "skip", "decision": "stop:budget", "spent": n["spent"], "next_worst": worst})
            break
        otype = TYPES[n["cycles"] % len(TYPES)]
        exp = int(clock()) + GTD_S if otype == "GTD" else 0
        base = {"cycle": n["cycles"], "slug": m["slug"], "book_ms": {t[:6]: round(b["resp"].ms, 3) for t, b in books.items()}}
        legs = [("marketable", tok, ask, otype, False, exp, size),
                ("control", other, None, "GTC", True, 0, VENUE_MIN_SHARES)]
        for role, t, price, ot, post_only, e, sh in (legs if n["cycles"] % 2 else legs[::-1]):
            b = books[t]
            if role == "control":
                price = probe.passive_price(b["bb"])
                if price is None:
                    log({**base, "role": "control", "decision": "skip:book_too_low", "bb": b["bb"]})
                    continue
                probe.assert_passive(price, b["bb"])
            rec = order.send(venue, t, price, ot, post_only, e, size=sh, sleep=sleep)
            rec.update(base, role=role, side="up" if t == m["up"] else "down", bb=b["bb"], ba=b["ba"], decision="sent")
            n["spent"] += rec["spent"]
            n["marketable" if role == "marketable" else "controls"] += 1
            n["filled"] += rec["fill_sh"] > 0
            rec["spent_run"] = round(n["spent"], 4)
            log(rec)
            _check(rec, n["spent"])
        n["cycles"] += 1
        wait = every - (now() - t0)
        if wait > 0 and n["cycles"] < want:
            sleep(wait)
    return n


def _check(rec: dict, spent: float) -> None:
    k = rec.get("err_kind")
    if k in probe.FATAL:
        raise Stop(f"hold test rejected: {k}: {rec.get('err')}")
    if k == "min_notional":
        raise Stop(f"venue rejects a ${rec['size'] * rec['price']:.2f} marketable BUY: its minimum notional is higher "
                   f"than ${TARGET_NOTIONAL} ({rec.get('err')})")
    if rec["role"] == "control" and rec["fill_sh"] > 0:
        raise Stop("control order reported a fill: stopping (should be impossible)")
    if rec.get("cancelled") is False:
        raise Stop(f"cancel of {rec.get('order_id')} not confirmed: stopping (cancel-all on exit)")
    if spent > HARD_HOLD_BUDGET + 1e-9:
        raise Stop(f"hold test spent ${spent:.2f} > ${HARD_HOLD_BUDGET}: stopping")
