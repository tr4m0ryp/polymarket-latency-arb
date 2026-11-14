"""Read-only paper-trading bot for the BTC 5m up/down markets.

Runs the two pre-registered arms (predictive taker `vt_v1_m0.03_any`, predictive veto
`vt_v1_m0.02_trigger`, data/out/predict/prereg2.json) and the micf / theirs_micro baselines
on live Binance + Polymarket feeds, and logs every order it WOULD send with a paper fill
measured on the live venue book. Nothing is ever sent: no keys, no signing, no order
client (guard.py blocks those imports).

Layout: feeds/ (websockets, parsing, clock), state/ (incremental Binance and Polymarket
state), features/ (one decision row = the offline table's columns), model/ (frozen value
model, hash-checked, C trees), arms/ (research rules on one row), execution/ (venue
rollback and paper fills), engine/ (the per-event loop), replay/ (recorded hours, parity
test), report/ (run summary vs the replay simulator), deploy/ (Dublin kit).

    nice -n 10 python3 -m btclat.paper --hours 0.5           # live
    nice -n 10 python3 -m btclat.paper.replay.run --hours H0,H1
    nice -n 10 python3 -m btclat.paper.replay.parity
    python3 -m btclat.paper.report --run <run> [--raw]"""
from .arms.defs import ARM_NAMES, MICRO_ARMS, VT_ARMS
from .engine.core import Engine
from .engine.world import World
from .model.load import ValueModel

__all__ = ["ARM_NAMES", "MICRO_ARMS", "VT_ARMS", "Engine", "ValueModel", "World"]
