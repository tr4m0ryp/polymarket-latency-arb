"""Hard risk limits of the live test. They are module constants, not config defaults: the
CLI may only LOWER a limit (`Limits.lowered`), never raise one, and `RiskBook` re-checks
every value against these constants when it is built, so an edited Limits object is refused.

Venue rules (BTC up/down 5m, verified 2026-10-12 on GET /clob-markets: mos 5, mts 0.01,
fee r 0.07 e 1 taker-only, itode true): 5-share minimum, 0.01 tick. The $1 minimum for a
marketable BUY is reported by third parties, not by Polymarket's docs: kept as a skip rule
(`below_venue_min_notional`) so the first live day does not spend its order budget on rejects."""
from __future__ import annotations

from dataclasses import dataclass, fields, replace

HARD_MAX_SHARES = 5.0            # per order (= venue minimum: every order is exactly 5)
HARD_MAX_NOTIONAL = 3.0          # $ per order, price x shares at the limit
HARD_MAX_EXPOSURE = 15.0         # $ open: cost + fee of unresolved positions + orders in flight
HARD_LOSS_CAP = 10.0             # $ per UTC day, realised + marked; then stop and lock the day
HARD_MAX_ORDERS_HOUR = 40        # sent micro orders in any rolling 3600 s
HARD_MAX_PROBE_HOUR = 120        # probe orders in any rolling 3600 s (1 per 30 s)
HARD_MIN_PROBE_EVERY = 5.0       # s between probe orders, floor
HARD_HOLD_BUDGET = 5.0           # $ spent (fills + fees) per hold-test run (hold/)
HARD_HOLD_MARKETABLE = 40        # marketable orders per hold-test run (unfillable controls not counted)
HARD_HOLD_CYCLES = 40            # hold-test cycles per run
HARD_HOLD_MAX_ASK = 0.30         # hold test buys at most at this ask: 5 sh <= $1.50
HARD_HOLD_MAX_NOTIONAL = 1.60    # $ per hold-test marketable order (sized just over the $1 minimum)
HARD_DUP_REPS = 10               # duplicate-send repetitions per copy count (unfillable orders)
HARD_MAKER_MAX_OPEN = 25.0        # $ maker: unresolved fills (cost) + every resting quote's notional
HARD_MAKER_MARKET_CAP = 10.0      # $ maker per market: its fills (cost) + its resting notional
HARD_MAKER_INSERTS_HOUR = 3600    # maker quote inserts per rolling 3600 s (dry: 1166/h on one market; pull flicker)
HARD_MAKER_FANOUT = 3             # copies per maker insert / cancel (venue dedupes one signed payload)
VENUE_MIN_SHARES = 5.0
VENUE_MIN_NOTIONAL = 1.0         # $ marketable BUY (third-party figure, see above; the hold test sizes over it)
TICK = 0.01
FEE_RATE = 0.07                  # taker fee per share = FEE_RATE * p * (1 - p), our 0% tier

# limit name -> (hard value, True if a larger value is looser)
HARD = {"max_shares": (HARD_MAX_SHARES, True), "max_notional": (HARD_MAX_NOTIONAL, True),
        "max_exposure": (HARD_MAX_EXPOSURE, True), "loss_cap": (HARD_LOSS_CAP, True),
        "max_orders_hour": (HARD_MAX_ORDERS_HOUR, True), "max_probe_hour": (HARD_MAX_PROBE_HOUR, True),
        "min_probe_every": (HARD_MIN_PROBE_EVERY, False)}


class LimitError(SystemExit):
    pass


def fee(p: float, shares: float) -> float:
    return FEE_RATE * p * (1 - p) * shares


@dataclass(frozen=True)
class Limits:
    max_shares: float = HARD_MAX_SHARES
    max_notional: float = HARD_MAX_NOTIONAL
    max_exposure: float = HARD_MAX_EXPOSURE
    loss_cap: float = HARD_LOSS_CAP
    max_orders_hour: int = HARD_MAX_ORDERS_HOUR
    max_probe_hour: int = HARD_MAX_PROBE_HOUR
    min_probe_every: float = HARD_MIN_PROBE_EVERY

    def lowered(self, **kw) -> "Limits":
        """A copy with some limits tightened. Loosening one past its hard value is refused."""
        kw = {k: v for k, v in kw.items() if v is not None}
        out = replace(self, **kw)
        out.checked()
        return out

    def checked(self) -> "Limits":
        for f in fields(self):
            hard, up_is_loose = HARD[f.name]
            v = getattr(self, f.name)
            if not (v == v) or v <= 0 or (v > hard if up_is_loose else v < hard):
                raise LimitError(f"limit {f.name}={v} is looser than the hard limit {hard}; refusing")
        return self
