"""Follow-up tables of the write-up: the rival taker clock, the trade hazard on stale touches,
the per-hour Binance regime (message rate, feed lag), the train-vs-ext feature support, and the
post hoc gates on the deployed arms' unseen fills (labelled post hoc: these windows were tests).

    python3 research/predict/improve/diag/mechanism-literature posthoc"""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.predict.report.md import md
from research.predict import RUN2, SPLIT
from .. import PCACHE, RUN_HOURS, SCACHE, SEALED, WORK
from ..data.guard import assert_allowed, market_ids
from .run import DIR

WIN = ((-0.3, 0.0), (0.0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.5), (0.5, 1.0), (1.0, 2.0))
SUPPORT = ("p_lam", "s_lam", "st_tn", "sigma", "p_tsm", "pm_tsc")


def rival_clock(d: pd.DataFrame) -> pd.DataFrame:
    e = d[d["placebo"] == 0].copy()
    e["grp"] = pd.qcut(e["pmsg10"], [0, .4, .8, 1.0], labels=["calm", "mid", "busy"]).astype(str)
    rows = []
    for lo, hi in WIN:
        r = {"window ms": f"{int(lo * 1000)}..{int(hi * 1000)}"}
        for g in ("calm", "busy"):
            x = e[e["grp"] == g]
            r[f"{g} toward /s"] = round(x[f"n_s{lo:g}"].mean() / (hi - lo), 1)
            r[f"{g} against /s"] = round(x[f"n_o{lo:g}"].mean() / (hi - lo), 1)
        r["placebo toward /s"] = round(d.loc[d["placebo"] == 1, f"n_s{lo:g}"].mean() / (hi - lo), 1)
        rows.append(r)
    hz = []
    for g, x in list(e.groupby("grp")) + [("placebo", d[d["placebo"] == 1])]:
        p, life = x["snipe"].mean(), x["lag_q"].median()
        hz.append({"state": g, "n": len(x), "touch life s": round(life, 3), "ended by trade": round(p, 2),
                   "trade hazard /s": round(-np.log(1 - p) / life, 2)})
    return pd.DataFrame(rows), pd.DataFrame(hz)


def hours() -> pd.DataFrame:
    rows = []
    for h in RUN_HOURS:
        assert (h + 1) * 3600 <= SEALED
        p = SCACHE / f"hour-{h}.npz"
        if not p.exists():
            continue
        with np.load(p) as z:
            if "fb_t" not in z.files:
                continue
            t, T = z["fb_t"], z["fb_T"]
        c = np.bincount(((t - t.min()) // 10).astype(int)) / 10
        rows.append({"hour": h, "utc": (h * 3600 % 86400) // 3600, "msgs/s": round(len(t) / 3600, 1),
                     "share 10 s > 313/s": round((c > 313).mean(), 3),
                     "lag median s": round(float(np.median(t - T)), 3), "share lag > 0.5 s": round(((t - T) > 0.5).mean(), 3)})
    return pd.DataFrame(rows)


def support() -> pd.DataFrame:
    mk = pd.read_csv(SCACHE / "markets.csv", usecols=["start"])
    tr = [i for i, s in enumerate(mk["start"]) if RUN2 <= s < SPLIT][::3]   # run 2 train, every 3rd
    sets = {"train": tr, **{w: v for w, v in market_ids(("test3r1", "ext")).items()}}

    def load(idx):
        out = []
        for i in idx:
            assert mk["start"][i] < SEALED
            p = PCACHE / "tab" / f"{i}.npz"
            if p.exists():
                with np.load(p) as z:
                    out.append(pd.DataFrame({c: z[c] for c in SUPPORT}))
        return pd.concat(out)
    d = {k: load(v) for k, v in sets.items()}
    rows = []
    for c in SUPPORT:
        p99 = np.nanpercentile(d["train"][c], 99)
        r = {"feature": c}
        for k, x in d.items():
            r[f"{k} median"] = round(float(np.nanmedian(x[c])), 6)
            r[f"{k} > train p99"] = round(float((x[c] > p99).mean()), 3)
        rows.append(r)
    return pd.DataFrame(rows)


def gates() -> pd.DataFrame:
    f = pd.read_pickle(WORK / "fills_state.pkl")
    assert_allowed(f["start"], "fills")
    mi = market_ids(("dev3", "test3r1", "ext"))
    ids = sorted(i for v in mi.values() for i in v)
    days, rng = len(ids) / 288, np.random.default_rng(3)
    if "stale_s" not in f:
        parts = []
        for i, g in f.groupby("m"):
            with np.load(PCACHE / "tab" / f"{i}.npz") as z:
                t, ps = z["t"], z["pm_stale"]
            j = np.clip(np.searchsorted(t, g["t"].to_numpy(), side="right") - 1, 0, None)
            parts.append(pd.Series(ps[j] * g["side"].to_numpy(), index=g.index))
        f["stale_s"] = pd.concat(parts)
    u = f[(f["window"] != "select") & f["m"].isin(ids)]

    def gain(a, b):
        d = (a.groupby("m")["mk10v"].sum().reindex(ids).fillna(0) - b.groupby("m")["mk10v"].sum().reindex(ids).fillna(0)).to_numpy()
        s = d[rng.integers(0, len(d), (1000, len(d)))].sum(1) / days
        return f"{d.sum() / days:+.0f} [{np.percentile(s, 2.5):+.0f}, {np.percentile(s, 97.5):+.0f}]"
    rules = {"none": lambda g: np.ones(len(g), bool),
             "feed ok (lag <= 0.5 s, compression <= 1.5; micf gated too)":
                 lambda g: ((g["lag_feed"] <= 0.5) & (g["compress"] <= 1.5)).to_numpy(),
             "side-signed staleness > 0": lambda g: (g["stale_s"] > 0).to_numpy(),
             "msgs/s <= 313": lambda g: (g["pmsg10"] <= 313).to_numpy()}
    rows = []
    for name, fn in rules.items():
        for L in (0, -40):
            base = u[(u["arm"] == "micf") & (u["L"] == L)]
            base = base[fn(base)] if name.startswith("feed") else base
            for arm in ("vt_v1_m0.03_any", "vt_v1_m0.02_trigger"):
                g = u[(u["arm"] == arm) & (u["L"] == L)]
                k = g[fn(g)]
                rows.append({"gate (post hoc)": name, "arm": arm, "L": L, "fills": len(k),
                             "mk10 c/$": round(100 * k["mk10v"].sum() / k["cost"].sum(), 1),
                             "mk10 $/day": round(k["mk10v"].sum() / days), "gain vs micf $/day [CI]": gain(k, base)})
    return pd.DataFrame(rows)


def main() -> None:
    np.seterr(all="ignore")
    DIR.mkdir(parents=True, exist_ok=True)
    d = pd.read_pickle(WORK / "events.pkl")
    assert_allowed(d["start"], "events")
    d = d[(d["bb0"] > 0) & (d["ba0"] < 100) & (d["pm_silence"] < 2.0) & (d["lag_pmfeed"] < 0.5)]
    clock, hz = rival_clock(d)
    out = {"rival_clock": clock, "trade_hazard": hz, "hours_regime": hours(), "feature_support": support(),
           "gates_posthoc_unseen": gates()}
    for name, t in out.items():
        t.to_csv(DIR / f"{name}.csv", index=False)
        print(f"\n### {name}\n")
        print(md(t, 3))


if __name__ == "__main__":
    main()
