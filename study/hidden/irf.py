"""Reaction latency: how the leaders' fill rate responds to Binance book events (impulse
response), on venue clocks (Binance stamp T -> CLOB print stamp).

    nice -n 10 python3 study/hidden/irf.py

Events, per 20 ms bucket of the Binance stream: perp mid change (any tick), perp microprice change
>= 0.02 bp, spot mid change (spot bookTicker has no venue stamp: receipt - median trade lag), spot
trade price move >= 0.05 bp (trade stamp T). Polymarket holds taker orders 150 ms before matching
(docs changelog, since 2026-09-04), so print - event = network + decision + 150 ms; excess fills
< 150 ms after an event were sent before it.
For each event, taker buys of A, B and all other takers in all 5m markets at lags -1..+1.5 s in 10 ms bins, split by
same / opposite side to the event's direction. Lift = count / (rate * bin * events / 2).
Latency of the excess: percentiles of the same-side excess over the baseline within 0-1 s.
Also isolated perp mid ticks (no other tick within 1 s before): first same-side fill delay.
Writes data/out/hidden/irf.csv and irf.md."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import series  # noqa: E402
from attrib import A, B, CACHE, ROOT  # noqa: E402

BINS = np.round(np.arange(-1.0, 1.5001, 0.01), 3)
OUT = ROOT / "data" / "out" / "hidden"


def events(t: np.ndarray, x: np.ndarray, thr: float) -> tuple[np.ndarray, np.ndarray]:
    """Bucket a log-price series (bp) in 20 ms; events where the bucket-end value moved >= thr."""
    o = np.argsort(t, kind="stable")
    t, x = t[o], x[o]
    g = np.floor(t / 0.02).astype(np.int64)
    last = pd.Series(x).groupby(g).last()
    dx = last.diff().dropna()
    ev = dx[dx.abs() >= thr]
    return (ev.index.to_numpy() + 1) * 0.02, np.sign(ev.to_numpy())


def lag_hist(et, es, ft, fd):
    same = np.zeros(len(BINS) - 1)
    opp = np.zeros(len(BINS) - 1)
    lo, hi = np.searchsorted(ft, et + BINS[0]), np.searchsorted(ft, et + BINS[-1])
    for i in np.flatnonzero(hi > lo):
        lag, sg = ft[lo[i]:hi[i]] - et[i], fd[lo[i]:hi[i]] * es[i]
        same += np.histogram(lag[sg > 0], BINS)[0]
        opp += np.histogram(lag[sg < 0], BINS)[0]
    return same, opp


def first_delay(et, es, ft, fd, iso: np.ndarray) -> np.ndarray:
    out = []
    for i in np.flatnonzero(iso):
        j = np.searchsorted(ft, et[i])
        while j < len(ft) and ft[j] - et[i] <= 1.0:
            if fd[j] == es[i]:
                out.append(ft[j] - et[i])
                break
            j += 1
    return np.array(out)


def main() -> None:
    fl = pd.read_pickle(CACHE / "fills_5m.pkl")
    fl = fl[fl["buy"] == 1].sort_values("ts")
    acc: dict = {}
    delays: dict = {}
    secs = 0
    for h in sorted(int(p.stem) for p in (CACHE / "prep").glob("*.pkl")):
        d = series.load(h)
        if "perp_bk" not in d or not len(d["perp_bk"]):
            continue
        secs += 3600
        pb = d["perp_bk"][lambda x: (x["ts"] >= h * 3600) & (x["ts"] < (h + 1) * 3600)]
        sb = d["spot_bk"]
        lag_spot = float(np.median(d["spot_tr"]["t"] - d["spot_tr"]["ts"]))
        sbt = sb["t"].to_numpy() - lag_spot
        keep = (sbt >= h * 3600) & (sbt < (h + 1) * 3600)
        evs = {
            "perp mid tick": events(pb["ts"].to_numpy(), 1e4 * np.log((pb["bid"] + pb["ask"]) / 2).to_numpy(), 1e-6),
            "perp micro >= 0.02 bp": events(pb["ts"].to_numpy(), 1e4 * np.log(
                (pb["bid"] * pb["aq"] + pb["ask"] * pb["bq"]) / (pb["aq"] + pb["bq"])).to_numpy(), 0.02),
            "spot mid tick": events(sbt[keep], 1e4 * np.log((sb["bid"] + sb["ask"]) / 2).to_numpy()[keep], 1e-6),
            "spot trade move >= 0.05 bp": events(d["spot_tr"]["ts"].to_numpy(),
                                                 1e4 * np.log(d["spot_tr"]["px"].to_numpy()), 0.05),
        }
        hr = fl[(fl["ts"] >= h * 3600) & (fl["ts"] < (h + 1) * 3600)]
        for who, f in (("A", hr[hr["wallet"] == A]), ("B", hr[hr["wallet"] == B]),
                       ("other takers", hr[~hr["wallet"].isin([A, B])])):
            ft, fd = f["ts"].to_numpy(), f["d"].to_numpy()
            for name, (et, es) in evs.items():
                s, o = lag_hist(et, es, ft, fd)
                a = acc.setdefault((name, who), [0, 0, 0, 0])
                acc[(name, who)] = [a[0] + s, a[1] + o, a[2] + len(et), a[3] + len(ft)]
            et, es = evs["perp mid tick"]
            iso = np.r_[True, np.diff(et) > 1.0]
            delays.setdefault(who, []).append(first_delay(et, es, ft, fd, iso))
        print("hour", h, flush=True)
    rows, lines = [], ["# Reaction latency (venue clocks: Binance T -> CLOB print)\n",
                       "| event | who | events | peak lag ms | lift at peak | excess p10 / p50 / p90 ms | "
                       "excess < 150 ms (sent before the event) | share of fills in excess |",
                       "|---|---|---|---|---|---|---|---|"]
    c = (BINS[:-1] * 1000).round().astype(int)
    for (name, who), (s, o, ne, nf) in acc.items():
        base = nf / secs * 0.01 * ne / 2
        for i in range(len(c)):
            rows.append((name, who, c[i], s[i] / base, o[i] / base))
        win = (c >= 0) & (c < 1000)
        ex = np.clip(s[win] - base, 0, None)
        cdf = np.cumsum(ex) / ex.sum()
        pct = [c[win][np.searchsorted(cdf, q)] for q in (0.1, 0.5, 0.9)]
        k = int(np.argmax(s))
        early = ex[c[win] < 150].sum() / ex.sum()
        lines.append(f"| {name} | {who} | {ne} | {c[k]} | {s[k] / base:.0f}x | {pct[0]} / {pct[1]} / {pct[2]} | "
                     f"{early:.2f} | {ex.sum() / nf:.3f} |")
    lines.append("\nIsolated perp mid ticks (none in the prior 1 s): delay to the first same-side fill within 1 s\n")
    for who in delays:
        dl = np.concatenate(delays[who]) * 1000
        lines.append(f"- {who}: n {len(dl)}, p5 {np.percentile(dl, 5):.0f}, p25 {np.percentile(dl, 25):.0f}, "
                     f"median {np.median(dl):.0f}, p75 {np.percentile(dl, 75):.0f} ms; "
                     f"share within 200-350 ms {np.mean((dl >= 200) & (dl < 350)):.2f}")
    pd.DataFrame(rows, columns=["event", "who", "lag_ms", "lift_same", "lift_opp"]).to_csv(OUT / "irf.csv", index=False)
    (OUT / "irf.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
