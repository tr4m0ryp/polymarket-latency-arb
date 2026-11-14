"""The live fused trigger (Deribit quote + Binance spot/perp), twin of rust/crates/signal/src/trigger.

Per part (one price series): the onset of moves.onsets (first update >= X USD from the series'
own price 1 s earlier, then a 1 s refractory). The Deribit part may weight its move by the size
at the touch: |d| * min(1, S / size_ref) >= X, S = best bid amount on an up move and best ask
amount on a down move (USD contracts); size_ref 0 = no weighting (exactly moves.onsets).
A Deribit onset may need the Binance perp to agree: some perp update (book mid or trade price)
in [t - W, t + W] whose own 1 s change is in the same direction and >= agree USD. Agreement
already seen fires at the Deribit onset; a later one fires at that perp update; none drops it.
Fused fires = part onsets (Binance ones unconfirmed) clustered per direction as moves.cluster
does: a fire opens a move when > win (default 1 s, moves.WIN_NS) after the last opened move of
that direction; win 0 fires on every part onset (one per instant), which is the research
composite: per move, the first fire is exactly the earliest part onset."""
from __future__ import annotations

import numpy as np

from moves import LOOK_NS, REFR_NS, WIN_NS


def deltas(t: np.ndarray, p: np.ndarray) -> np.ndarray:
    """Each update's price minus the series' last price at or before t - 1 s (0 if none)."""
    j = np.searchsorted(t, t - LOOK_NS, side="right") - 1
    return np.where(j >= 0, p - p[np.clip(j, 0, None)], 0.0)


def onsets_w(t: np.ndarray, p: np.ndarray, x: float, w: np.ndarray | None = None) -> list[tuple[int, int]]:
    """moves.onsets with an optional per-update weight on |d| (w None: identical to it)."""
    if len(t) < 2:
        return []
    d = deltas(t, p)
    a = np.abs(d) if w is None else np.abs(d) * w
    out, last = [], -(1 << 62)
    for i in np.flatnonzero(a >= x):
        if t[i] - last >= REFR_NS:
            out.append((int(t[i]), 1 if d[i] > 0 else -1))
            last = t[i]
    return out


def size_weight(t: np.ndarray, p: np.ndarray, bq: np.ndarray, aq: np.ndarray, size_ref: float) -> np.ndarray | None:
    if size_ref <= 0:
        return None
    s = np.where(deltas(t, p) > 0, bq, aq)
    return np.minimum(1.0, s / size_ref)


def agree_times(perp: list[tuple[np.ndarray, np.ndarray]], agree: float) -> dict[int, np.ndarray]:
    """Per direction: sorted times of perp updates whose own 1 s change agrees (>= agree, > 0)."""
    out = {}
    for s in (1, -1):
        ts = [t[(deltas(t, p) * s >= agree) & (deltas(t, p) * s > 0)] for t, p in perp]
        out[s] = np.sort(np.concatenate(ts)) if ts else np.array([], np.int64)
    return out


def confirm(der: list[tuple[int, int]], agr: dict[int, np.ndarray], w_ns: int) -> list[tuple[int, int, int]]:
    """Deribit onsets -> (fire time, dir, 0 = at the onset / 1 = at the agreeing perp update)."""
    out = []
    for t, s in der:
        a = agr[s]
        i = np.searchsorted(a, t - w_ns, side="left")
        if i < len(a) and a[i] <= t:
            out.append((t, s, 0))
        elif i < len(a) and a[i] <= t + w_ns:
            out.append((int(a[i]), s, 1))
    return out


def fuse(cands: list[tuple[int, int, int, str]], win_ns: int = WIN_NS) -> list[tuple[int, int, str]]:
    """cands (t, dir, order, src): sorted by (t, order); a fire opens a move > win after the
    last move of its direction (moves.cluster), the others join it."""
    last = {1: -(1 << 62), -1: -(1 << 62)}
    out = []
    for t, s, _, src in sorted(cands, key=lambda c: (c[0], c[2])):
        if t - last[s] > win_ns:
            last[s] = t
            out.append((t, s, src))
    return out


def fires(parts: dict[str, tuple[np.ndarray, np.ndarray]], der: tuple, x: float, mode: str = "none",
          size_ref: float = 0.0, w_ms: float = 50.0, agree: float = 0.0,
          win_ms: float = 1000.0) -> list[tuple[int, int, str]]:
    """parts: Binance series name -> (t, p) (bn_spot_book, bn_spot_trade, bn_perp_book,
    bn_perp_trade); der: Deribit (t, mid, bid amount, ask amount) or None (Binance only).
    mode: none | size | perp | both (size and perp)."""
    cands = [(t, s, 2, n) for n, (tt, pp) in parts.items() for t, s in onsets_w(tt, pp, x)]
    if der is not None:
        t, p, bq, aq = der
        w = size_weight(t, p, bq, aq, size_ref) if mode in ("size", "both") else None
        on = onsets_w(t, p, x, w)
        if mode in ("perp", "both"):
            perp = [parts[n] for n in ("bn_perp_book", "bn_perp_trade") if n in parts]
            for tf, s, late in confirm(on, agree_times(perp, agree), int(w_ms * 1e6)):
                cands.append((tf, s, 1 - late, "deribit+perp" if late else "deribit"))
        else:
            cands += [(t, s, 2, "deribit") for t, s in on]
    return fuse(cands, int(win_ms * 1e6))
