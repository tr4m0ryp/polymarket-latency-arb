"""Variant sets per drive tag: family -> (selection variants, controls never selected).

r1: the pre-declared C4 set (spec): vlim_tight / rc_lim / rc_size on each family; controls frz
(the frozen rule re-sent through this code, must pair to 0) and C1's value-keyed size (taker
ek_vstar_2000: clip(2000 v*, 30, 200); veto vk_vstar_3000: clip(3000 v*, 100, 300), 60 at
L = -40) under the same fill model, for kill test (2).

r2: after the r1 diagnosis (diag.py, train markets: shares walked to +1 / +2 c still mark
+10-12 c/sh in every P_alive bucket and the unfilled rest of an order is free, so a cap can
only remove profitable fills): use the race clock to send MORE where depth is predicted to
survive and to walk further only where the stale level is predicted gone.
  rc_boost, rc_walk, rc_boost_walk (selection); controls ek and vlw_ek (no race model)."""
from __future__ import annotations

from ...harness.api import Arm
from .arms import Race, family


def _controls(tag: str, margin: float, require):
    ek = (Race("ek", margin, require) if not require else
          Race("ek", margin, require, K=3000.0, lo=100.0, hi=300.0, lo_by_L={-40: 60.0}))
    name = "c1_ek_vstar_2000" if not require else "c1_vk_vstar_3000"
    return [Arm(f"frz{tag}", Race("frz", margin, require)), Arm(f"{name}{tag}", ek)]


def r1():
    return {"taker": (family(0.03, None, ""), _controls("", 0.03, None)),
            "veto": (family(0.02, "trigger", "_veto"), _controls("_veto", 0.02, "trigger"))}


class _BoostWalk(Race):
    """rc_boost size with rc_walk limit."""

    def _rule(self, mk, j, side, vs, edge, L):
        self.mode = "rc_walk"
        slip, _ = super()._rule(mk, j, side, vs, edge, L)
        self.mode = "rc_boost"
        _, sh = super()._rule(mk, j, side, vs, edge, L)
        self.mode = "rc_boost_walk"
        return slip, sh


def _r2fam(margin, require, tag, **kw):
    sel = [Arm(f"rc_boost{tag}", Race("rc_boost", margin, require, **kw)),
           Arm(f"rc_walk{tag}", Race("rc_walk", margin, require, **kw)),
           Arm(f"rc_boost_walk{tag}", _BoostWalk("rc_boost_walk", margin, require, **kw))]
    ctl = [Arm(f"ek{tag}", Race("ek", margin, require, **kw)), Arm(f"vlw_ek{tag}", Race("vlw_ek", margin, require, **kw))]
    return sel, ctl


def r2():
    return {"taker": _r2fam(0.03, None, ""), "veto": _r2fam(0.02, "trigger", "_veto")}


def _sweep(margin, require, tag, kind):
    """Round 3: sweep the round-2 winner's key parameter, each point next to its race-free control."""
    if kind == "walk":
        sel = [Arm(f"rc_walk_p{p:g}_w{w:g}{tag}", Race("rc_walk", margin, require, p_thr=p, wmax=w))
               for p in (0.35, 0.5, 0.65) for w in (0.06, 0.10)]
        ctl = [Arm(f"ek{tag}", Race("ek", margin, require))] + \
              [Arm(f"vlw_ek_w{w:g}{tag}", Race("vlw_ek", margin, require, wmax=w)) for w in (0.06, 0.10)]
    else:
        sel = [Arm(f"rc_boost_m{m:g}_h{h}{tag}", Race("rc_boost", margin, require, bm=m, hi=h))
               for m in (0.5, 1.0, 2.0) for h in (200, 300)]
        ctl = [Arm(f"ek_h{h}{tag}", Race("ek", margin, require, hi=h)) for h in (200, 300)]
    return sel, ctl


def r3w():
    return {"taker": _sweep(0.03, None, "", "walk"), "veto": _sweep(0.02, "trigger", "_veto", "walk")}


def r3b():
    return {"taker": _sweep(0.03, None, "", "boost"), "veto": _sweep(0.02, "trigger", "_veto", "boost")}


def _r3fam(margin, require, tag):
    sel = [Arm(f"rc_boost_vlw_m{m:g}{tag}", Race("rc_boost_vlw", margin, require, bm=m)) for m in (0.5, 1.0, 2.0)]
    ctl = [Arm(f"vlw_ek{tag}", Race("vlw_ek", margin, require)), Arm(f"dq_vlw{tag}", Race("dq_vlw", margin, require)),
           Arm(f"max_vlw{tag}", Race("max_vlw", margin, require))]
    return sel, ctl


def r3():
    """Round 3: sweep the boost multiplier bm on the winner, next to its race-free twins."""
    return {"taker": _r3fam(0.03, None, ""), "veto": _r3fam(0.02, "trigger", "_veto")}


# pm60 (Polymarket book msgs/s over 60 s) at the fired rows of run 2 TRAIN markets, 50/75/90th pct
HEAT = {"taker": (775.8, 1015.9, 1529.3), "veto": (705.5, 920.8, 1248.3)}


def _r4fam(margin, require, tag, fam):
    sel = [Arm(f"heat_vlw_p{q}{tag}", Race("heat_vlw", margin, require, heat=h))
           for q, h in zip((50, 75, 90), HEAT[fam])]
    ctl = [Arm(f"vlw_ek{tag}", Race("vlw_ek", margin, require)), Arm(f"max_vlw{tag}", Race("max_vlw", margin, require))]
    return sel, ctl


def r4():
    """Round 4: the race-heat gauge as a size guard (full size only while the book is calm)."""
    return {"taker": _r4fam(0.03, None, "", "taker"), "veto": _r4fam(0.02, "trigger", "_veto", "veto")}


def _r5fam(margin, require, tag):
    sel = [Arm(f"max_vlw_h{h}{tag}", Race("max_vlw", margin, require, hi=h)) for h in (100, 300)] + \
          [Arm(f"max_vlw_w{w:g}{tag}", Race("max_vlw", margin, require, wmax=w)) for w in (0.04, 0.10)]
    return sel, [Arm(f"max_vlw{tag}", Race("max_vlw", margin, require))]


def r5():
    """Round 5: sweep the best arm's key parameters (size cap hi, walk cap wmax) around max_vlw
    (h 200, w 0.06). Race-free: characterises the ceiling the race clock was measured against."""
    return {"taker": _r5fam(0.03, None, ""), "veto": _r5fam(0.02, "trigger", "_veto")}


SETS = {"r1": r1, "r2": r2, "r3": r3, "r4": r4, "r5": r5, "r3w": r3w, "r3b": r3b}
