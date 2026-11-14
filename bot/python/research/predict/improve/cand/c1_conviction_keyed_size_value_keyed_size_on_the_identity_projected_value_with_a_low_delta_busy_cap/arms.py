"""C1 arms: the frozen firing rules with a conviction-keyed order size (harness plug-ins).

Firing is exactly the deployed rule (research/predict/sim/rules.vtaker: same margin, require,
refractory, limit = seen ask + 2 c); only `shares` changes:

    shares = clip(K * max(k, 0), lo, hi)       k = pred of the fired side   (key "pred")
                                               k = v* of the fired side     (key "vstar", value.py)
                                               k = min(pred, v*) of the fired side (key "vmin":
                                                   only a positive symmetric residual cuts size)
    cap_delta: shares = 60 where the settlement delta < cap_delta c/bp (busy-hour cap)
    K = 0, lo = hi = s: flat s shares (the size control: upsizing without conviction)

    python3 -m research.predict.improve.harness --arm <this module>:size_taker --out ..."""
from __future__ import annotations

import numpy as np

from ....sim import rules
from ...harness.api import Arm
from .value import delta, vstar

BASE_SH = 60.0


def fired_rows(t_tab: np.ndarray, d: dict, pu, pd_) -> np.ndarray:
    """Row index in the table of every fired decision (times may repeat in the table: the
    row whose max prediction equals the decision's edge is taken)."""
    j0 = np.searchsorted(t_tab, d["t"], "left")
    j1 = np.searchsorted(t_tab, d["t"], "right")
    j = j0.copy()
    for n in np.flatnonzero(j1 - j0 > 1):
        cand = np.arange(j0[n], j1[n])
        hit = cand[np.isclose(np.maximum(pu[cand], pd_[cand]), d["edge"][n])]
        j[n] = hit[0] if len(hit) else j0[n]
    assert np.allclose(np.maximum(pu[j], pd_[j]), d["edge"]), "fired rows do not match the table"
    return j


class _Size:
    def __init__(self, margin, require, K, lo, hi, key, cap_delta=None, lo_by_L=None, model="v1"):
        assert key in ("pred", "vstar", "vmin")
        self.margin, self.require, self.K, self.lo, self.hi = margin, require, K, lo, hi
        self.key, self.cap_delta, self.lo_by_L, self.model = key, cap_delta, lo_by_L or {}, model

    def __call__(self, mk, L):
        pu, pd_ = mk.pred(self.model, L)
        tab = mk.tab
        d = rules.vtaker(tab, pu, pd_, margin=self.margin, require=self.require)
        if not len(d["t"]):
            return d
        j = fired_rows(tab["t"].to_numpy(), d, pu, pd_)
        if self.key == "pred":
            k = d["edge"]
        else:
            vu, vd = vstar(tab, pu, pd_)
            k = np.where(d["side"] > 0, vu[j], vd[j])
            if self.key == "vmin":
                k = np.minimum(k, d["edge"])
        lo = self.lo_by_L.get(L, self.lo)
        sh = np.clip(self.K * np.maximum(k, 0.0), lo, self.hi)
        if self.cap_delta is not None:
            dl = delta(tab)[j]
            sh = np.where(dl < self.cap_delta, BASE_SH, sh)
        d["shares"] = np.round(sh, 2)
        return d


def _flag(f):
    f.FOLD_INVARIANT, f.CRITERION, f.SELECT_L = True, "lcb", 0
    return f


def taker_arm(K=2000, key="vstar", cap=None, lo=30, hi=200, tag=""):
    name = f"ek_{key}_{K}" + (f"_d{cap:g}" if cap is not None else "") + tag
    if K == 0:
        name = f"ek_flat_{lo:g}" + (f"_d{cap:g}" if cap is not None else "")
    return Arm(name, _Size(0.03, None, K, lo, hi, key, cap_delta=cap))


def veto_arm(K=3000, key="vstar", cap=None, lo=100, hi=300, tag="", lo40=60):
    name = f"vk_{key}_{K}" + (f"_d{cap:g}" if cap is not None else "") + tag
    if K == 0:
        name, lo40 = f"vk_flat_{lo:g}" + (f"_d{cap:g}" if cap is not None else ""), lo
    return Arm(name, _Size(0.02, "trigger", K, lo, hi, key, cap_delta=cap, lo_by_L={-40: lo40}))


@_flag
def size_taker(fold):
    """Pre-declared C1 taker family: pred-keyed, v*-keyed, v*-keyed with the delta < 8 cap."""
    return [taker_arm(2000, "pred"), taker_arm(2000, "vstar"), taker_arm(2000, "vstar", cap=8)]


@_flag
def size_veto(fold):
    """Pre-declared C1 veto family (margin 2 c, leaders' trigger required)."""
    return [veto_arm(3000, "pred"), veto_arm(3000, "vstar"), veto_arm(3000, "vstar", cap=8)]


def _taker_sweep():
    out = [taker_arm(0, "pred", lo=s, hi=s) for s in (75, 100, 150)]           # flat-size controls
    out += [taker_arm(K, "vstar") for K in (1000, 1500, 3000, 4000)]            # winner's slope K
    out += [taker_arm(3000, "vstar", hi=300, tag="_h300")]
    out += [taker_arm(K, "pred") for K in (1500, 3000)]
    out += [taker_arm(K, "vmin") for K in (2000, 3000)]                         # one-sided projection
    out += [taker_arm(2000, "vstar", cap=c) for c in (6, 10, 12)]               # busy-cap threshold
    return out


def _veto_sweep():
    out = [veto_arm(0, "pred", lo=s, hi=s) for s in (100, 150)]
    out += [veto_arm(K, "vstar") for K in (2000, 4000)]
    out += [veto_arm(3000, "vstar", lo=60, tag="_l60"), veto_arm(3000, "vstar", hi=200, tag="_h200")]
    out += [veto_arm(K, "pred") for K in (2000, 4000)]
    out += [veto_arm(3000, "vmin")]
    out += [veto_arm(3000, "vstar", cap=c) for c in (6, 10)]
    return out


@_flag
def size_sweep(fold):
    """Second round, one simulation pass: flat-size controls, the slope K, caps, the one-sided
    projection, for the taker and the veto (scored offline per family by score.py)."""
    return _taker_sweep() + _veto_sweep()


@_flag
def size_round3(fold):
    """Third round (defined after the round-2 sweep was scored on every window, labelled as
    such): slope K x busy cap for v*, the cap below 6 c/bp, pred-keyed with the cap (the v*
    delta under the cap), and flat size with the cap (the conviction delta under the cap)."""
    out = [taker_arm(K, "vstar", cap=c) for K in (3000, 4000) for c in (6, 8)]
    out += [taker_arm(3000, "vstar", cap=6, hi=300, tag="_h300"), taker_arm(2000, "vstar", cap=4)]
    out += [taker_arm(3000, "pred", cap=6), taker_arm(0, "pred", cap=6, lo=100, hi=100)]
    out += [veto_arm(4000, "vstar", cap=c) for c in (6, 8)]
    out += [veto_arm(3000, "vstar", cap=c) for c in (4, 5)]
    out += [veto_arm(3000, "pred", cap=6), veto_arm(0, "pred", cap=6, lo=100, hi=100)]
    return out


@_flag
def size_round4(fold):
    """Fourth round (after round 3, labelled): the veto winner's slope past the grid edge
    (K 5000/6000, hi 400) and cap 5 under K 4000; the busy cap on the pred-keyed taker."""
    out = [taker_arm(2000, "pred", cap=c) for c in (6, 8)] + [taker_arm(2500, "vstar", cap=6)]
    out += [veto_arm(K, "vstar", cap=6) for K in (5000, 6000)]
    out += [veto_arm(4000, "vstar", cap=6, hi=400, tag="_h400"), veto_arm(4000, "vstar", cap=5)]
    return out
