"""Price signals per venue/feed, as local-receipt series (mono ns, price).

A Binance signal fans in every connection carrying it (earliest arrival per id), which is what
an optimised client would see; the BASE_* signals are single connections as the bot reads them
today (spot combined trade+bookTicker, perp /public combined), price = mid or last trade."""
from __future__ import annotations

import numpy as np

from parse import load

SPOT_BOOK = ["spot_comb_a", "spot_comb_b", "spot_book_a", "spot_book_b", "spot_vision", "spot_443"]
SPOT_TRADE = ["spot_comb_a", "spot_comb_b", "spot_trade_a", "spot_trade_b", "spot_vision",
              "spot_443"]
PERP = ["perp_pub_a", "perp_pub_b", "perp_book"]

SIGNALS: dict[str, tuple[list[str], tuple[int, ...]]] = {
    "bn_spot_book": (SPOT_BOOK, (1,)),
    "bn_spot_trade": (SPOT_TRADE, (0,)),
    "bn_perp_book": (PERP, (1,)),
    "bn_perp_trade": (PERP[:2], (0,)),
    "cb_book": (["coinbase"], (1,)),
    "cb_trade": (["coinbase"], (0,)),
    "bybit_spot_book": (["bybit_spot"], (1,)),
    "bybit_spot_trade": (["bybit_spot"], (0,)),
    "bybit_lin_book": (["bybit_lin"], (1,)),
    "bybit_lin_trade": (["bybit_lin"], (0,)),
    "okx_spot_book": (["okx_spot"], (1,)),
    "okx_spot_trade": (["okx_spot"], (0,)),
    "okx_swap_book": (["okx_swap"], (1,)),
    "okx_swap_trade": (["okx_swap"], (0,)),
    "deribit_book": (["deribit"], (1,)),
    "deribit_trade": (["deribit"], (0,)),
    "bitstamp_book": (["bitstamp"], (1,)),
    "bitstamp_trade": (["bitstamp"], (0,)),
    "kraken_spot_book": (["kraken_spot"], (1,)),
    "kraken_spot_trade": (["kraken_spot"], (0,)),
    "kraken_fut_book": (["kraken_fut"], (1,)),
    "kraken_fut_trade": (["kraken_fut"], (0,)),
    "bullish_book": (["bullish"], (1,)),
    "lmax_book": (["lmax"], (1,)),
    "BASE_spot_comb_a": (["spot_comb_a"], (0, 1)),
    "BASE_perp_pub_a": (["perp_pub_a"], (0, 1)),
    "BASE_spot_fan": (["spot_comb_a", "spot_comb_b"], (0, 1)),
    "BASE_perp_fan": (["perp_pub_a", "perp_pub_b"], (0, 1)),
}
# Onset of a composite = earliest onset of its parts in the same move (prices never mixed:
# the perp-spot basis would read as a jump).
COMPOSITES = {
    "bn_best": ["bn_spot_book", "bn_spot_trade", "bn_perp_book", "bn_perp_trade"],
    "BASE_bot_fanin": ["BASE_spot_fan", "BASE_perp_fan"],
    "fused_deribit_binance": ["deribit_book", "bn_spot_book", "bn_spot_trade", "bn_perp_book",
                              "bn_perp_trade"],
}


VTS: dict[str, np.ndarray] = {}  # per signal: venue stamp (match time if given, else push), us


def build(run, name: str) -> tuple[np.ndarray, np.ndarray]:
    streams, kinds = SIGNALS[name]
    t_l, p_l, k_l, v_l = [], [], [], []
    for s in streams:
        d = load(run, s)
        m = np.isin(d["kind"], kinds)
        t_l.append(d["mono"][m])
        p_l.append(d["px"][m])
        v_l.append(np.where(d["vts2"][m] > 0, d["vts2"][m], d["vts"][m]))
        # key per (kind, id); the perp and spot id spaces never meet in one fan-in group key,
        # so tag them by venue to keep them apart
        tag = (2 if s.startswith("perp") else 0) + d["kind"][m]
        k_l.append(np.where(d["key"][m] >= 0, d["key"][m] * 4 + tag, -1))
    t, p, k, v = (np.concatenate(x) if x else np.array([]) for x in (t_l, p_l, k_l, v_l))
    o = np.argsort(t, kind="stable")
    t, p, k, v = t[o], p[o], k[o], v[o]
    if len(streams) > 1:  # keep the first arrival of each id
        _, first = np.unique(k, return_index=True)
        keep = np.zeros(len(k), bool)
        keep[first] = True
        keep |= k < 0
        t, p, v = t[keep], p[keep], v[keep]
    ok = np.isfinite(p) & (p > 0)
    VTS[name] = (t[ok], v[ok])
    return t[ok], p[ok]


def all_signals(run, window: tuple[int, int] | None = None) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """window: (mono_from, mono_to) ns; signals are cut to it (all onsets fall inside)."""
    have = {p.stem for p in (run / "parsed").glob("*.npz") if p.stat().st_size > 400}
    out = {n: build(run, n) for n, (streams, _) in SIGNALS.items() if set(streams) <= have}
    if window:
        out = {n: (t[(t >= window[0]) & (t < window[1])], p[(t >= window[0]) & (t < window[1])])
               for n, (t, p) in out.items()}
    return {n: v for n, v in out.items() if len(v[0]) > 100}
