"""Mechanism check of C3: the common-mode residual e = pred_up + pred_dn + c at firing rows.

Part 1 (label-free, every allowed window + busyQ): e at the rows each arm fires on (frozen
vt_any / veto and the C3 variants), L = 0 and -40: n, mean, p90, share > 0 (cents).
Part 2 (labelled, decision rows of every allowed window through Fold.load_rows, a
diagnostic that chooses nothing): e = err + dc, where err = pred_up + pred_dn + c_m is model
error at the match book (c_m = spread + fees at t + L + 150 ms, so y_up + y_dn = -c_m exactly)
and dc = c_seen - c_m is the spread change during the hold. Plus the best-level realized 1 s
value of the side fired, by arm (no depth, no rivals: the simulator does those).

    OMP_NUM_THREADS=2 nice -n 10 python3 -m research.predict.improve.cand.<pkg>.diag_e
Writes data/out/predict/improve/c3_coherence/diag_e_{fire,decomp}.csv; with argument 2 (round 2,
match-cost anchor) diag_e2_*.csv with ehat = pred_up + pred_dn + c_hat and c_hat - c_m."""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "2")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from research.predict import OUT  # noqa: E402
from research.predict.improve.harness import windows as W  # noqa: E402
from research.predict.improve.harness.api import Market  # noqa: E402
from research.predict.improve.harness.fold import Fold  # noqa: E402
from research.predict.improve.harness.guard import SEALED, assert_allowed  # noqa: E402
from research.predict.improve.harness.score import sets  # noqa: E402
from research.predict.sim import rules  # noqa: E402

from .arms import Coh  # noqa: E402
from .cost import chat  # noqa: E402
from .score import costs, fee  # noqa: E402

DST = OUT / "improve" / "c3_coherence"
ARMS = {"vt_any": Coh(0.03, None, "none"), "veto": Coh(0.02, "trigger", "none"),
        "coh_any_m0.03": Coh(0.03), "coh_any_m0.025": Coh(0.025), "coh_trig_m0.02": Coh(0.02, "trigger"),
        "cohc_any_m0.03": Coh(0.03, None, "cap"), "cohh_any_m0.03": Coh(0.03, None, "proj", 0.5)}
ARMS2 = {"vt_any": ARMS["vt_any"], "veto": ARMS["veto"], "cm_any_m0.03": Coh(0.03, anchor="cm"),
         "cm_any_m0.025": Coh(0.025, anchor="cm"), "cm_trig_m0.02": Coh(0.02, "trigger", anchor="cm"),
         "cm_trig_m0.015": Coh(0.015, "trigger", anchor="cm")}
CHOOSE_FOLD = {"select": "A", "dev3": "A", "test3r1": "B", "ext": "B"}


def fire_idx(tab: pd.DataFrame, arm: Coh, pu, pd_, L: int, c=None) -> np.ndarray:
    """Row indices an arm fires on (t made unique so the returned times map back exactly)."""
    t = tab["t"].to_numpy(float)
    tu = tab.assign(t=t + np.arange(len(t)) * 1e-9)
    vu, vd, _ = arm.values(tab, pu, pd_, L, c)
    d = rules.vtaker(tu, vu, vd, margin=arm.margin, require=arm.require)
    return np.searchsorted(tu["t"].to_numpy(), d["t"])


def _markets():
    mk = W._markets()
    ids = W.all_eval_ids()
    assert_allowed(mk.start[ids], "c3 diag")
    out = [Market(i, {"start": float(mk.start[i]), "end": float(mk.end[i])}) for i in ids]
    busy = sets.busy_markets(pd.DataFrame([m.activity() for m in out]))
    return out, busy


def part1(mks, busy, ARMS=ARMS) -> pd.DataFrame:
    rows = []
    for m in mks:
        tab, w = m.tab, W.window_of(m.id)
        for L in (0, -40):
            pu, pd_ = m.pred("v1", L)
            e = np.asarray(pu) + np.asarray(pd_) + costs(tab)
            ch = chat(tab, L) if ARMS is ARMS2 else None
            for name, arm in ARMS.items():
                ix = fire_idx(tab, arm, pu, pd_, L, ch)
                rows += [{"m": m.id, "win": w, "busyQ": m.id in busy, "L": L, "arm": name, "e": x} for x in e[ix]]
            ok = np.isfinite(e) & (tab["pm_bb"].to_numpy() > 0) & (tab["pm_ba"].to_numpy() < 100)
            rows += [{"m": m.id, "win": w, "busyQ": m.id in busy, "L": L, "arm": "all_rows", "e": x}
                     for x in e[ok][:: max(1, ok.sum() // 200)]]
    return pd.DataFrame(rows)


def _summ(g: pd.DataFrame) -> pd.Series:
    e = 100 * g["e"].to_numpy(float)
    return pd.Series({"n": len(e), "e_mean_c": e.mean(), "e_p90_c": np.percentile(e, 90) if len(e) else np.nan,
                      "e_pos": (e > 0).mean()})


def part2(mks, busy, ARMS=ARMS) -> pd.DataFrame:
    by_id = {m.id: m for m in mks}
    rows = []
    for w, f in CHOOSE_FOLD.items():
        lab = Fold(f).load_rows(windows=(w,), cols=["t", "x_ba0", "x_bb0", "x_m1_0", "x_ba-40", "x_bb-40", "x_m1_-40"])
        assert lab["m"].map(W._markets().start).max() < SEALED
        for i, g in lab.groupby("m", sort=False):
            m = by_id[int(i)]
            tab = m.tab
            assert len(g) == len(tab) and np.allclose(g["t"].to_numpy(), tab["t"].to_numpy())
            for L in (0, -40):
                pu, pd_ = m.pred("v1", L)
                ba, bb = g[f"x_ba{L}"].to_numpy(float) / 100, g[f"x_bb{L}"].to_numpy(float) / 100
                mk1 = g[f"x_m1_{L}"].to_numpy(float)
                good = (ba > 0.005) & (ba < 0.995) & (bb > 0.005) & (bb < 0.995) & np.isfinite(mk1)
                cm = (ba - bb) + fee(ba) + fee(1 - bb)
                yu, yd = mk1 - ba - fee(ba), bb - mk1 - fee(1 - bb)
                cs = costs(tab)
                ch = chat(tab, L) if ARMS is ARMS2 else cs
                e = np.asarray(pu) + np.asarray(pd_) + cs
                for name, arm in {**ARMS, "all_rows": None}.items():
                    if arm is None:
                        ix = np.flatnonzero(good & np.isfinite(e))[::20]
                    else:
                        ix = fire_idx(tab, arm, pu, pd_, L, ch if ARMS is ARMS2 else None)
                        ix = ix[good[ix]]
                    up = np.asarray(pu)[ix] >= np.asarray(pd_)[ix]
                    rows.append(pd.DataFrame({
                        "m": m.id, "win": w, "busyQ": m.id in busy, "L": L, "arm": name, "e": e[ix],
                        "err": np.asarray(pu)[ix] + np.asarray(pd_)[ix] + cm[ix], "dc": cs[ix] - cm[ix],
                        "ehat": np.asarray(pu)[ix] + np.asarray(pd_)[ix] + ch[ix], "chat_err": ch[ix] - cm[ix],
                        "y": np.where(up, yu[ix], yd[ix]), "pred": np.where(up, np.asarray(pu)[ix], np.asarray(pd_)[ix])}))
    return pd.concat(rows, ignore_index=True)


def _summ2(g: pd.DataFrame) -> pd.Series:
    q = pd.qcut(g["e"].rank(method="first"), 3, labels=False) if len(g) >= 30 else None
    s = {"n": len(g), "e_c": 100 * g["e"].mean(), "err_c": 100 * g["err"].mean(), "dc_c": 100 * g["dc"].mean(),
         "y_c": 100 * g["y"].mean(), "pred_c": 100 * g["pred"].mean()}
    if q is not None:
        for k, lab in ((0, "lo"), (2, "hi")):
            s[f"y_{lab}e_c"] = 100 * g.loc[q == k, "y"].mean()
    s["ehat_c"], s["chat_err_c"] = 100 * g["ehat"].mean(), 100 * g["chat_err"].mean()
    s["corr_ehat_err"] = g["ehat"].corr(g["err"]) if len(g) > 2 else np.nan
    s["corr_e_err"] = g["e"].corr(g["err"]) if len(g) > 2 else np.nan
    s["corr_e_dc"] = g["e"].corr(g["dc"]) if len(g) > 2 else np.nan
    return pd.Series(s)


def main() -> None:
    import sys
    r2 = len(sys.argv) > 1 and sys.argv[1] == "2"
    arms, sfx = (ARMS2, "2") if r2 else (ARMS, "")
    DST.mkdir(parents=True, exist_ok=True)
    mks, busy = _markets()
    f1 = part1(mks, busy, arms)
    s1 = pd.concat([f1.groupby(["L", "arm", "win"]).apply(_summ).reset_index(),
                    f1[f1["busyQ"]].groupby(["L", "arm"]).apply(_summ).reset_index().assign(win="busyQ")])
    s1.to_csv(DST / f"diag_e{sfx}_fire.csv", index=False)
    print(s1.round(3).to_string(), flush=True)
    f2 = part2(mks, busy, arms)
    s2 = pd.concat([f2.groupby(["L", "arm", "win"]).apply(_summ2).reset_index(),
                    f2[f2["busyQ"]].groupby(["L", "arm"]).apply(_summ2).reset_index().assign(win="busyQ")])
    s2.to_csv(DST / f"diag_e{sfx}_decomp.csv", index=False)
    print(s2.round(3).to_string(), flush=True)


if __name__ == "__main__":
    main()
