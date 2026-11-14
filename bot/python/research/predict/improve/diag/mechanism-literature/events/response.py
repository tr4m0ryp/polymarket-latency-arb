"""How the Polymarket book answers one Binance event (venue clocks: Binance T vs Polymarket ts).

Per event, side s = +1 (fair up: the stale quote is the Up ask) or -1 (the Up bid):
- lag_q: time until the stale best level is gone (ask above a0 / bid below b0), censored;
- lag_m: time until the venue mid has moved >= 1 c toward s;
- snipe: a taker trade in direction s at or through the stale price before lag_q
  (Foucault-Kozhan-Tham: the stale quote ended in a trade, not a requote); t_snipe, v_snipe;
- n_s{lo} / n_o{lo}: taker prints toward / against s in windows [T0 + lo, T0 + hi) (the
  excess of n_s over n_o, by window, is the rival takers' reaction clock);
- v{L}_{h}: per-share value of OUR taker (decided at receipt t0, matched at t0 + L + 150 ms
  on the venue book) marked at the venue mid h s later, after fee; vseen_{h}: same at the
  price we saw at t0 (no hold); surv{L}: share of the seen level still resting at the match;
- pass3: venue mid move over 3 s (s-oriented, c); imp3: perp move over 3 s in cents."""
from __future__ import annotations

import numpy as np

from research.strategy import DT, fee
from .. import CENSOR, HOLD, LS

NG = int(CENSOR / DT)
WIN = ((-0.3, 0.0), (0.0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.5), (0.5, 1.0), (1.0, 2.0))


def flow(tr: dict):
    """Taker trades in the Up frame (sim/maker.py _flow): venue ts, +1 = bought Up exposure,
    Up-frame price, size."""
    if not tr:
        z = np.zeros(0)
        return z, z, z, z
    o = np.argsort(tr["ts"], kind="stable")
    up = tr["up"][o].astype(bool)
    d = np.where(up, 1, -1) * tr["side"][o]
    p = np.where(up, tr["px"][o], 1 - tr["px"][o]).astype(float)
    return tr["ts"][o], d, np.round(p, 4), tr["size"][o].astype(float)


def _first(cond: np.ndarray) -> int:
    k = int(np.argmax(cond)) if len(cond) else 0
    return k if len(cond) and cond[k] else -1


def _val(s, px, mid):
    """s-oriented per-share value of buying at Up-frame price px, marked at Up mid."""
    if not (0 < px < 1) or not np.isfinite(mid):
        return np.nan
    return mid - px - fee(px) if s > 0 else (1 - mid) - (1 - px) - fee(1 - px)


def respond(book, fl, T0: float, t0: float, s: int) -> dict:
    ts, d, p, sz = fl
    g0 = int(book.g_floor(T0))
    bb0, ba0 = int(book.bb[g0]), int(book.ba[g0])
    out = {"bb0": bb0, "ba0": ba0, "spr0": ba0 - bb0}
    if bb0 <= 0 or ba0 >= 100:
        return out
    col = 100 + ba0 if s > 0 else bb0
    out["size0"] = float(book.size[g0, col])
    mid0 = (bb0 + ba0) / 200
    seg = slice(g0 + 1, min(g0 + 1 + NG, book.n))
    rel = book.t0 + np.arange(seg.start, seg.stop) * DT - T0
    k = _first(book.ba[seg] > ba0) if s > 0 else _first(book.bb[seg] < bb0)
    out["lag_q"] = rel[k] if k >= 0 else np.nan
    mids = book.mid(np.arange(seg.start, seg.stop))
    km = _first(s * (mids - mid0) >= 0.01 - 1e-9)
    out["lag_m"] = rel[km] if km >= 0 else np.nan
    end = T0 + (out["lag_q"] if k >= 0 else CENSOR) + 0.005
    px0 = (ba0 if s > 0 else bb0) / 100
    hit = (d == s) & ((p <= px0 + 1e-9) if s > 0 else (p >= px0 - 1e-9))
    a, b = np.searchsorted(ts, [T0, end])
    j = np.flatnonzero(hit[a:b])
    out["snipe"] = float(len(j) > 0)
    out["t_snipe"] = ts[a + j[0]] - T0 if len(j) else np.nan
    out["v_snipe"] = float(sz[a + j].sum())
    for lo, hi in WIN:  # taker prints toward s vs against s, any price (rival reaction clock)
        a2, b2 = np.searchsorted(ts, [T0 + lo, T0 + hi])
        out[f"n_s{lo:g}"] = int((d[a2:b2] == s).sum())
        out[f"n_o{lo:g}"] = int((d[a2:b2] == -s).sum())
    gs = int(book.g_floor(t0))
    bs, as_ = int(book.bb_r[gs]), int(book.ba_r[gs])
    pseen = (as_ if s > 0 else bs) / 100
    cseen = 100 + as_ if s > 0 else bs
    q_seen = float(book.size[int(book.g_floor(t0)), cseen]) if 0 < pseen < 1 else 0.0
    for L in LS:
        tm = t0 + L / 1000 + HOLD
        gm = int(book.g_ceil(tm))
        pm = (book.ba[gm] if s > 0 else book.bb[gm]) / 100
        for h in (1, 10):
            mk = float(book.mid(book.g_ceil(tm + h)))
            out[f"v{L}_{h}"] = _val(s, pm, mk)
            if L == 0:
                out[f"vseen_{h}"] = _val(s, pseen, mk)
        out[f"surv{L}"] = float(book.size[gm, cseen]) / q_seen if q_seen > 0 else np.nan
        out[f"slip{L}"] = s * (pm - pseen) * 100 if 0 < pseen < 1 and 0 < pm < 1 else np.nan
    out["pass3"] = s * (float(book.mid(book.g_ceil(T0 + 3))) - mid0) * 100
    return out
