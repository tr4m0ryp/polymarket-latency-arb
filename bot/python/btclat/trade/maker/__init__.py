"""Maker mode: the simulator's frozen value maker `vm_fair0.03_p-0.03` quoted for real (or dry)
on the BTC 5m up/down markets.

Taker orders are held ~250 ms by the venue and adversely selected live (14% fills, -4.1 c/$);
resting post-only quotes are not held (insert ack ~56 ms) and the maker simulates at +5.1 c/$
at L = 50 ms (reports/predict.md, "Taker hold 270 ms vs 150 ms"). Its edge decays with cancel
latency, so every insert and cancel goes out on 2-3 warm connections at once (the venue
dedupes one signed payload; first ack wins).

Layout: arm.py (the research rule on one live row), decide.py (paper engine + decision
instants, model v1_L50), orders/ (slots, order manager, maker risk caps), ops/ (live hedged
sends, dry simulated acks), fills/ (trade tape parsing, inferred fills by the simulator's
maker rule, real fills by order lookup), log.py (streams, 10 s markouts), run.py (loop).

    python3 -m btclat.trade maker --dry [--hours H] [--record]     # no orders, no keys
    python3 -m btclat.trade maker --i-approve [--hours H]          # real orders
    python3 -m btclat.trade.report --run <run>"""
from .arm import MODEL, NAME, PARAMS

__all__ = ["MODEL", "NAME", "PARAMS"]
