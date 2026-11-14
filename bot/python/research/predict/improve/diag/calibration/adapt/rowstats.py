"""Row-level read of the refit variants next to the frozen v1 (best level, no depth or rivals:
a screen; the simulator decides).

    python3 -m research.predict.improve.diag.calibration.adapt.rowstats

Per model x L x window, on the side the model would buy: firing rows per market-hour
(pred >= 3 c), mean pred / realised 1 s / 10 s and the gaps (market-bootstrap CI), the slope
of realised 1 s on pred, the same gap on busy rows (busy index >= 1), the top-2% realised
10 s value (ranking), and a row proxy: orders after the 0.2 s refractory at 3 c and at the
threshold that matches the frozen arm's order count on select, 60 sh x realised 10 s $/day,
paired vs the frozen 3 c rule. Writes OUT/adapt_rows.md / .csv."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .....report.md import md
from .. import CACHE, OUT
from ..analyze.common import boot_ratio, busy_index, rows
from ..recal.rows import orders

WINS = ("train", "select", "dev3", "final", "ext")


def table(win: str) -> pd.DataFrame:
    d = rows(win)
    p = pd.read_pickle(CACHE / f"adapt-preds-{win}.pkl")
    d = d.merge(p, on=["m", "row", "side"], how="inner", validate="one_to_one")
    d["busy"] = busy_index(d, rows("train"))
    return d


def chosen(d: pd.DataFrame, col: str, L: int) -> pd.DataFrame:
    key = d["m"].to_numpy().astype(np.int64) * 10_000_000 + d["row"].to_numpy().astype(np.int64)
    d = d.iloc[np.lexsort((-d["side"].to_numpy(), key))]
    x = d[col].to_numpy(float)
    pick = np.where(x[0::2] >= x[1::2], 0, 1) + np.arange(0, len(d), 2)
    c = d.iloc[pick][["m", "t", "seen", "busy", f"v1_{L}", f"v10_{L}", f"bad{L}"]].copy()
    c["pred"] = x[pick]
    c = c.rename(columns={f"v1_{L}": "r1", f"v10_{L}": "r10"})
    c = c[(c[f"bad{L}"] == 0) & np.isfinite(c["r1"]) & np.isfinite(c["r10"])]
    return c.sort_values(["m", "t"], kind="stable").reset_index(drop=True)


def proxy(c: pd.DataFrame, thr: float) -> tuple[dict, pd.Series]:
    """Orders at pred >= thr after the refractory; per-market 60 sh x realised 10 s value."""
    k = orders(c, c["pred"].to_numpy(), thr)
    mk = np.unique(c["m"])
    days = len(mk) / 288
    v = pd.Series(60 * c["r10"].to_numpy() * k, index=c["m"]).groupby(level=0).sum().reindex(mk, fill_value=0)
    return {"orders_h": k.sum() / (len(mk) / 12), "usd_day": v.sum() / days}, v


def stats(c: pd.DataFrame) -> dict:
    mk = c["m"].to_numpy()
    nm = len(np.unique(mk))
    f = c["pred"].to_numpy() >= 0.03
    out = {"fire_h": f.sum() / (nm / 12), "pred_c": 100 * c.loc[f, "pred"].mean(),
           "r1_c": 100 * c.loc[f, "r1"].mean(), "r10_c": 100 * c.loc[f, "r10"].mean()}
    for y in ("r1", "r10"):
        g = boot_ratio(mk[f], (c[y] - c["pred"]).to_numpy()[f], np.ones(f.sum()))
        out[f"gap_{y}"], out[f"gap_{y}_lo"], out[f"gap_{y}_hi"] = (100 * x for x in g)
    fb = f & (c["busy"].to_numpy() >= 1.0)
    out["busy_fire_share"] = fb.sum() / max(f.sum(), 1)
    out["gap_r1_busy"] = 100 * (c.loc[fb, "r1"] - c.loc[fb, "pred"]).mean() if fb.any() else np.nan
    w = c["pred"].to_numpy() >= 0
    out["slope"] = float(np.polyfit(c.loc[w, "pred"], c.loc[w, "r1"], 1)[0]) if w.sum() > 10 else np.nan
    top = c["pred"] >= c["pred"].quantile(0.98)
    out["top2_r10_c"] = 100 * c.loc[top, "r10"].mean()
    return out


def paired(v: pd.Series, vb: pd.Series, B: int = 1000) -> tuple[float, float, float]:
    d = (v - vb.reindex(v.index, fill_value=0)).to_numpy()
    days = len(d) / 288
    s = d[np.random.default_rng(7).integers(0, len(d), size=(B, len(d)))].sum(1) / days
    return d.sum() / days, np.percentile(s, 2.5), np.percentile(s, 97.5)


def main() -> None:
    tabs = {w: table(w) for w in WINS}
    models = sorted({c[2:].rsplit("_L", 1)[0] for c in tabs["select"].columns if c.startswith("p_") and "_L" in c}
                    - {"v1", "v3p"})
    out = []
    for L in (0, -40):
        base = {w: chosen(tabs[w], f"p_v1_L{L}", L) for w in WINS}
        bk = {w: proxy(base[w], 0.03)[1] for w in WINS}
        n_sel = orders(base["select"], base["select"]["pred"].to_numpy(), 0.03).sum()
        for name in ["v1"] + models:
            col = f"p_{name}_L{L}"
            cs = {w: chosen(tabs[w], col, L) for w in WINS}
            s = np.sort(cs["select"]["pred"].to_numpy())[::-1]
            lo_t, hi_t = 0.005, 0.10
            for _ in range(30):                      # threshold matching the frozen order count on select
                mid = (lo_t + hi_t) / 2
                n = orders(cs["select"], cs["select"]["pred"].to_numpy(), mid).sum()
                lo_t, hi_t = (mid, hi_t) if n > n_sel else (lo_t, mid)
            thr_m = (lo_t + hi_t) / 2
            for w in WINS:
                r = {"model": name, "L": L, "win": w, **stats(cs[w])}
                for tag, thr in (("m3", 0.03), ("bm", thr_m)):
                    o, v = proxy(cs[w], thr)
                    g = paired(v, bk[w])
                    r |= {f"{tag}_orders_h": o["orders_h"], f"{tag}_usd_day": o["usd_day"],
                          f"{tag}_vs_frozen": g[0], f"{tag}_lo": g[1], f"{tag}_hi": g[2]}
                r["bm_thr_c"] = 100 * thr_m
                out.append(r)
            print(L, name, flush=True)
    t = pd.DataFrame(out)
    t.to_csv(OUT / "adapt_rows.csv", index=False)
    txt = ["# Refit variants, row-level screen (best level, 60 sh, 0.2 s refractory)\n"]
    for (L, w), g in t.groupby(["L", "win"], sort=False):
        txt.append(f"\n## L = {L}, {w}\n\n" + md(g.drop(columns=["L", "win"]).round(2)))
    (OUT / "adapt_rows.md").write_text("\n".join(txt))


if __name__ == "__main__":
    main()
