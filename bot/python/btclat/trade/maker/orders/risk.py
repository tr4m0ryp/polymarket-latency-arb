"""Maker caps on top of the shared risk book (risk/book.py: positions, day loss cap and lock,
ledger). Every resting quote counts as if it filled in full:

- market cap: this market's fills (cost) + its resting notional + the new quote <= $10;
- max open: all unresolved fills (cost) + all resting notional + the new quote <= $25;
- loss headroom: marked PnL - all resting notional - the new quote > -day loss cap;
- inserts per rolling hour (runaway guard), the pUSD balance, 5 shares, price in [0.01, 0.99].
Limits are module constants (risk/limits.py); the CLI may only lower them. Cancels are never
blocked. A dry run (--dry) applies none of the money caps (MONEY: day lock, market cap, max open,
loss headroom, balance) nor the loss-cap stop: the quote goes to the simulated venue and the cap
is logged as a would-skip (would-stop); the other guards apply as live."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, fields, replace

from ...risk.limits import (HARD_MAKER_FANOUT, HARD_MAKER_INSERTS_HOUR, HARD_MAKER_MARKET_CAP,
                            HARD_MAKER_MAX_OPEN, VENUE_MIN_SHARES, LimitError)

MONEY = ("day_locked", "market_cap", "max_open", "loss_headroom", "balance")   # dry: logged, not applied
HARD = {"max_open": HARD_MAKER_MAX_OPEN, "market_cap": HARD_MAKER_MARKET_CAP,
        "inserts_hour": HARD_MAKER_INSERTS_HOUR, "fanout": HARD_MAKER_FANOUT}


@dataclass(frozen=True)
class MakerLimits:
    max_open: float = HARD_MAKER_MAX_OPEN
    market_cap: float = HARD_MAKER_MARKET_CAP
    inserts_hour: int = HARD_MAKER_INSERTS_HOUR
    fanout: int = HARD_MAKER_FANOUT

    def lowered(self, **kw) -> "MakerLimits":
        return replace(self, **{k: v for k, v in kw.items() if v is not None}).checked()

    def checked(self) -> "MakerLimits":
        for f in fields(self):
            v = getattr(self, f.name)
            if not (v == v) or v <= 0 or v > HARD[f.name]:
                raise LimitError(f"maker limit {f.name}={v} is looser than the hard limit {HARD[f.name]}; refusing")
        return self


class MakerRisk:
    def __init__(self, book, limits: MakerLimits | None = None, dry: bool = False):
        self.book = book
        self.limits = (limits or MakerLimits()).checked()
        self.inserts: deque = deque()
        self.dry, self.would_stop = dry, False

    def inserts_last_hour(self, now: float) -> int:
        while self.inserts and self.inserts[0] <= now - 3600:
            self.inserts.popleft()
        return len(self.inserts)

    def market_cost(self, slug: str) -> float:
        return sum(p.cost + p.fee for (s, _), p in self.book.pos.items() if s == slug)

    def _breaks(self, o, working, now: float):
        """Every cap the new quote `o` breaks, in order (lazy). `working`: our other orders that may
        still fill (resting, or off the book and not settled: Working.at_risk)."""
        b, L = self.book, self.limits
        if b.stop_reason:
            yield "stopped"
        if b.locked():
            yield "day_locked"
        if abs(o.size - VENUE_MIN_SHARES) > 1e-9 or o.size > b.limits.max_shares + 1e-9:
            yield "size"
        if not 0.01 - 1e-9 <= o.price <= 0.99 + 1e-9:
            yield "price"
        rest = sum(w.at_risk for w in working)
        rest_m = sum(w.at_risk for w in working if w.slug == o.slug)
        new = o.price * o.size
        if self.market_cost(o.slug) + rest_m + new > L.market_cap + 1e-9:
            yield "market_cap"
        if b.exposure() + rest + new > L.max_open + 1e-9:
            yield "max_open"
        if b.pnl() - rest - new <= -b.limits.loss_cap:
            yield "loss_headroom"
        if self.inserts_last_hour(now) >= L.inserts_hour:
            yield "inserts_hour"
        if b.balance is not None and b.balance - rest < new:
            yield "balance"

    def check(self, o, working, now: float) -> str | None:
        """First cap the new quote `o` breaks, or None."""
        return next(self._breaks(o, working, now), None)

    def gate(self, o, working, now: float) -> tuple[str | None, str | None]:
        """(cap that skips the quote, money cap a dry run only logs as a would-skip). Live: check()."""
        if not self.dry:
            return self.check(o, working, now), None
        would = None
        for why in self._breaks(o, working, now):
            if why not in MONEY:
                return why, would
            would = would or why
        return None, would

    def dry_watch(self, session, mgr, now: float, note) -> str | None:
        """micro/run.py `watch` for a dry run: the loss cap never trips (no lock), it logs a would-stop."""
        if session.killed():
            return f"kill file {session.kill}"
        b = self.book
        b.roll(now)
        if not self.would_stop and b.pnl() <= -b.limits.loss_cap:
            self.would_stop = True
            note("would_stop", reason=f"loss cap: pnl {b.pnl():.2f} <= -{b.limits.loss_cap} (dry: not applied)")
        return mgr.stop_reason

    def sent(self, now: float) -> None:
        self.inserts.append(now)

    def fill(self, o, sh: float, cost: float) -> None:
        self.book.fill(o.intent(), sh, cost, 0.0)       # makers pay no fee
