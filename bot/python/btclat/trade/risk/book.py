"""Risk state of one UTC day: positions, orders in flight, sends per hour, realised and
marked PnL, the day lock. Every change is appended to `<state>/ledger-<day>.jsonl` and replayed
on start, so a restart the same day sees the same exposure, PnL and order count.

`check(intent)` returns the first cap an order would break (or None); `breach()` trips the
loss cap: it writes `<state>/lock-<day>` and the day cannot be restarted (gate/preflight.py)."""
from __future__ import annotations

import json
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from .limits import VENUE_MIN_NOTIONAL, VENUE_MIN_SHARES, Limits, fee


def utc_day(t: float) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(t))


def lock_path(state: Path, day: str) -> Path:
    return Path(state) / f"lock-{day}"


@dataclass
class Intent:
    arm: str
    slug: str
    token: str
    up: bool
    price: float
    size: float
    end: float

    @property
    def notional(self) -> float:
        return self.price * self.size

    @property
    def worst(self) -> float:
        """Most this order can lose: notional plus taker fee."""
        return self.notional + fee(self.price, self.size)


@dataclass
class Pos:
    slug: str
    up: bool
    end: float
    sh: float = 0.0
    cost: float = 0.0
    fee: float = 0.0
    marks: list = field(default_factory=list)


class RiskBook:
    def __init__(self, limits: Limits, state: Path, now: float | None = None):
        self.limits = limits.checked()
        self.state = Path(state)
        self.state.mkdir(parents=True, exist_ok=True)
        self.day = utc_day(time.time() if now is None else now)
        self.pos: dict[tuple, Pos] = {}
        self.inflight: dict[str, float] = {}
        self.sends: deque = deque()
        self.realised = 0.0
        self.balance: float | None = None
        self.mark: dict[str, float] = {}      # token -> its mid (our book)
        self.stop_reason: str | None = None
        self._replay()

    # persistence -------------------------------------------------------------------------
    @property
    def ledger(self) -> Path:
        return self.state / f"ledger-{self.day}.jsonl"

    def _log(self, **row) -> None:
        with open(self.ledger, "a") as fh:
            fh.write(json.dumps(row) + "\n")

    def _replay(self) -> None:
        if not self.ledger.exists():
            return
        for line in self.ledger.read_text().splitlines():
            r = json.loads(line)
            if r["k"] == "send":
                self.sends.append(r["t"])
            elif r["k"] in ("fill", "carry"):
                self._add(r["slug"], r["token"], r["up"], r["end"], r["sh"], r["cost"], r["fee"])
            elif r["k"] == "resolve":
                self._resolve(r["slug"], r["outcome"])

    def roll(self, now: float) -> bool:
        """New UTC day: fresh ledger, open positions carried, realised PnL and counts reset."""
        day = utc_day(now)
        if day == self.day:
            return False
        self.day, self.realised = day, 0.0
        for (slug, token), p in self.pos.items():
            self._log(k="carry", slug=slug, token=token, up=p.up, end=p.end, sh=p.sh, cost=p.cost, fee=p.fee)
        return True

    # state changes -----------------------------------------------------------------------
    def _add(self, slug, token, up, end, sh, cost, fee_) -> None:
        p = self.pos.setdefault((slug, token), Pos(slug, up, end))
        p.sh, p.cost, p.fee = p.sh + sh, p.cost + cost, p.fee + fee_

    def _resolve(self, slug: str, outcome: float) -> None:
        for key in [k for k in self.pos if k[0] == slug]:
            p = self.pos.pop(key)
            won = outcome if p.up else 1 - outcome
            self.realised += p.sh * won - p.cost - p.fee

    def reserve(self, oid: str, it: Intent, t: float) -> None:
        self.inflight[oid] = it.worst
        self.sends.append(t)
        self._log(k="send", t=t, oid=oid)

    def release(self, oid: str) -> None:
        self.inflight.pop(oid, None)

    def fill(self, it: Intent, sh: float, cost: float, fee_: float) -> None:
        if sh <= 0:
            return
        self._add(it.slug, it.token, it.up, it.end, sh, cost, fee_)
        if self.balance is not None:            # until the next venue balance read
            self.balance -= cost + fee_
        self._log(k="fill", slug=it.slug, token=it.token, up=it.up, end=it.end, sh=sh, cost=cost, fee=fee_)

    def resolve(self, slug: str, outcome: float) -> None:
        if any(k[0] == slug for k in self.pos):
            self._resolve(slug, outcome)
            self._log(k="resolve", slug=slug, outcome=outcome)

    # readings ----------------------------------------------------------------------------
    def exposure(self) -> float:
        return sum(p.cost + p.fee for p in self.pos.values()) + sum(self.inflight.values())

    def marked(self) -> float:
        """Open positions at our book's mid (at cost while no mid is known)."""
        out = 0.0
        for (slug, token), p in self.pos.items():
            m = self.mark.get(token)
            out += (p.sh * m if m is not None and m == m else p.cost) - p.cost - p.fee
        return out

    def pnl(self) -> float:
        return self.realised + self.marked()

    def orders_last_hour(self, now: float) -> int:
        while self.sends and self.sends[0] <= now - 3600:
            self.sends.popleft()
        return len(self.sends)

    def locked(self) -> bool:
        return lock_path(self.state, self.day).exists()

    def breach(self) -> bool:
        """Loss cap reached: lock the day (once) and report True."""
        if self.pnl() > -self.limits.loss_cap:
            return False
        lp = lock_path(self.state, self.day)
        if not lp.exists():
            lp.write_text(json.dumps({"pnl": self.pnl(), "realised": self.realised, "t": time.time()}))
        self.stop_reason = f"loss cap: pnl {self.pnl():.2f} <= -{self.limits.loss_cap}"
        return True

    def check(self, it: Intent, now: float) -> str | None:
        """First cap this order breaks, or None if it may be sent."""
        L = self.limits
        if self.stop_reason:
            return "stopped"
        if self.locked():
            return "day_locked"
        if it.size > L.max_shares + 1e-9:
            return "max_shares"
        if it.notional > L.max_notional + 1e-9:
            return "max_notional"
        if it.size < VENUE_MIN_SHARES - 1e-9:
            return "below_venue_min_shares"
        if it.notional < VENUE_MIN_NOTIONAL - 1e-9:
            return "below_venue_min_notional"
        if self.exposure() + it.worst > L.max_exposure + 1e-9:
            return "max_exposure"
        if self.pnl() - it.worst <= -L.loss_cap:
            return "loss_headroom"
        if self.orders_last_hour(now) >= L.max_orders_hour:
            return "max_orders_hour"
        if self.balance is not None and self.balance - sum(self.inflight.values()) < it.worst:
            return "balance"
        return None
