"""Bankroll simulator for the taker + model veto arm at i = 0 (reports/bankroll-caps.md).

Replays the veto arm's own orders (v1 frozen and the hold-aware winner v1h_G_h250x_L0) on the
venue-clock book of the 48 h Dublin paper run under the measured taker hold, with real cash
flow: cost + fee leave the cash at the fill, $1 per winning share comes back at resolution
plus a redeem delay, an order the cash (minus orders in flight) cannot cover is rejected.
Then searches pre-registered cap sets (sizing, per-market and open-exposure fractions, one side
per market, fills per market, drawdown stop, minimum edge) for median 24 h log growth from a
$100 start under ruin constraints. Read-only research: no orders.

    PYTHONPATH=. python3 -m research.bankroll.stream.run --workers 6   # order streams (~20 min)
    PYTHONPATH=. python3 -m research.bankroll.search.prereg            # freeze grid + objective
    PYTHONPATH=. python3 -m research.bankroll.search.screen            # selection hours, v1
    PYTHONPATH=. python3 -m research.bankroll.search.final             # finalists, test hours, ablation"""
from research.vetohold import OUT as VOUT, SPLIT  # noqa: F401  (sets the paper-run env first)

OUT = VOUT.parent / "bankroll"
ARMS = ("v1_frozen", "G_h250+x")
SCENS = ("old", "new", "fast50")   # 2026-10-13 hold, 2026-10-14 bot-run hold, 50 ms what-if
K = 16                             # hold draws stored per order
START = 100.0
