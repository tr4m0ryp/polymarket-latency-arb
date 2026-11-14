"""Trade-level calibration: the frozen simulator fills of the deployed arms joined to the
model's prediction and the regime at their decision row.

    python3 -m research.predict.improve.diag.calibration.analyze.trades

Fills come from the frozen runs (fills-sel1 / dev1 / final / ext.pkl; same simulator, 150 ms
hold, depth and rivals). Per fill: predicted value at the seen ask ($/sh), realised 10 s
markout per share (mk10v / shares, at the fill price, after fee) and per $. Per window x
regime level x prediction bin: fills per market-hour, mean pred, realised, gap, c/$ with a
market-bootstrap CI. Writes OUT/trades.md and OUT/trades.csv."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ...... import predict
from .. import OUT
from ..safe import TAGS, check, start_of
from .....report.md import md
from .common import LEVELS, boot_ratio, busy_index, fmt, level, rows

ARMS = {"vt_v1_m0.03_any": "v1_L{L}", "vt_v1_m0.02_trigger": "v1_L{L}", "vt_v3p_m0.02_any": "v3p_L{L}"}
WINS = ("select", "dev3", "final", "ext")
PB = (0.0, 0.03, 0.04, 0.05, 0.07, 1.0)


def fills(win: str) -> pd.DataFrame:
    f = pd.read_pickle(predict.OUT / f"fills-{TAGS[win]}.pkl")
    f = f[f["arm"].isin(list(ARMS)) & f["L"].isin([0, -40])].copy()
    check(start_of(f["m"].unique()))
    d = rows(win)
    out = []
    for (arm, L), g in f.groupby(["arm", "L"]):
        mdl = ARMS[arm].format(L=L)
        col = f"p_{mdl}"
        if col not in d:
            continue
        j = g.merge(d[["m", "t", "side", col] + [c for c in ("bn10", "bn60", "rv1", "rv10", "rv60", "pm10",
                                                                "pmtop10", "pmtr60", "jump10") if c in d]],
                    on=["m", "t", "side"], how="left")
        j["pred"] = j[col].astype(float)
        out.append(j.drop(columns=[col]))
    f = pd.concat(out, ignore_index=True)
    f["r10"] = f["mk10v"] / f["shares"]
    return f


def table(f: pd.DataFrame, win: str, nmk: int) -> list[dict]:
    f = f.assign(busy=busy_index(f, rows("train")))
    hours = nmk * 5 / 60
    out = []
    for (arm, L), g in f.groupby(["arm", "L"]):
        for rg in ("all", "busy", "bn60", "rv10", "pmtr60", "pmtop10"):
            lv = np.zeros(len(g), int) if rg == "all" else level(g, rg)
            for k in range(3 if rg != "all" else 1):
                s = g[lv == k]
                for lo, hi in [(PB[0], PB[-1])] + list(zip(PB[1:-1], PB[2:])):
                    b = s[(s["pred"] >= lo) & (s["pred"] < hi)]
                    if rg != "all" and (lo, hi) != (PB[0], PB[-1]):
                        continue
                    m = b["m"].to_numpy()
                    p = boot_ratio(m, b["mk10v"].to_numpy(), b["cost"].to_numpy())
                    gp = boot_ratio(m, (b["r10"] - b["pred"]).to_numpy(), np.ones(len(b)))
                    out.append({"win": win, "arm": arm, "L": L, "regime": rg,
                                "level": "all" if rg == "all" else LEVELS[k], "pred_bin": f"{lo:.2f}-{hi:.2f}",
                                "fills": len(b), "fills_per_mkt_h": len(b) / hours,
                                "pred_c": 100 * b["pred"].mean(), "r10_c_sh": 100 * b["r10"].mean(),
                                "gap_c_sh": fmt(*gp), "mk10_c_usd": fmt(*p), "mk10_usd_day": b["mk10v"].sum() / (nmk / 288),
                                "miss_pred": float(b["pred"].isna().mean())})
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    allr = []
    for w in WINS:
        f = fills(w)
        nmk = len(pd.read_csv(predict.OUT / f"markets-{TAGS[w]}.csv"))
        allr += table(f, w, nmk)
        print(w, len(f), "pred missing", float(f["pred"].isna().mean()), flush=True)
    t = pd.DataFrame(allr)
    t.to_csv(OUT / "trades.csv", index=False)
    cols = ["win", "L", "regime", "level", "pred_bin", "fills", "fills_per_mkt_h", "pred_c", "r10_c_sh", "gap_c_sh",
            "mk10_c_usd", "mk10_usd_day"]
    txt = ["# Trade-level calibration of the deployed arms (frozen simulator fills)\n"]
    for arm in ARMS:
        txt.append(f"\n## {arm}\n")
        txt.append(md(t[t["arm"] == arm][cols], 2))
    (OUT / "trades.md").write_text("\n".join(txt))


if __name__ == "__main__":
    main()
