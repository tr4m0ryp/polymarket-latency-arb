"""(b) Per BTC move, which feed shows it first on this box, and by how many ms.

Onset of a signal: first update whose price is >= X USD away from that signal's own price 1 s
earlier (basis-free), then a 1 s refractory period. Onsets of all signals within 1 s of each other
and in the same direction form one move; moves where >= MIN_SHARE of the venue signals fire are
kept (market-wide moves, not one book flickering). Composite onsets (signals.COMPOSITES) are the
earliest of their parts. Per signal: delay vs the first onset, share first, and the gain over each
reference (reference onset - signal onset, > 0 = signal earlier)."""
from __future__ import annotations

import numpy as np

from ids import q
from signals import COMPOSITES

WIN_NS, REFR_NS, LOOK_NS = 1_000_000_000, 1_000_000_000, 1_000_000_000
MIN_SHARE = 0.5
REFS = ("BASE_spot_comb_a", "BASE_bot_fanin", "bn_best")


def onsets(t: np.ndarray, p: np.ndarray, x: float) -> list[tuple[int, int]]:
    if len(t) < 2:
        return []
    j = np.searchsorted(t, t - LOOK_NS, side="right") - 1
    d = np.where(j >= 0, p - p[np.clip(j, 0, None)], 0.0)
    out, last = [], -(1 << 62)
    for i in np.flatnonzero(np.abs(d) >= x):
        if t[i] - last >= REFR_NS:
            out.append((int(t[i]), 1 if d[i] > 0 else -1))
            last = t[i]
    return out


def cluster(sig_on: dict[str, list[tuple[int, int]]]) -> list[dict]:
    ev = sorted((t, s, n) for n, lst in sig_on.items() for t, s in lst)
    moves: list[dict] = []
    open_: dict[int, dict] = {}
    for t, s, n in ev:
        c = open_.get(s)
        if c is None or t - c["t0"] > WIN_NS:
            c = {"t0": t, "dir": s, "on": {}}
            open_[s] = c
            moves.append(c)
        c["on"].setdefault(n, t)
    for m in moves:
        for comp, parts in COMPOSITES.items():
            ts = [m["on"][p] for p in parts if p in m["on"]]
            if ts:
                m["on"][comp] = min(ts)
    return moves


def market_moves(sigs: dict, x: float) -> tuple[list[dict], list[str]]:
    sig_on = {n: onsets(t, p, x) for n, (t, p) in sigs.items()}
    venue = [n for n in sigs if not n.startswith("BASE_")]
    keep = [m for m in cluster(sig_on) if sum(n in m["on"] for n in venue) >= MIN_SHARE * len(venue)]
    return keep, venue


def race(sigs: dict, x: float) -> dict:
    moves, venue = market_moves(sigs, x)
    res = {"threshold_usd": x, "moves": len(moves), "signals": {}}
    for n in list(sigs) + list(COMPOSITES):
        lag, first = [], 0
        for m in (m["on"] for m in moves):
            if n in m:
                t0 = min(m[v] for v in venue if v in m)
                lag.append((m[n] - t0) / 1e6)
                first += m[n] == t0
        r = {"fired": len(lag), "delay_vs_first_venue_ms": q(lag),
             "first_share": round(first / max(1, len(moves)), 3)}
        for b in REFS:
            g = [(m["on"][b] - m["on"][n]) / 1e6 for m in moves if n in m["on"] and b in m["on"]]
            r["gain_vs_" + b + "_ms"] = q(g, (10, 25, 50, 75, 90))
            r["earlier_than_" + b + "_share"] = round(float(np.mean([v > 0 for v in g])), 3) if g else None
        res["signals"][n] = r
    return res
