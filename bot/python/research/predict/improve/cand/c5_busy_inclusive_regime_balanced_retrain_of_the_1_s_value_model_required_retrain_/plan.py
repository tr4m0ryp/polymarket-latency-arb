"""Arm sets and their views (eval/__main__.py --set NAME). An arm spec is
(name, scheme, margin, projection, blend with the frozen v1_L0); a view is (arm names,
selection criterion) and picks per fold on that fold's choose windows when it lists several.

main: the three pre-registered variants (candidates.busy_refit) as one per-fold selection
      view and each variant alone (the kill tests compare them).
var:  the follow-up variants, each asking what would have to be true for the refit to work:
      tilt2/tilt4 (busy rows need more weight), feat (the model needs to know the regime),
      blend (the refit adds busy information but loses quiet-hour precision)."""
from __future__ import annotations

from .arms import arm
from .candidates import FRAC, busy_refit
from .fit.model import fit_fold

MAIN = ["rf_plain_m3", "rf_bal_m3", "rf_bal_coh_m3"]


def specs_fn(specs, frac: float = FRAC):
    def build(fold):
        models = fit_fold(fold, tuple(dict.fromkeys(s[1] for s in specs)), frac=frac)
        return [arm(n, models[sc], mg, coh, bl) for n, sc, mg, coh, bl in specs]
    return build


def _spec(scheme, mg, coh=False, bl=1.0):
    name = f"rf_{scheme}{'_coh' if coh else ''}{f'_bl{int(bl * 100)}' if bl < 1 else ''}_m{mg * 100:g}"
    return (name, scheme, mg, coh, bl)


# var1 (scale fix): the refits fire ~40% fewer fills than v1 at 3 c with a higher c/$; the
# margin is re-chosen on each fold's choose windows (3 c arms come from the main memo)
VAR1 = [_spec(sc, mg, coh) for sc, coh in (("bal", False), ("bal", True)) for mg in (0.02, 0.025, 0.03)] \
    + [_spec("plain", mg) for mg in (0.025, 0.03)]
# var2: shrink toward the frozen model (blend), busy rows need more weight (tilt2), the model
# needs to know the regime (feat); margins 2.5 / 3 c chosen per fold
VAR2 = [_spec(sc, mg, False, bl) for sc, bl in (("bal", 0.5), ("tilt2", 1.0), ("feat", 1.0)) for mg in (0.025, 0.03)] \
    + [_spec("bal", 0.03, False, bl) for bl in (0.25, 0.75)]       # blend-weight sweep at the frozen margin

# var3 (control): the same refit on run 2 train only (v1's rows at frac 0.25); if it loses to
# v1 as much as the busy-inclusive refits, the loss is refit variance / v1's selection, not the rows
VAR3 = [_spec("tronly", 0.03), _spec("tronly", 0.025)]

# var4 (isolate the added rows): frac 0.5 draws exactly v1's run 2 train rows (eval/repro.py: the
# fit path reproduces v1_L0 to 0.0 on them) plus the fold's choose-window rows, so the only
# difference from the frozen model is the added (busy-inclusive) rows and their weights
VAR4 = [(n.replace("_m", "_f50_m"), sc, mg, coh, bl) for n, sc, mg, coh, bl in
        (_spec("plain", 0.03), _spec("bal", 0.03), _spec("bal", 0.03, True))]


def _single(specs):
    return {s[0]: ([s[0]], "lcb") for s in specs}


def _sweep(specs, key):
    return [s[0] for s in specs if s[0].startswith(key + "_m")]


SETS = {
    "main": (busy_refit, {"busy_refit": (MAIN, "lcb"), "rf_plain": (["rf_plain_m3"], "lcb"),
                          "rf_bal": (["rf_bal_m3"], "lcb"), "rf_bal_coh": (["rf_bal_coh_m3"], "lcb")}),
    "var1": (specs_fn(VAR1), {**_single(VAR1), **{f"{k}_msel": (_sweep(VAR1, k), "lcb")
                                                  for k in ("rf_bal", "rf_bal_coh", "rf_plain")},
                              "var1_all_sel": ([s[0] for s in VAR1], "lcb")}),
    "var2": (specs_fn(VAR2), {**_single(VAR2), **{f"{k}_msel": (_sweep(VAR2, k), "lcb")
                                                  for k in ("rf_bal_bl50", "rf_tilt2", "rf_feat")},
                              "rf_bal_blsel_m3": (["rf_bal_bl25_m3", "rf_bal_bl50_m3", "rf_bal_bl75_m3"], "lcb")}),
    "var3": (specs_fn(VAR3), _single(VAR3)),
    "var4": (specs_fn(VAR4, 0.5), _single(VAR4)),
}
