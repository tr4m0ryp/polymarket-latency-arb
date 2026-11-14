"""Hypothesis 4: copying other bots, fixed cadence, bursts. Also the fastest wallets.

    nice -n 10 python3 study/hidden/peers.py

(1) Lag from the latest same-side fill of the other leader (and of anyone else) to each leader
fill, and the Binance-trigger accuracy of leader fills by that lag (a copy would sit >= 150 ms
after the copied print because taker orders are held 150 ms). (2) Shared isolated perp ticks:
print gap A - B and A / B - fast third parties. (3) Cadence: phase within the wall-clock second
(chi2, 10 bins), inter-fill gaps, burst openers vs follow-ups. (4) Impulse-response peak per
wallet for the 25 most active takers. Writes data/out/hidden/peers.md."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import series  # noqa: E402
from attrib import A, B, CACHE, ROOT  # noqa: E402
from irf import BINS, events, lag_hist  # noqa: E402

FAST = ["0x0ca4e9d27ff826a109ecbf74754fb66b93f277a6", "0x764fd57b0b885cbeada5a119cdf0a113ee4ec347"]


def since_same_side(x: pd.DataFrame, y: pd.DataFrame) -> np.ndarray:
    out = np.full(len(x), np.nan)
    for (m, d), idx in x.groupby(["market", "d"]).groups.items():
        ys = np.sort(y.loc[(y["market"] == m) & (y["d"] == d), "ts"].to_numpy())
        t = x.loc[idx, "ts"].to_numpy()
        i = np.searchsorted(ys, t, "left")
        out[x.index.get_indexer(idx)] = t - np.r_[-np.inf, ys][i]
    return out


def tick_tables(fl: pd.DataFrame, wallets: list[str]):
    """First same-side fill 0.15-0.6 s after each isolated perp tick, per wallet; IRF per wallet."""
    first = {w: [] for w in wallets}
    irf, secs = {}, 0
    for h in sorted(int(p.stem) for p in (CACHE / "prep").glob("*.pkl")):
        d = series.load(h)
        if "perp_bk" not in d or not len(d["perp_bk"]):
            continue
        secs += 3600
        pb = d["perp_bk"][lambda x: (x["ts"] >= h * 3600) & (x["ts"] < (h + 1) * 3600)]
        et, es = events(pb["ts"].to_numpy(), 1e4 * np.log((pb["bid"] + pb["ask"]) / 2).to_numpy(), 1e-6)
        iso = np.r_[True, np.diff(et) > 1.0]
        hr = fl[(fl["ts"] >= h * 3600) & (fl["ts"] < (h + 1) * 3600)]
        for w in wallets:
            x = hr[hr["wallet"] == w]
            ts, dd = x["ts"].to_numpy(), x["d"].to_numpy()
            s, o = lag_hist(et, es, ts, dd)
            a = irf.get(w, [0, 0, 0])
            irf[w] = [a[0] + s, a[1] + len(et), a[2] + len(x)]
            v = np.full(iso.sum(), np.nan)
            for j, (e, sg) in enumerate(zip(et[iso], es[iso])):
                lo, hi = np.searchsorted(ts, e + 0.15), np.searchsorted(ts, e + 0.6)
                k = np.flatnonzero(dd[lo:hi] == sg)
                if len(k):
                    v[j] = ts[lo + k[0]] - e
            first[w].append(v)
    return {w: np.concatenate(v) for w, v in first.items()}, irf, secs


def main() -> None:
    fl = pd.read_pickle(CACHE / "fills_5m.pkl")
    fl = fl[fl["buy"] == 1].sort_values("ts").reset_index(drop=True)
    feat = pd.read_pickle(CACHE / "feat.pkl")
    feat = feat[feat["perp_micro_trig"].notna()].sort_values("ts")
    comb = np.sign(feat["perp_micro_trig"]) + np.sign(feat["spot_micro_trig"].fillna(0))
    L = ["# Copying, cadence and the fastest wallets\n", "## Lag from the latest same-side fill of ...\n",
         "| leader after | < 50 ms | 50-150 | 150-300 | 300-600 | Binance trigger acc / cov at 150-300 ms |",
         "|---|---|---|---|---|---|"]
    for who, w, peer in (("A", A, B), ("B", B, A)):
        g = feat[feat["wallet"] == w]
        for pname, y in (("other leader", fl[fl["wallet"] == peer]), ("anyone else", fl[~fl["wallet"].isin([A, B])])):
            lag = since_same_side(g, y) * 1000
            cells = [f"{np.mean((lag >= a) & (lag < b)):.3f}" for a, b in ((0, 50), (50, 150), (150, 300), (300, 600))]
            hump = (lag >= 150) & (lag < 300)
            c = comb[g.index][hump]
            cells.append(f"{(c[c != 0] > 0).mean():.2f} / {(c != 0).mean():.2f} (n {hump.sum()})")
            L.append(f"| {who} after {pname} | " + " | ".join(cells) + " |")
    wallets = list(dict.fromkeys([A, B] + FAST + list(fl["wallet"].value_counts().head(25).index)))
    first, irf, secs = tick_tables(fl, wallets)
    L += ["\n## Shared isolated perp ticks: print gap (ms)\n", "| pair | n | p25 | median | p75 | abs < 20 ms |",
          "|---|---|---|---|---|---|"]
    for a_, b_, name in ((A, B, "A - B"), (A, FAST[0], "A - 0x0ca4e9d2"), (B, FAST[0], "B - 0x0ca4e9d2"),
                         (A, FAST[1], "A - 0x764fd57b"), (B, FAST[1], "B - 0x764fd57b")):
        v = (first[a_] - first[b_]) * 1000
        v = v[~np.isnan(v)]
        if len(v) > 5:
            L.append(f"| {name} | {len(v)} | {np.percentile(v, 25):.0f} | {np.median(v):.0f} | "
                     f"{np.percentile(v, 75):.0f} | {np.mean(np.abs(v) < 20):.2f} |")
    L += ["\n## Cadence\n"]
    for who, w in (("A", A), ("B", B)):
        x = fl[fl["wallet"] == w]
        h = np.histogram(x["ts"] % 1.0, bins=10)[0]
        gap = x.groupby("market")["ts"].diff().dropna()
        mode = np.histogram(gap[gap < 3], bins=np.arange(0, 3.01, 0.1))
        g = feat[feat["wallet"] == w].copy()
        g["gap"] = g.groupby("market")["ts"].diff()
        g["same"] = g.groupby("market")["d"].shift() == g["d"]
        weak = (g["perp_micro_trig"].abs() < 1e-4) & (g["spot_micro_trig"].fillna(0).abs() < 1e-5)
        op, fu = g["gap"].isna() | (g["gap"] > 5), (g["gap"] >= 0.2) & (g["gap"] < 0.6)
        L.append(f"- {who}: phase chi2 {((h - h.mean()) ** 2 / h.mean()).sum():.1f} (9 df); modal gap "
                 f"{mode[1][np.argmax(mode[0])]:.1f}-{mode[1][np.argmax(mode[0])] + 0.1:.1f} s; openers (gap > 5 s) "
                 f"{op.mean():.2f} of fills, weak trigger {weak[op].mean():.2f}; follow-ups 0.2-0.6 s {fu.mean():.2f}, "
                 f"weak {weak[fu].mean():.2f}, same side {g.loc[fu, 'same'].mean():.2f}")
    L += ["\n## Impulse-response peak per wallet (perp mid ticks, 25 most active takers)\n",
          "| wallet | fills | peak ms | lift |", "|---|---|---|---|"]
    c = (BINS[:-1] * 1000).round().astype(int)
    rows = []
    for w, (s, ne, nf) in irf.items():
        base = nf / secs * 0.01 * ne / 2
        k = int(np.argmax(s))
        if s[k] / max(base, 1e-9) >= 10:
            rows.append((c[k], w, nf, s[k] / base))
    L += [f"| {w} | {nf} | {pk} | {lift:.0f}x |" for pk, w, nf, lift in sorted(rows)]
    (ROOT / "data" / "out" / "hidden" / "peers.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
