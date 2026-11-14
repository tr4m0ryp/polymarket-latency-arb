"""A cap set and its float-vector encoding for the kernel.

size_mode: 0 = fixed shares, 1 = fraction of equity per order (stake = f x E), 2 = fractional
Kelly on v1's predicted value e (stake = c x e / (1 - p) x E). Shares are floored, capped at
max_sh, raised to the venue's $1 minimum like the bot, and shrunk to fit the per-market room,
the open-exposure room and the cash (fit = 1); below 5 sh or $1 the order is skipped.
Equity E = cash + cost basis of positions not yet paid out (read at each order)."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

INF = 1e18
SIDES = ("any side", "1 direction", "per-side cap", "hedge only")


@dataclass(frozen=True)
class Caps:
    size_mode: int = 0
    size: float = 60.0
    max_sh: float = 500.0
    market_frac: float = INF      # per-market committed cost + fee <= x E
    open_frac: float = INF        # all open positions + orders in flight <= x E
    side_policy: int = 0          # 0 none, 1 one direction, 2 per-side fill cap, 3 hedge only
    max_fills: float = INF        # known fills per market
    dd_stop: float = INF          # pause the rest of the day below (1 - y) x day's peak equity
    min_edge: float = 0.0         # model score >= tau + min_edge
    fit: int = 1                  # shrink to the room left (0: reject, as the uncapped live bot)
    redeem_s: float = 120.0       # payout reaches the cash this long after the market ends
    floor: float = INF            # halt for good below x the all-time peak equity (amendment 2)

    def label(self) -> str:
        sz = {0: f"{self.size:g} sh", 1: f"{self.size:.0%} E", 2: f"Kelly x{self.size:g}"}[self.size_mode]
        f = lambda v, p: "-" if v >= INF / 2 else (f"{v:.0%}" if p else f"{v:g}")
        return (f"{sz} | mkt {f(self.market_frac, 1)} | open {f(self.open_frac, 1)} | "
                f"{SIDES[self.side_policy]} | fills {f(self.max_fills, 0)} | "
                f"dd {f(self.dd_stop, 1)} | edge +{self.min_edge * 100:g}c"
                + ("" if self.floor >= INF / 2 else f" | floor {self.floor:.0%}"))

    def dict(self) -> dict:
        return asdict(self)


def encode(c: Caps) -> np.ndarray:
    return np.array([c.size_mode, c.size, c.max_sh, c.market_frac, c.open_frac, c.side_policy, c.max_fills,
                     c.dd_stop, c.min_edge, c.fit, c.redeem_s, c.floor], np.float64)
