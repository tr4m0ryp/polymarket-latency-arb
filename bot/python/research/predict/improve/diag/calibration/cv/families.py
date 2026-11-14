"""Variant families for the cross-validation driver. Each family: (reference frozen arm,
list of harness Arms). A variant named exactly like the frozen rule ("m3" / "v_m2") is an
alias of the frozen reference results (not re-simulated).

taker_margin: the deployed 1 s taker (60 sh, limit seen ask + 2 c, 0.2 s refractory) with
    m<X>          static margin X c
    rm_<Q>_<B>    Q c below busy index 1.0 (ctx/load.busy), B c at or above it
    lin_<b>_<s>_<cap>  margin = min(cap, b + s * max(busy, 0)) c (continuous)
taker_slow: srm_<Q>_<B> / frm_<Q>_<B> on the hour-scale regime (ctx/slow.py, margin_of)
refit: the deployed taker rule on the adapt/ refit models at margins 2.5 / 3 / 3.5 c
taker_fb: margin set per market by the recent fill-level money gap (ctx/feedback.py)
veto_margin: the deployed trigger veto (leaders' trigger kept when p >= margin) with
    v_m<X>, v_rm_<Q>_<B> as above, and v_brefr<R>: 2 c margin, orders at busy >= 1.0 thinned
    to one per R s (the veto's busy-hour problem is its fire rate)."""
from __future__ import annotations

import numpy as np

from .....sim import rules
from ....harness.api import Arm
from ..ctx.load import busy, ctx
from ..ctx.slow import slow_index

HI = 1.0
VT_ANY, VETO = "vt_v1_m0.03_any", "vt_v1_m0.02_trigger"


SLOW_SPAN, SLOW_HI = 1800.0, 0.5


def margin_of(name: str, b: np.ndarray, slow: float = np.nan):
    """srm_Q_B: B c when the slow (previous 30 min) regime index >= 0.5, else Q c; frm_Q_B:
    B c when either the slow index >= 0.5 or the row busy index >= 1.0 (fast attack, slow
    release), else Q c. A market without a slow index keeps the row-level rule."""
    k = name.split("_")
    if k[0] in ("srm", "frm"):
        hot = np.full(len(b), bool(slow >= SLOW_HI)) if np.isfinite(slow) else b >= HI
        if k[0] == "frm":
            hot = hot | (b >= HI)
        return np.where(hot, float(k[2]), float(k[1])) / 100
    if len(k) == 1 and name.startswith("m"):
        return float(name[1:]) / 100
    if k[0] == "rm":
        return np.where(b >= HI, float(k[2]), float(k[1])) / 100
    if k[0] == "lin":
        base, s, cap = (float(x) for x in k[1:4])
        return np.minimum(cap, base + s * np.maximum(b, 0.0)) / 100
    raise ValueError(name)


def thin(d: dict, bz: np.ndarray, refr: float) -> dict:
    """Drop orders at busy >= HI that come within refr s of the previous kept order."""
    keep, last = [], -np.inf
    for j, (t, x) in enumerate(zip(d["t"], bz)):
        if x >= HI and t - last < refr:
            continue
        keep.append(j)
        last = t
    k = np.asarray(keep, dtype=np.int64)
    return {c: np.asarray(v)[k] for c, v in d.items()}


class Rule:
    def __init__(self, form: str, require=None, refr_busy: float | None = None):
        self.form, self.require, self.refr_busy = form, require, refr_busy

    def __call__(self, mk, L):
        pu, pdn = mk.pred("v1", L)
        b = busy(ctx(mk.id, len(mk.tab)))
        slow = slow_index(SLOW_SPAN).get(mk.id, np.nan)
        d = rules.vtaker(mk.tab, pu, pdn, margin=margin_of(self.form, b, slow), require=self.require)
        if self.refr_busy and len(d["t"]):
            ix = np.searchsorted(mk.tab["t"].to_numpy(), d["t"])
            d = thin(d, b[ix], self.refr_busy)
        return {k: d[k] for k in ("t", "side", "shares", "limit")}


TAKER = ["m2.5", "m3", "m3.5", "rm_2.5_3", "rm_2.5_3.5", "rm_2.5_4", "rm_2_3", "rm_2_3.5", "rm_3_3.5",
         "rm_3_4", "lin_2.5_0.5_3.5", "lin_2.5_1_4", "lin_2_1_3.5"]
VETOS = ["m1.5", "m2", "m2.5", "rm_2_3", "rm_2_4", "rm_1.5_3", "frm_2_3", "frm_1.5_2", "frm_1.5_3", "srm_2_3"]


def taker_margin():
    arms = [Arm(f, Rule(f)) for f in TAKER]
    return VT_ANY, arms, {"m3": VT_ANY}


SLOW = ["m2.5", "m3", "srm_2_3", "srm_2.5_3", "srm_2.5_3.5", "frm_2_3", "frm_2.5_3", "frm_2_3.5", "frm_2.5_3.5"]


def taker_slow():
    slow_index(SLOW_SPAN)                     # warm the cache before the worker fork
    return VT_ANY, [Arm(f, Rule(f)) for f in SLOW], {"m3": VT_ANY}


def veto_margin():
    slow_index(SLOW_SPAN)
    arms = [Arm(f"v_{f}", Rule(f, "trigger")) for f in VETOS]
    arms += [Arm(f"v_brefr{r:g}", Rule("m2", "trigger", r)) for r in (1.0, 3.0)]
    return VETO, arms, {"v_m2": VETO}


class FeedbackRule:
    """fb_<span min>_<thr c>: margin 2.5 c when the recent fill-level gap (ctx/feedback.py) is
    >= thr, 3.5 c when <= -thr, else 3 c; fbdn_ only lowers, fbup_ only raises."""

    def __init__(self, form: str):
        k = form.split("_")
        self.form, self.kind, self.span, self.thr = form, k[0], 60.0 * float(k[1]), float(k[2]) / 100

    def margin(self, i: int, L: int) -> float:
        from ..ctx.feedback import gap_by_market
        g = gap_by_market(L, self.span).get(i, 0.0)
        if g >= self.thr and self.kind in ("fb", "fbdn"):
            return 0.025
        if g <= -self.thr and self.kind in ("fb", "fbup"):
            return 0.035
        return 0.03

    def __call__(self, mk, L):
        pu, pdn = mk.pred("v1", L)
        d = rules.vtaker(mk.tab, pu, pdn, margin=self.margin(mk.id, L))
        return {k: d[k] for k in ("t", "side", "shares", "limit")}


FB = ["fb_30_2", "fb_60_1", "fb_60_2", "fb_120_1", "fb_120_2", "fbdn_120_2", "fbup_60_2"]


def taker_fb():
    from ..ctx.feedback import gap_by_market
    for f in FB:                                   # warm the caches before the worker fork
        for L in (0, -40):
            gap_by_market(L, 60.0 * float(f.split("_")[1]))
    return VT_ANY, [Arm(f, FeedbackRule(f)) for f in FB] + [Arm("m3", Rule("m3"))], {"m3": VT_ANY}


class RefitRule:
    """The deployed taker rule on a refit variant's predictions (adapt/), memoised per market."""
    _memo: dict = {}

    def __init__(self, var: str, margin: float, require=None):
        import pickle
        from ..adapt import MODELS
        self.var, self.margin, self.require = var, margin, require
        self.mdl = {}
        for L in (0, -40):
            with open(MODELS / f"{var}_L{L}.pkl", "rb") as fh:
                self.mdl[L] = pickle.load(fh)

    def __call__(self, mk, L):
        from ..adapt.sides import predict_sides
        key = (self.var, L, mk.id)
        if key not in RefitRule._memo:
            if len(RefitRule._memo) > 8:
                RefitRule._memo.clear()
            RefitRule._memo[key] = predict_sides(mk.tab, ctx(mk.id, len(mk.tab)), self.mdl[L])
        pu, pdn = RefitRule._memo[key]
        d = rules.vtaker(mk.tab, pu, pdn, margin=self.margin, require=self.require)
        return {k: d[k] for k in ("t", "side", "shares", "limit")}


# set after the row screen (adapt/rowstats.py): agc fixed the busy-window calibration; ds, dsc
# and q25 lost the ranking screen; ctx (activity as plain inputs) is the incumbent contrast
REFIT = {"agc": (2.5, 2.75, 3.0), "agc_add": (2.75, 3.0), "ctx": (3.0,)}


def refit():
    arms = [Arm(f"{v}_m{m:g}", RefitRule(v, m / 100)) for v, ms in REFIT.items() for m in ms]
    return VT_ANY, arms, {}


FAMILIES = {"taker_margin": taker_margin, "taker_slow": taker_slow, "veto_margin": veto_margin, "refit": refit,
            "taker_fb": taker_fb}
