"""Venue rollback equals the research grid replay; paper fills follow the taker simulator."""
import numpy as np

from btclat.paper.execution import venue
from btclat.paper.state.pm import PMBook
from research.strategy import fee
from research.strategy.sim.grid import Book

START = 1_000_000.0


def _random_book(seed=0, n=400):
    rng = np.random.default_rng(seed)
    pm, ev = PMBook(keep_log=60.0), {"t": [], "ts": [], "side": [], "tick": [], "size": []}
    ts = START
    for _ in range(n):
        ts += rng.exponential(0.01)
        side, k = int(rng.choice([1, -1])), int(rng.integers(30, 60))
        s = float(rng.choice([0.0, 10.0, 25.0, 80.0]))
        pm.apply(ts + 0.02, ts, False, [(side, k, s)])
        for key, v in zip(ev, (ts + 0.02, ts, side, k, s)):
            ev[key].append(v)
    return pm, {k: np.array(v, dtype=float) for k, v in ev.items()}, ts


def test_rows_match_research_grid():
    pm, ev, last = _random_book()
    book = Book(ev, START - 2, last + 1)
    t0 = START - 2
    for x in np.linspace(last - 1.5, last - 0.05, 40):
        g = venue.g_ceil(x, t0)
        got = venue.rows_at(pm, t0, g, g + 2)
        assert np.array_equal(got, book.size[g:g + 3])


def test_fill_walks_levels_with_fee():
    pm = PMBook()
    pm.apply(START, START, True, [(1, 38, 30.0), (-1, 40, 40.0), (-1, 41, 50.0)])
    pm.apply(START + 0.3, START + 0.3, False, [(-1, 40, 0.0)])
    f, new, levels = venue.fill(pm, START - 2, START + 0.05, 1, 60.0, 0.42, 0.0, 0.01, 0.15, [])
    assert f["shares"] == 60 and abs(f["cost"] - (40 * 0.40 + 20 * 0.41)) < 1e-9
    assert abs(f["fee"] - (40 * fee(0.40) + 20 * fee(0.41))) < 1e-9
    f2, _, _ = venue.fill(pm, START - 2, START + 0.2, 1, 60.0, 0.42, 0.0, 0.01, 0.15, [])
    assert f2["shares"] == 50 and abs(f2["px"] - 0.41) < 1e-9
    f3, _, _ = venue.fill(pm, START - 2, START + 0.06, 1, 60.0, 0.42, 0.0, 0.01, 0.15, new)
    assert f3["shares"] == 30   # own earlier takes are remembered (taker.MEMORY)
