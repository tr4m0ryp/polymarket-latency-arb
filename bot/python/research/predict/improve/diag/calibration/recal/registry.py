"""Named recalibration forms shared by the row-level test (recal/rows.py) and the simulator
arms (recal/arms.py). Each form turns a prediction array p (one side, $/sh) into a score
and the margin it is compared with:

  m2 .. m5           static margin X c (m3 = the deployed rule)
  busy_m4.5          4.5 c in the busy-index top tertile (train cutpoints), 3 c elsewhere
  pmtr_m4            4 c in the Polymarket-trade-rate top tertile, 3 c elsewhere
  iso                isotonic p -> E[1 s value | p] fitted on select, margin 3 c (a static margin)
  iso_busy           same per busy tertile (a static margin per regime)
  onl_r1_30          online additive bias of the 1 s target on the band 2-5 c, tau 30 min
  onl_r10_30 / _90   online additive bias of the 10 s markout on the band 2-5 c, tau 30 / 90 min
  onlratio_r1_90     online ratio (all p >= 2 c labels) of the 1 s target, tau 90 min
  rm_Q_B             regime margin: Q c below busy index HI (train ~88th percentile, the
                     extreme-activity regime), B c at or above it"""
from __future__ import annotations

import numpy as np

from .forms import Isotonic, online

FORMS = ["m2", "m2.5", "m3", "m3.5", "m4", "m5", "busy_m4.5", "pmtr_m4", "iso", "iso_busy",
         "onl_r1_30", "onl_r10_30", "onl_r10_90", "onlratio_r1_90"]
RM = [f"rm_{q:g}_{b:g}" for q in (2.0, 2.5, 3.0) for b in (3.0, 3.5, 4.0) if b > q]
HI = 1.0   # busy index (mean of train-standardised log rates); 11.6% of train rows, 62.6% of ext


def make_fit(timelines: dict, cuts: dict) -> dict:
    """timelines: L -> chosen-row frame (t, pred, r1, r10, win, lv) over train..ext."""
    fit = {"cuts": cuts, "labels": {}, "iso": {}, "iso_busy": {}}
    for L, d in timelines.items():
        w = (d["pred"] >= 0.02).to_numpy()
        fit["labels"][L] = {k: d[k].to_numpy()[w] for k in ("t", "pred", "r1", "r10")}
        sel = (d["win"] == "select").to_numpy()
        p, y, lv = d["pred"].to_numpy()[sel], d["r1"].to_numpy()[sel], d["lv"].to_numpy()[sel]
        fit["iso"][L] = Isotonic(0.0).fit(p, y, np.zeros(len(p), int))
        fit["iso_busy"][L] = Isotonic(0.0).fit(p, y, lv)
    return fit


def score(form: str, p: np.ndarray, t: np.ndarray, lv: np.ndarray, lv_pmtr: np.ndarray, L: int,
          fit: dict, busy: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray | float]:
    """(score, margin) for one side's predictions at times t with regime levels lv (busy
    index tertile), lv_pmtr (Polymarket trade-rate tertile) and the busy index itself."""
    if form.startswith("rm_"):
        _, q, b = form.split("_")
        return p, np.where(busy >= HI, float(b) / 100, float(q) / 100)
    if form.startswith("m") and form[1:].replace(".", "").isdigit():
        return p, float(form[1:]) / 100
    if form == "busy_m4.5":
        return p, np.where(lv == 2, 0.045, 0.03)
    if form == "pmtr_m4":
        return p, np.where(lv_pmtr == 2, 0.04, 0.03)
    if form == "iso":
        return fit["iso"][L](p, np.zeros(len(p), int)), 0.03
    if form == "iso_busy":
        return fit["iso_busy"][L](p, lv), 0.03
    lab = fit["labels"][L]
    if form.startswith("onl_"):
        _, y, tau = form.split("_")
        return online(t, p, lab["t"], lab["pred"], lab[y], L, 60.0 * float(tau), band=(0.02, 0.05),
                      kind="additive", lag=1.0 if y == "r1" else 10.0), 0.03
    if form.startswith("onlratio_"):
        _, y, tau = form.split("_")
        return online(t, p, lab["t"], lab["pred"], lab[y], L, 60.0 * float(tau), band=(0.02, 1.0),
                      kind="ratio", lag=1.0 if y == "r1" else 10.0), 0.03
    raise ValueError(form)
