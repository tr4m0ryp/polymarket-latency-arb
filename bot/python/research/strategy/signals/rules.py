"""Decision rules: feature table of one market -> taker orders (t, side, shares, limit).

side +1 = buy Up, -1 = buy Down; prices are in the bought token's terms. `seen` = the best
ask of that token in our view at t (Up ask, or 1 - Up bid for Down).

- momentum: the leaders' family. Fire when the move over `win` s of `src` is >= thr (bp,
  or z-units if `znorm`), side = its sign, limit = seen + slip, global refractory `refr`.
- fair: invention 1. Fire when fair - seen - fee >= margin on either side; limit = the
  highest tick still worth >= `m_fill` after the fee; size grows with the edge."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import fee

TICKS = np.arange(1, 100) / 100


def _seen(df: pd.DataFrame, side: np.ndarray) -> np.ndarray:
    return np.where(side > 0, df["ba"].to_numpy() / 100, 1 - df["bb"].to_numpy() / 100)


def _gate(df, side, seen, band, tleft, fav_max):
    mid = df["mid"].to_numpy()
    ok = (seen >= band[0]) & (seen <= band[1]) & (df["secs_left"].to_numpy() >= tleft)
    ok &= np.maximum(mid, 1 - mid) <= fav_max
    ok &= (df["bb"].to_numpy() > 0) & (df["ba"].to_numpy() < 100)
    return ok


def _refractory(t, ok, refr):
    out, last = [], -np.inf
    for i in np.flatnonzero(ok):
        if t[i] - last >= refr:
            out.append(i)
            last = t[i]
    return np.array(out, dtype=np.int64)


def momentum(df, src="spot", win=3.0, thr=0.5, refr=1.0, band=(0.01, 0.99), tleft=30.0,
             fav_max=0.9, shares=60.0, slip=0.01, znorm=False):
    r = df[f"{src}_r{win:g}"].to_numpy(dtype=float)
    x = r * df["zs"].to_numpy() * 1e-4 if znorm else r
    side = np.sign(r)
    seen = _seen(df, side)
    ok = (np.abs(x) >= thr) & (side != 0) & _gate(df, side, seen, band, tleft, fav_max)
    i = _refractory(df["t"].to_numpy(), ok, refr)
    n = len(i)
    return {"idx": i, "t": df["t"].to_numpy()[i], "side": side[i], "shares": np.full(n, shares),
            "limit": np.minimum(seen[i] + slip, 0.99), "edge": np.full(n, np.nan)}


def best_limit(value: np.ndarray, m_fill: float) -> np.ndarray:
    """Highest tick p with value - p - fee(p) >= m_fill (0 if none)."""
    net = value[:, None] - TICKS[None, :] - fee(TICKS)[None, :]
    ok = net >= m_fill
    k = np.where(ok.any(1), 98 - np.argmax(ok[:, ::-1], axis=1), -1)
    return np.where(k >= 0, TICKS[np.clip(k, 0, None)], 0.0)


def fair(df, p_fair, margin=0.03, m_fill=0.01, refr=0.5, band=(0.05, 0.95), tleft=20.0,
         fav_max=0.97, base=60.0, kelly=0.0, max_sh=300.0):
    """p_fair: fair P(Up) per row (from signals.fair). Size = base, plus kelly * edge / price
    shares per $ of edge when kelly > 0, capped at max_sh."""
    up_seen, dn_seen = _seen(df, np.ones(len(df))), _seen(df, -np.ones(len(df)))
    e_up = p_fair - up_seen - fee(up_seen)
    e_dn = (1 - p_fair) - dn_seen - fee(dn_seen)
    side = np.where(e_up >= e_dn, 1.0, -1.0)
    edge = np.maximum(e_up, e_dn)
    seen = np.where(side > 0, up_seen, dn_seen)
    ok = (edge >= margin) & _gate(df, side, seen, band, tleft, fav_max) & np.isfinite(p_fair)
    i = _refractory(df["t"].to_numpy(), ok, refr)
    val = np.where(side[i] > 0, p_fair[i], 1 - p_fair[i])
    lim = best_limit(val, m_fill)
    sh = base + kelly * edge[i] / np.maximum(seen[i], 0.05) if kelly > 0 else np.full(len(i), base)
    return {"idx": i, "t": df["t"].to_numpy()[i], "side": side[i], "shares": np.minimum(sh, max_sh),
            "limit": lim, "edge": edge[i]}


def quotes(df, p_fair, half=0.02, band=(0.10, 0.90), tleft=30.0, pull_bp=None, pull_win=0.2,
           pull_src="perp"):
    """Invention 2: maker quotes off the perp fair value. Target Up bid / ask ticks per
    candidate (0 = no quote): fair -/+ half, never crossing our view of the book (post-only).
    pull_bp: pull both quotes while `pull_src` (perp mid, or pmic = perp microprice) moved
    >= pull_bp over the last pull_win s."""
    bb, ba = df["bb"].to_numpy(), df["ba"].to_numpy()
    b = np.minimum(np.floor((p_fair - half) * 100 + 1e-9), ba - 1)
    a = np.maximum(np.ceil((p_fair + half) * 100 - 1e-9), bb + 1)
    mid = df["mid"].to_numpy()
    ok = (mid >= band[0]) & (mid <= band[1]) & (df["secs_left"].to_numpy() >= tleft)
    ok &= np.isfinite(p_fair) & (bb > 0) & (ba < 100)
    if pull_bp is not None:
        r = np.abs(np.nan_to_num(df[f"{pull_src}_r{pull_win:g}"].to_numpy(dtype=float)))
        ok &= r < pull_bp
    b = np.where(ok & (b >= 1), b, 0).astype(int)
    a = np.where(ok & (a <= 99), a, 0).astype(int)
    return df["t"].to_numpy(), b, a


def quotes_book(df, p_fair, pull=0.01, improve=False, band=(0.10, 0.90), tleft=30.0):
    """Invention 2b: book-anchored maker. Join (or, if the spread allows, improve by a tick)
    the best bid and ask in our view; pull the side the perp fair says is about to be run
    over: no bid while fair < mid - pull, no ask while fair > mid + pull."""
    bb, ba = df["bb"].to_numpy(), df["ba"].to_numpy()
    mid = df["mid"].to_numpy()
    wide = (ba - bb) >= 2
    b = np.where(improve & wide, bb + 1, bb)
    a = np.where(improve & wide, ba - 1, ba)
    ok = (mid >= band[0]) & (mid <= band[1]) & (df["secs_left"].to_numpy() >= tleft)
    ok &= np.isfinite(p_fair) & (bb > 0) & (ba < 100)
    b = np.where(ok & (p_fair >= mid - pull), b, 0).astype(int)
    a = np.where(ok & (p_fair <= mid + pull), a, 0).astype(int)
    return df["t"].to_numpy(), b, a


def micro(df, win=0.1, thr=0.002, refr=0.2, band=(0.01, 0.99), tleft=30.0, fav_max=0.9,
          shares=60.0, slip=0.02, p_fair=None, margin=None, spot=True, agree=False):
    """Microprice trigger (the leaders' real trigger, reports/hidden-trigger.md): fire when
    the perp microprice moved >= thr bp over the last `win` s; side = sign of the perp (+ spot)
    microprice change. With p_fair / margin: also require fair - seen - fee >= margin.
    agree: only when the perp and spot microprices moved the same way (both non-zero)."""
    pm = np.nan_to_num(df[f"pmic_r{win:g}"].to_numpy(dtype=float))
    sm = np.nan_to_num(df[f"smic_r{win:g}"].to_numpy(dtype=float)) if spot else 0.0
    side = np.sign(pm + sm)
    seen = _seen(df, side)
    ok = (np.abs(pm) >= thr) & (side != 0) & _gate(df, side, seen, band, tleft, fav_max)
    if agree:
        ok &= np.sign(pm) * np.sign(sm) > 0
    edge = np.full(len(df), np.nan)
    if p_fair is not None:
        val = np.where(side > 0, p_fair, 1 - p_fair)
        edge = val - seen - fee(seen)
        ok &= edge >= margin
    i = _refractory(df["t"].to_numpy(), ok, refr)
    return {"idx": i, "t": df["t"].to_numpy()[i], "side": side[i], "shares": np.full(len(i), shares),
            "limit": np.minimum(seen[i] + slip, 0.99), "edge": edge[i]}
