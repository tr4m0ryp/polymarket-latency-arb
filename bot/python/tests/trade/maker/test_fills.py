"""Maker fills: the tape parser, the simulator's maker fill rule live (trade through, queue at
our price, book crossing after the hold), dry end to end into the fills stream, and the real
fills of live runs found by order lookups."""
import json

import pytest

from btclat.trade.maker.fills.infer import Infer
from btclat.trade.maker.fills.live import LiveFills
from btclat.trade.maker.fills.trades import TradeTap, parse_trades
from btclat.trade.maker.ops.dry import DryOps

from .fakes import START, book, lines, manager, q

TOK = {"UP": ("s", True), "DN": ("s", False)}


def _ltp(asset, side, px, size, ts_ms=1_791_800_200_000):
    return {"event_type": "last_trade_price", "asset_id": asset, "side": side, "price": str(px), "size": str(size),
            "timestamp": str(ts_ms)}


def test_parse_trades_up_frame():
    raw = json.dumps([_ltp("UP", "BUY", 0.40, 10), _ltp("DN", "BUY", 0.60, 3), _ltp("DN", "SELL", 0.6, 2),
                      _ltp("XX", "BUY", 0.5, 1), {"event_type": "book"}])
    tr = parse_trades(5.0, raw, TOK)
    assert [(x["d"], x["p"], x["size"]) for x in tr] == [(1, 0.4, 10.0), (-1, 0.4, 3.0), (1, 0.4, 2.0)]
    assert tr[0]["ts"] == pytest.approx(1_791_800_200.0) and tr[0]["slug"] == "s"
    got, raw_sink = [], []
    tap = TradeTap(got.append, raw=type("S", (), {"write": lambda self, t, r: raw_sink.append(r)})())
    tap.add_market({"slug": "s", "up": "UP", "down": "DN"})
    tap.write(5_000_000_000, json.dumps(_ltp("UP", "SELL", 0.45, 4)))
    tap.write(5_000_000_000, json.dumps({"event_type": "price_change"}))
    assert len(got) == 1 and got[0]["d"] == -1 and len(raw_sink) == 2


class O:
    def __init__(self, side="bid", tick=47, t_on=100.0, slug="s"):
        self.side, self.tick, self.t_on, self.slug = side, tick, t_on, slug
        self.size, self.matched, self.t_off = 5.0, 0.0, float("nan")


def _infer(bk):
    got = []
    return Infer(lambda o, x, t, how: got.append((x, t, how)), lambda slug: bk), got


def _tr(ts, d, p, size):
    return {"slug": "s", "ts": ts, "d": d, "p": p, "size": size}


def test_trade_through_and_queue():
    inf, got = _infer(book(bb=47, ba=55, size=100.0))      # 100 shares ahead of us at 47
    o = O()
    inf.on_live(o)
    inf.on_trade(_tr(99.0, -1, 0.40, 50))                   # before we rest
    inf.on_trade(_tr(100.1, 1, 0.40, 50))                   # a buyer: never hits a bid
    inf.on_trade(_tr(100.2, -1, 0.47, 60))                  # at our price: queue 100 -> 40
    inf.on_trade(_tr(100.3, -1, 0.47, 42))                  # 40 ahead, 2 fill us
    inf.on_trade(_tr(100.4, -1, 0.46, 9))                   # through: the 3 left
    assert got == [(2.0, 100.3, "queue"), (3.0, 100.4, "trade")]
    o.t_off = 101.0
    inf.on_off(o)
    inf.on_trade(_tr(101.5, -1, 0.40, 9))
    assert len(got) == 2


def test_ask_side_mirror():
    inf, got = _infer(book())
    inf.on_live(O(side="ask", tick=53))
    inf.on_trade(_tr(100.2, -1, 0.60, 9))                   # seller: never lifts an ask
    inf.on_trade(_tr(100.3, 1, 0.55, 9))                    # buyer above our ask: fills
    assert got == [(5.0, 100.3, "trade")]


@pytest.mark.parametrize("t_off,filled", [(float("inf"), True), (100.2, False)])
def test_crossing_fills_after_the_hold(t_off, filled):
    bk = book()
    inf, got = _infer(bk)
    o = O()
    inf.on_live(o)
    bk.apply(100.1, 100.1, False, [(-1, 46, 30.0)])         # an ask at 46 <= our bid 47
    m = type("M", (), {"meta": {"slug": "s"}, "book": bk})()
    inf.on_book(m, 100.1, 100.1)
    o.t_off = t_off
    inf.on_off(o)
    inf.on_tick(100.1 + 0.27 + 0.05)
    assert got == []
    inf.on_tick(100.1 + 0.27 + 0.2)
    assert got == ([(5.0, pytest.approx(100.37), "cross")] if filled else [])


def test_dry_end_to_end_fill_and_markout(tmp_path):
    w = manager(tmp_path)
    later = []
    ops = DryOps(lambda dt, fn: later.append(fn), w.clock.now, lambda slug: w.m.book, L=0.05)
    w.mgr.ops = ops
    inf = Infer(w.mgr.fill, lambda slug: w.m.book)
    w.mgr.watchers = [inf]
    w.mgr.on_quote(w.m, q(w.clock.t, ask=0))
    later.pop(0)()                                          # insert acked at t + L: resting
    o = w.mgr.slots[(w.m.meta["slug"], "bid")].order
    assert o.state == "live" and o.oid.startswith("dry:")
    inf.on_trade({"slug": w.m.meta["slug"], "ts": w.clock.t + 0.01, "d": -1, "p": 0.40, "size": 20})
    assert o.state == "done" and w.mgr.n["fills"] == 1
    later.pop(0)() if later else None
    w.mgr.on_quote(w.m, q(w.clock.t + 0.5, bid=0, ask=0, pull_bid=True))   # the model pulls 0.5 s later
    w.log.advance(w.clock.t + 11)
    f = lines(w.sinks["fills"])
    assert len(f) == 1 and f[0]["shares"] == 5.0 and f[0]["px"] == 0.47 and f[0]["pull_1s"] is True
    assert f[0]["mk10"] == pytest.approx(0.50) and f[0]["final"] is True


def test_dry_post_only_cross_rejected(tmp_path):
    w = manager(tmp_path)
    later = []
    w.mgr.ops = DryOps(lambda dt, fn: later.append(fn), w.clock.now, lambda slug: w.m.book)
    w.mgr.on_quote(w.m, q(w.clock.t, bid=47, ask=0))
    w.m.book.apply(START + 61, START + 61, False, [(-1, 47, 10.0)])   # ask moved to our bid
    later.pop(0)()
    acks = [r for r in lines(w.sinks["ops"]) if r["kind"] == "insert_ack"]
    assert acks[0]["err_kind"] == "post_only_crosses" and w.mgr.stop_reason is None


def test_live_fills_by_lookup(tmp_path):
    w = manager(tmp_path)
    lf = LiveFills(w.ops, w.mgr, w.clock.now, w.log, every=3.0)
    w.mgr.watchers = [lf]
    w.mgr.on_quote(w.m, q(w.clock.t, ask=0))
    o = w.ops.ack("insert")
    slug = w.m.meta["slug"]
    lf.on_trade({"slug": slug, "ts": w.clock.t + 0.2, "d": 1, "p": 0.47, "size": 9})     # buyer: no
    assert w.ops.n("lookup") == 0
    lf.on_trade({"slug": slug, "ts": w.clock.t + 0.3, "d": -1, "p": 0.47, "size": 9})
    lf.on_trade({"slug": slug, "ts": w.clock.t + 0.4, "d": -1, "p": 0.45, "size": 9})    # queued behind
    assert w.ops.n("lookup") == 1
    w.ops.ack("lookup", status="LIVE", fill_sh=2.0)
    assert o.matched == 2.0 and w.ops.n("lookup") == 2
    f = w.mgr.n["fills"]
    w.ops.ack("lookup", status="MATCHED", fill_sh=5.0)
    assert o.matched == 5.0 and o.state == "done" and w.mgr.n["fills"] == f + 1
    rs = lines(w.sinks["ops"])
    assert sum(r["kind"] == "lookup" for r in rs) == 2
    w.ops.ack("lookup") if any(p[0] == "lookup" for p in w.ops.pending) else None   # the final lookup
    w.log.advance(w.clock.t + 20)
    fl = lines(w.sinks["fills"])
    assert [x["shares"] for x in fl] == [2.0, 3.0] and fl[0]["t_fill"] == pytest.approx(w.clock.t + 0.3)


def test_live_fills_poll_and_final(tmp_path):
    w = manager(tmp_path)
    lf = LiveFills(w.ops, w.mgr, w.clock.now, w.log, every=3.0)
    w.mgr.watchers = [lf]
    w.mgr.on_quote(w.m, q(w.clock.t, ask=0))
    w.ops.ack("insert")
    lf.on_tick(w.clock.t + 1)
    assert w.ops.n("lookup") == 0
    w.clock.t += 3.1
    lf.on_tick(w.clock.t)
    assert w.ops.n("lookup") == 1
    w.ops.ack("lookup")
    w.mgr.on_quote(w.m, q(w.clock.t, bid=0, ask=0))
    w.ops.ack("cancel")
    assert w.ops.n("lookup") == 2                            # after the cancel: shares matched before it
    w.ops.ack("lookup", status="CANCELED", fill_sh=1.0)
    assert w.mgr.n["fills"] == 1 and w.mgr.n["filled_sh"] == 1.0
