"""Hypothesis 3: does another venue (Coinbase, OKX swap, Bybit linear) or Binance perp trades
explain the leaders' fills beyond the Binance perp and spot books? Side-recorder hours only.

    nice -n 10 python3 study/hidden/venue_cmp.py

(1) single-rule side accuracy of each feed's microprice / taker flow in the trigger window, on all
fills and on the fills where the Binance books are silent, disagree or point the other way;
(2) impulse response of fills to each venue's mid ticks (peak lag and lift, venue clocks);
(3) lead of each venue's mid ticks over the Binance perp (median signed gap to the nearest
same-direction perp tick within 0.5 s); (4) side AUC, Binance books vs Binance + other venues,
cross-validated by hour (GroupKFold). Writes data/out/hidden/venues.md."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import series  # noqa: E402
import window  # noqa: E402
from attrib import A, B, CACHE, ROOT  # noqa: E402
from irf import BINS, events, lag_hist  # noqa: E402

FEEDS = ["perp_micro", "spot_micro", "perp_flow", "spot_flow", "okx_micro", "okx_flow",
         "bybit_micro", "bybit_flow", "coinbase_micro", "coinbase_flow"]


def acc(v: pd.Series) -> str:
    v = v.dropna()
    nz = v[v != 0]
    return f"{(nz > 0).mean():.3f} / {len(nz) / max(len(v), 1):.2f}" if len(nz) else "n/a"


def cv_auc(x: pd.DataFrame, cols: list[str]) -> float:
    """Out-of-fold side AUC, folds = hours; features in the Up frame."""
    X = x[cols].mul(x["d"], axis=0)
    y = (x["d"] > 0).astype(int).to_numpy()
    groups = (x["ts"] // 1800).astype(int).to_numpy()  # half-hour folds
    pred = np.full(len(x), np.nan)
    for tr, te in GroupKFold(n_splits=min(5, len(set(groups)))).split(X, y, groups):
        clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=7,
                                             l2_regularization=1.0, random_state=0).fit(X.iloc[tr], y[tr])
        pred[te] = clf.predict_proba(X.iloc[te])[:, 1]
    return roc_auc_score(y, pred)


def main() -> None:
    fl = pd.read_pickle(CACHE / "fills_5m.pkl")
    fl = fl[fl["buy"] == 1].sort_values("ts")
    hours = [int(p.stem) for p in sorted((CACHE / "prep").glob("*.pkl"))]
    rows, irf, lead, secs = [], {}, {}, 0
    for h in hours:
        d = series.load(h)
        if "okx_bk" not in d:
            continue
        s = series.build(d)
        lo = max(h * 3600, float(d["okx_bk"]["ts"].min()) + 1)
        f = fl[fl["wallet"].isin([A, B]) & (fl["ts"] >= lo) & (fl["ts"] < (h + 1) * 3600)]
        if not len(f):
            continue
        secs += (h + 1) * 3600 - lo
        w = window.binance(s, f["ts"].to_numpy(), f["d"].to_numpy())
        rows.append(f.assign(**{k: w[k] for k in w}))
        pk = (d["perp_bk"]["ts"] >= lo).to_numpy()
        pt, ps = events(d["perp_bk"]["ts"].to_numpy()[pk],
                        1e4 * np.log((d["perp_bk"]["bid"] + d["perp_bk"]["ask"]) / 2).to_numpy()[pk], 1e-6)
        for v in ("perp", "okx", "bybit", "coinbase"):
            b = d[f"{v}_bk"] if v != "perp" else d["perp_bk"][pk]
            et, es = events(b["ts"].to_numpy(), 1e4 * np.log((b["bid"] + b["ask"]) / 2).to_numpy(), 1e-6)
            for who, wal in (("A", A), ("B", B)):
                x = f[f["wallet"] == wal]
                sm, op = lag_hist(et, es, x["ts"].to_numpy(), x["d"].to_numpy())
                a = irf.setdefault((v, who), [0, 0, 0, 0])
                irf[(v, who)] = [a[0] + sm, a[1] + op, a[2] + len(et), a[3] + len(x)]
            j = np.searchsorted(pt, et)
            gaps = []
            for i, jj in enumerate(j):
                cand = [k for k in (jj - 1, jj) if 0 <= k < len(pt) and ps[k] == es[i] and abs(pt[k] - et[i]) < 0.5]
                if cand:
                    k = min(cand, key=lambda k: abs(pt[k] - et[i]))
                    gaps.append(pt[k] - et[i])
            lead.setdefault(v, []).extend(gaps)
        print("hour", h, len(f), flush=True)
    x = pd.concat(rows)
    x["who"] = np.where(x["wallet"] == A, "A", "B")
    comb = np.sign(x["perp_micro_trig"]) + np.sign(x["spot_micro_trig"].fillna(0))
    x["binance_miss"] = comb <= 0
    lines = [f"# Other venues vs the Binance books ({secs / 3600:.1f} h of side-recorder data, "
             f"{len(x)} leader fills)\n", "Side accuracy / coverage, trigger window (0.21-0.33 s before the print):\n",
             "| feed | A all | A Binance-miss | B all | B Binance-miss |", "|---|---|---|---|---|"]
    for k in FEEDS:
        col = f"{k}_trig"
        if col not in x:
            continue
        cells = [acc(g[col]) for who in "AB" for g in (x[x["who"] == who], x[(x["who"] == who) & x["binance_miss"]])]
        lines.append(f"| {k} | " + " | ".join(cells) + " |")
    p, q = np.sign(x["perp_micro_trig"]), np.sign(x["spot_micro_trig"].fillna(0))
    agree = (p + q) != 0
    for name, fb in (("Binance only", np.zeros(len(x))), ("Binance, else Bybit", np.sign(x["bybit_micro_trig"].fillna(0))),
                     ("Binance, else Bybit, else OKX", np.where(x["bybit_micro_trig"].fillna(0) != 0,
                                                               np.sign(x["bybit_micro_trig"].fillna(0)),
                                                               np.sign(x["okx_micro_trig"].fillna(0))))):
        r = pd.Series(np.where(agree & (p * q >= 0), np.sign(p + q), fb), index=x.index)
        cells = [f"{(r[(x['who'] == w) & (r != 0)] > 0).mean():.3f} / {(r[x['who'] == w] != 0).mean():.2f}" for w in "AB"]
        lines.append(f"- rule '{name}': A {cells[0]}, B {cells[1]} (accuracy / coverage)")
    lines.append(f"\nBinance-miss fills (perp + spot book silent, split or opposite): "
                 f"A {x[x['who'] == 'A']['binance_miss'].mean():.3f}, B {x[x['who'] == 'B']['binance_miss'].mean():.3f}\n")
    wins = ("trig", "pre", "post", "wide")
    binance = [f"{k}_{w}" for k in ("perp_micro", "perp_mid", "spot_micro", "spot_mid", "spot_flow") for w in wins]
    other = [f"{k}_{w}" for k in ("okx_micro", "okx_flow", "bybit_micro", "bybit_flow", "coinbase_micro",
                                  "coinbase_flow", "perp_flow") for w in wins]
    lines += ["Side AUC, out-of-fold by half hour:\n", "| features | A | B |", "|---|---|---|"]
    per = {v: [c for c in other if c.startswith(v)] for v in ("okx", "bybit", "coinbase", "perp_flow")}
    for name, cols in (("Binance books", binance), ("other venues + perp trades", other),
                       ("Binance + OKX", binance + per["okx"]), ("Binance + Bybit", binance + per["bybit"]),
                       ("Binance + Coinbase", binance + per["coinbase"]),
                       ("Binance + perp trades", binance + per["perp_flow"]),
                       ("Bybit alone", per["bybit"]), ("Binance + other venues", binance + other)):
        cells = [f"{cv_auc(x[x['who'] == w], [c for c in cols if c in x]):.3f}" for w in "AB"]
        lines.append(f"| {name} | {cells[0]} | {cells[1]} |")
    lines += ["", "Impulse response to each venue's mid ticks (venue clocks):\n",
              "| venue | who | ticks | peak lag ms | lift at peak |", "|---|---|---|---|---|"]
    c = (BINS[:-1] * 1000).round().astype(int)
    for (v, who), (sm, op, ne, nf) in irf.items():
        base = nf / secs * 0.01 * ne / 2
        k = int(np.argmax(sm))
        lines.append(f"| {v} | {who} | {ne} | {c[k]} | {sm[k] / max(base, 1e-9):.0f}x |")
    lines += ["\nLead over the Binance perp (perp tick time minus venue tick time, same direction, |gap| < 0.5 s; "
              "positive = venue first):\n"]
    for v, g in lead.items():
        g = np.array(g) * 1000
        lines.append(f"- {v}: matched {len(g)}, median {np.median(g):.0f} ms, p25 {np.percentile(g, 25):.0f}, "
                     f"p75 {np.percentile(g, 75):.0f}, venue first {np.mean(g > 0):.2f}")
    (ROOT / "data" / "out" / "hidden" / "venues.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
