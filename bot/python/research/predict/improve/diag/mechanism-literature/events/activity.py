"""Activity state at each event (all strictly before the event, no look-ahead), plus the Binance
move's persistence and our feed lags.

- pmsg10: perp bookTicker updates per s over the last 10 s (leading-venue message load);
- pvol30: perp mid path length over the last 30 s, bp; cvol30 = pvol30 * delta (cents of
  Polymarket fair-value churn per 30 s: what the follower's makers must track);
- rv60: std of 1 s perp log-mid changes over the last 60 s, bp;
- smsg10: spot bookTicker updates per s; pmtr30: Polymarket trade prints in this market over
  the last 30 s; pmupd10: Polymarket book messages per s (maker requote load); ev60: events
  of this market in the last 60 s;
- per{h}: perp move from the pre-event base to t0 + h, over the initial move (persistence);
- imp3: perp move to t0 + 3 s in Polymarket cents (s-oriented);
- lag_feed: our perp receipt minus Binance T; lag_spot: same for the last spot trade;
  Tspan / tspan: Binance-clock / receipt-clock span of the detected move (Tspan >> tspan =
  a backlog flushed old moves into one receipt window); lag_pmfeed: median Polymarket receipt minus
  venue ts over +-1 s."""
from __future__ import annotations

import numpy as np


def _at(t, x, q):
    j = np.searchsorted(t, q, side="right") - 1
    return np.where(j >= 0, x[np.clip(j, 0, None)], np.nan)


def activity(perp, lm, spot_bk, spot_tr, ev, fl_ts, e: dict) -> dict:
    t, T = perp["t"], perp["T"]
    k, base, s = e["k"], e["base"], e["side"]
    t0 = t[k]
    out = {"t0": t0, "T0": T[k], "lag_feed": t0 - T[k]}
    out["Tspan"] = T[k] - T[base]          # Binance-clock span of the move we saw in LOOK s
    out["tspan"] = t0 - t[base]
    if spot_tr:
        out["lag_spot"] = _at(spot_tr["t"], spot_tr["t"] - spot_tr["T"], t0)
    out["pmsg10"] = (np.searchsorted(t, t0) - np.searchsorted(t, t0 - 10)) / 10
    dl = np.abs(np.diff(lm, prepend=lm[0]))
    cum = np.cumsum(dl)
    out["pvol30"] = _at(t, cum, t0 - 1e-6) - _at(t, cum, t0 - 30)
    out["cvol30"] = out["pvol30"] * e["delta"]
    rv = []
    for x in t0:
        g = _at(t, lm, x - np.arange(60, -1, -1.0))
        dg = np.diff(g)
        rv.append(np.nanstd(dg) if np.isfinite(dg).sum() > 10 else np.nan)
    out["rv60"] = np.array(rv)
    st = spot_bk.get("t", np.zeros(0))
    out["smsg10"] = (np.searchsorted(st, t0) - np.searchsorted(st, t0 - 10)) / 10
    out["pmtr30"] = np.searchsorted(fl_ts, out["T0"]) - np.searchsorted(fl_ts, out["T0"] - 30)
    ets = np.sort(np.where(np.isfinite(ev["ts"]), ev["ts"], ev["t"]))
    out["pmupd10"] = (np.searchsorted(ets, out["T0"]) - np.searchsorted(ets, out["T0"] - 10)) / 10
    out["ev60"] = np.array([np.sum((t0 < x) & (t0 >= x - 60)) for x in t0])
    init = lm[k] - lm[base]
    for h in (0.15, 1, 3, 10):
        out[f"per{h:g}"] = (_at(t, lm, t0 + h) - lm[base]) / init
    out["imp3"] = s * (_at(t, lm, t0 + 3) - lm[base]) * e["delta"]
    o = np.argsort(ev["t"], kind="stable")
    et, lag = ev["t"][o], (ev["t"] - ev["ts"])[o]
    pl = []
    for x in t0:
        a, b = np.searchsorted(et, [x - 1, x + 1])
        pl.append(np.nanmedian(lag[a:b]) if b > a else np.nan)
    out["lag_pmfeed"] = np.array(pl)
    gap = []
    for x in t0:  # Polymarket silence before the event (recorder gap guard)
        a = np.searchsorted(et, x) - 1
        gap.append(x - et[a] if a >= 0 else np.inf)
    out["pm_silence"] = np.array(gap)
    return out
