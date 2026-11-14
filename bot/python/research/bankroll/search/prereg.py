"""Freeze the cap grid, the objective and the evaluation plan (written once, never overwritten).

    PYTHONPATH=. python3 -m research.bankroll.search.prereg -> data/out/bankroll/prereg.json"""
from __future__ import annotations

import itertools
import json
import time

from .. import OUT, START
from ..sim.caps import INF, Caps

SIZING = [(0, s) for s in (5, 10, 20, 30, 60)] + [(1, f) for f in (0.01, 0.02, 0.03, 0.05, 0.08, 0.12)] \
    + [(2, c) for c in (0.1, 0.25, 0.5, 1.0)]
MARKET = (0.05, 0.10, 0.15, 0.25, 0.40, INF)
OPEN = (0.25, 0.50, INF)
SIDE = (0, 1, 2, 3)            # none, one direction, per-side fill cap, hedge only (amendment 1)
FILLS = (1, 2, 3, INF)
DD = (0.15, 0.25, 0.40, INF)
EDGE = (0.0, 0.005, 0.01, 0.02)

PLAN = {
    "start": START,
    "objective": "max median log(E_24h / start), E = cash + open cost after every market of the day is paid",
    "constraints": {"p_below_50_24h": 0.05, "p_below_25_7d": 0.01},
    "tie_break": "higher p10 of 24 h log growth",
    "choose_on": "selection hours (before 2026-10-13 00:00 UTC), arm v1_frozen, hold `old` (195 live "
                 "orders of 2026-10-13), redeem 120 s after the market end",
    "stage1": "every grid point, 200 bootstrap 24 h paths; keep the 100 best medians among points with "
              "P(<$50 in 24 h) <= 0.08 on the screen",
    "stage2": "finalists: 2000 bootstrap 24 h paths + all 288-market rotations (24 h) + 1000 bootstrap 7 d "
              "paths; constraints must hold on bootstrap and rotations; winner = best bootstrap median",
    "report_only": "test hours (both arms), hold `new` (bot run 2026-10-14) and `fast50`, redeem 1 h, "
                   "$26 start, ablation of each cap from the winner, live config (60 sh, no caps, no fit)",
    "fixed": {"max_sh": 500, "fit": 1, "refractory_s": 0.2, "i": 0},
}


FLOOR = (INF, 0.5, 0.6, 0.7)    # amendment 2: halt below x the all-time peak equity
AMEND2 = ("stage 2 found no grid point meeting P(ever < $25 in 7 d) <= 1% (best 5.4%): a daily drawdown "
          "pause cannot stop a run of bad days. Added an all-time-peak floor halt (0.5 / 0.6 / 0.7, the "
          "'never lose everything' mechanism) to the whole grid; stage 1b = 200 7 d bootstrap paths on the "
          "2,000 best stage-1 points per floor, stage 2 = the 100 best 24 h medians among points with stage-1b "
          "P(< $25 in 7 d) <= 2%; the user's update (sizing must compound) restricts the winner to fraction / "
          "Kelly sizing, the best fixed-size point is reported beside it. Test hours still unscored.")


def grid(floors=(INF,)) -> list[Caps]:
    out = []
    for fl, (mode, sz), fm, fe, side, nf, dd, me in itertools.product(floors, SIZING, MARKET, OPEN, SIDE, FILLS,
                                                                       DD, EDGE):
        out.append(Caps(size_mode=mode, size=float(sz), market_frac=fm, open_frac=fe, side_policy=side,
                        max_fills=float(nf), dd_stop=dd, min_edge=me, floor=fl))
    return out


AMEND1 = ("side policies (b) per-side fill cap, opposite side free and (c) hedge only (an opposite order is "
          "capped at the net share imbalance, so it never raises the market's worst-case loss) added to "
          "(a) one direction and (d) none, on the coordinator's request, before any path was scored")


AMEND2_NOW = True


def main():
    p = OUT / "prereg.json"
    if p.exists():
        body = json.loads(p.read_text())
        if len(body.get("amendments", [])) == 1 and AMEND2_NOW:
            body["amendments"].append({"utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "what": AMEND2,
                                       "scored_before": "selection hours only (stage 1 + 2); test hours unscored"})
            body["grid"]["floor"] = FLOOR
            p.write_text(json.dumps(body, indent=1))
            print("amended (2)", body["amendments"][1]["utc"])
        if "amendments" not in body:
            g = grid()
            body["amendments"] = [{"utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "what": AMEND1,
                                   "scored_before": False}]
            body["n_grid"], body["grid"]["one_side"] = len(g), None
            body["grid"]["side_policy"] = SIDE
            p.write_text(json.dumps(body, indent=1))
            print("amended", body["amendments"][0]["utc"], len(g))
        print("exists, frozen at", body["frozen_utc"])
        return
    OUT.mkdir(parents=True, exist_ok=True)
    g = grid()
    body = dict(PLAN, frozen_utc=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), n_grid=len(g),
                grid={"sizing": SIZING, "market_frac": MARKET, "open_frac": OPEN, "one_side": SIDE,
                      "max_fills": FILLS, "dd_stop": DD, "min_edge": EDGE})
    p.write_text(json.dumps(body, indent=1))
    print("frozen", body["frozen_utc"], len(g), "grid points")


if __name__ == "__main__":
    main()
