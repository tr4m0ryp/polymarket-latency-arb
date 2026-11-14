"""The quote rule the maker runs (`--rule`, `--hyst`):

- frozen (default): arm.py, the frozen value maker `vm_fair0.03_p-0.03`, unchanged; --hyst is
  refused, so the frozen arm stays frozen;
- inside: research/predict/sim/rules.py `vinside` itself (the pre-registered inside gate,
  reports/fill-improve.md idea 1): vmaker at fair -/+ 0.04, pull -0.02, a side kept only when its
  tick is strictly inside the spread. With h > 0, `hyst_step` per market and side: an idle side
  enters only at pred < pull - h and leaves at pred >= pull. vinside runs on ONE row with h = 0
  (its vectorized hysteresis needs a market's whole sequence); the state lives here, fresh for
  each new market slug.

An inside quote also carries, for arm.cause: raw_<side> (vmaker's tick before the inside gate),
in_<side> (the inside tick before hysteresis), the rule and h."""
from __future__ import annotations

import inspect

import numpy as np

from btclat.paper.arms.frame import Frame
from research.predict.sim import rules as vrules

from ..gate.preflight import Refused
from . import arm

_SIG = inspect.signature(vrules.vinside).parameters
INSIDE = {"half": _SIG["half"].default, "pull": _SIG["pull"].default}
KEEP = 8                  # markets whose hysteresis state is kept (one is live at a time)
assert INSIDE == {"half": 0.04, "pull": -0.02} and arm.MODEL == "v1_L50"


class Frozen:
    kind, h = "frozen", 0.0
    name, params = arm.NAME, arm.PARAMS

    def quote(self, r: dict, pu: float, pdn: float, slug: str = "") -> dict:
        return arm.quote(r, pu, pdn)


class Inside:
    kind = "inside"

    def __init__(self, h: float = 0.0):
        self.h = float(h)
        self.params = dict(INSIDE, h=self.h)
        self.name = f"vi_fair{INSIDE['half']}_p{INSIDE['pull']}" + (f"_h{self.h:g}" if self.h > 0 else "")
        self.on: dict[str, dict] = {}

    def state(self, slug: str) -> dict:
        """Hysteresis state of one market: side -> live? (fresh for a new slug)."""
        st = self.on.get(slug)
        if st is None:
            while len(self.on) >= KEEP:
                del self.on[next(iter(self.on))]
            st = self.on[slug] = dict.fromkeys(arm.SIDES, False)
        return st

    def quote(self, r: dict, pu: float, pdn: float, slug: str = "") -> dict:
        """Target ticks (0 = no quote), pull flags and the gate trail of one decision row."""
        f, u, d = Frame({k: r[k] for k in arm.COLS}), np.array([pu]), np.array([pdn])
        _, rb, ra = vrules.vmaker(f, u, d, **INSIDE)
        _, b, a = vrules.vinside(f, u, d, h=0.0, **INSIDE)
        pull = INSIDE["pull"]
        q = {"bid": int(b[0]), "ask": int(a[0]),
             "pull_bid": not pdn < pull,     # the Up bid is run over when Down gains
             "pull_ask": not pu < pull,      # the Up ask is lifted when Up gains
             "raw_bid": int(rb[0]), "raw_ask": int(ra[0]), "in_bid": int(b[0]), "in_ask": int(a[0]),
             "rule": self.kind, "h": self.h}
        if self.h > 0:
            st = self.state(slug)
            for side, p in (("bid", pdn), ("ask", pu)):
                st[side], q[side] = vrules.hyst_step(st[side], q[side], float(p), pull, self.h)
        return q


def of(rule: str = "frozen", h: float = 0.0):
    """The rule of `--rule` / `--hyst`, or Refused."""
    h = float(h)
    if not (0.0 <= h < 1.0):
        raise Refused(f"refusing: --hyst {h} must be in [0, 1)")
    if rule == "frozen":
        if h > 0:
            raise Refused("refusing: --hyst applies to --rule inside only; the frozen arm stays frozen")
        return Frozen()
    if rule == "inside":
        return Inside(h)
    raise Refused(f"refusing: unknown maker rule {rule!r}")
