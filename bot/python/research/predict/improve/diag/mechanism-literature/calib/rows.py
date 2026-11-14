"""Frozen 1 s value model (v1_L0, hash-checked, read only) against what it predicts, on the
unseen allowed windows, with the mechanism covariates the model cannot see.

Rows = decision rows where the better side's prediction is >= 2 c and the arm's gates hold
(seen price 0.05-0.95, >= 20 s left). Per row: pred (c), realized best-level value at L = 0
marked 1 s and 10 s after the match (model/derive.py side_values), and
- lag_feed: our perp receipt minus Binance T of the last perp update (feed delay now);
- compress: Binance-T span over receipt span of the last 20 perp updates (> 1 = a backlog
  flushed in a clump, so receipt-clock windows see compressed bursts);
- cvol30, pmsg10 as in events/activity.py; sigma, pm_spr, pm_stale from the table.

    OMP_NUM_THREADS=2 nice -n 10 python3 research/predict/improve/diag/mechanism-literature calib"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd
from scipy.special import ndtri

from research.predict.improve.harness.guard import check_models
from research.predict.model.derive import side_values
from research.predict.model.store import load_model, predict_sides
from .. import PCACHE, SEALED, WORK
from ..data.guard import assert_allowed, market_ids, meta, safe_hours
from ..data.load import Hours

UNSEEN = ("dev3", "test3r1", "ext")


def _at(t, x, q):
    j = np.searchsorted(t, q, side="right") - 1
    return np.where(j >= 0, x[np.clip(j, 0, None)], np.nan), j


def covariates(perp: dict, q: np.ndarray, delta: np.ndarray) -> dict:
    t, T = perp["t"], perp["T"]
    lm = 1e4 * np.log((perp["b"] + perp["a"]) / 2)
    cum = np.cumsum(np.abs(np.diff(lm, prepend=lm[0])))
    Tl, j = _at(t, T, q)
    out = {"lag_feed": np.where(j >= 0, t[np.clip(j, 0, None)] - Tl, np.nan)}
    j0 = np.clip(j - 19, 0, None)
    jj = np.clip(j, 0, None)
    out["compress"] = (T[jj] - T[j0]) / np.maximum(t[jj] - t[j0], 1e-3)
    out["pvol30"] = _at(t, cum, q)[0] - _at(t, cum, q - 30)[0]
    out["cvol30"] = out["pvol30"] * delta
    out["pmsg10"] = (np.searchsorted(t, q) - np.searchsorted(t, q - 10)) / 10
    return out


def one(hrs: Hours, i: int, m: pd.Series, mdl: dict) -> pd.DataFrame:
    start, end = float(m["start"]), float(m["end"])
    assert start < SEALED and end + 35 < SEALED
    with np.load(PCACHE / "tab" / f"{i}.npz") as z:
        tab = pd.DataFrame({k: z[k] for k in z.files})
    pu, pdn = predict_sides(tab, mdl)
    yu, yd = side_values(tab, 0, 1)
    yu10, yd10 = side_values(tab, 0, 10)
    side = np.where(pu >= pdn, 1, -1)
    pred = np.maximum(pu, pdn)
    seen = np.where(side > 0, tab["pm_ba"] / 100, 1 - tab["pm_bb"] / 100)
    ok = (pred >= 0.02) & (seen >= 0.05) & (seen <= 0.95) & (tab["secs_left"].to_numpy() >= 20)
    if not ok.any():
        return pd.DataFrame()
    d = tab.loc[ok, ["t", "sigma", "pm_spr", "pm_stale", "secs_left", "pm_mid", "zs"]].reset_index(drop=True)
    d["side"], d["pred"] = side[ok], pred[ok]
    d["y1"] = np.where(side > 0, yu, yd)[ok]
    d["y10"] = np.where(side > 0, yu10, yd10)[ok]
    zq = ndtri(np.clip(d["pm_mid"].to_numpy(float), 0.02, 0.98))
    delta = 100 * np.exp(-zq ** 2 / 2) / np.sqrt(2 * np.pi) * d["zs"].to_numpy(float) * 1e-4
    perp = hrs.cat(safe_hours(start - 60, end + 35), "fb",
                   lambda c: (c["t"] > start - 60) & (c["t"] < end + 35))
    if perp:
        for k, v in covariates(perp, d["t"].to_numpy(float), delta).items():
            d[k] = v
    d["m"], d["start"] = i, start
    return d


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--windows", default=",".join(UNSEEN))
    ap.add_argument("--tag", default="calib")
    a = ap.parse_args()
    sha = check_models(("v1_L0",))
    ids = market_ids(a.windows.split(","))
    allm = sorted({i for v in ids.values() for i in v})
    win = {i: w for w, v in ids.items() for i in v}
    mt = meta(allm)
    mdl = load_model("v1_L0")
    hrs, parts, t0 = Hours(keep=2), [], time.time()
    for n, i in enumerate(allm):
        d = one(hrs, i, mt.loc[i], mdl)
        if len(d):
            d["window"] = win[i]
            parts.append(d)
        if n % 25 == 0:
            print(f"{n}/{len(allm)} {time.time() - t0:.0f}s", flush=True)
    rows = pd.concat(parts, ignore_index=True)
    assert_allowed(rows["start"], "calib rows")
    WORK.mkdir(parents=True, exist_ok=True)
    rows.to_pickle(WORK / f"{a.tag}.pkl")
    print("rows", len(rows), "markets", rows["m"].nunique(), "model", sha)


if __name__ == "__main__":
    np.seterr(all="ignore")
    main()
