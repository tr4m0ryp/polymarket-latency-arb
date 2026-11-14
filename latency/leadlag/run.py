"""Live lead and stale-depth study over the recorder's logs.

    python3 latency/leadlag/run.py

Writes data/out/live/{events,baseline}.csv, summary.json and reports/live-lead.md."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import chain  # noqa: E402
import event  # noqa: E402
import load  # noqa: E402
import spot  # noqa: E402
from report import write_report  # noqa: E402

OUT = load.ROOT / "data" / "out" / "live"
THRESHOLDS = (1.0, 2.0, 3.0, 5.0)


def baseline_times(tr: pd.DataFrame, every: float = 5.0, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    lag = float((tr["t"] - tr["ts"]).median())
    T0 = np.arange(tr["ts"].iloc[0] + 310, tr["ts"].iloc[-1] - 10, every)
    T0 = T0 + rng.uniform(0, every, len(T0))
    return pd.DataFrame({"T0": T0, "R0": T0 + lag, "d": rng.choice([-1.0, 1.0], len(T0)),
                         "move_bp": np.nan, "s_before": spot.price_at(tr, T0 - 1),
                         "s_after": spot.price_at(tr, T0)})


def gaps() -> dict[str, list[tuple[float, float]]]:
    """Per market slug: (error, next connect) windows from the recorder's events."""
    out, open_err = {}, {}
    for t, raw in load._lines_all("events"):
        j = json.loads(raw)
        feed = j.get("feed", "")
        if not feed.startswith("clob:"):
            continue
        slug = feed[5:]
        if j["kind"] == "error":
            open_err.setdefault(slug, t)
        elif j["kind"] == "connect" and slug in open_err:
            out.setdefault(slug, []).append((open_err.pop(slug), t))
    return out


def main() -> None:
    tr = spot.trades(load.table("binance"))
    cl = load.table("chainlink")
    mk = load.markets()
    clob = {f: load.table(f"clob_{f}") for f in ("5m", "15m")}
    sets = {f"burst{thr:g}": spot.bursts(tr, thr) for thr in THRESHOLDS}
    sets["baseline"] = baseline_times(tr)
    res = {k: [] for k in sets}
    gp = gaps()
    for m in mk.to_dict("records"):
        rows = clob[m["fam"]]
        rows = rows[rows["market"] == m["condition_id"]]
        if len(rows) < 100:
            continue
        for k, ev in sets.items():
            res[k].append(event.study(m, rows, tr, ev, gp.get(m["slug"], [])))
    OUT.mkdir(parents=True, exist_ok=True)
    frames = {}
    for k, parts in res.items():
        df = pd.concat([p for p in parts if len(p)], ignore_index=True) if any(len(p) for p in parts) else pd.DataFrame()
        df["set"] = k
        frames[k] = df
    allev = pd.concat(frames.values(), ignore_index=True)
    allev.to_csv(OUT / "events.csv.gz", index=False)
    kept = allev.groupby("set")["ok"].mean().round(3).to_dict()
    allev = allev[allev["ok"]].reset_index(drop=True)
    meta = {"binance_recv_delay_s": float((tr["t"] - tr["ts"]).median()),
            "hours": float((tr["ts"].iloc[-1] - tr["ts"].iloc[0]) / 3600),
            "markets": {f: int((mk["fam"] == f).sum()) for f in ("5m", "15m")},
            "clob_recv_delay_s": {f: float((c["t"] - c["ts"]).median()) for f, c in clob.items()},
            "chainlink": chain.lead(tr, cl), "kept_share": kept,
            "gaps": {k: len(v) for k, v in gp.items()}}
    (OUT / "summary.json").write_text(json.dumps(meta, indent=1))
    write_report(allev, meta, OUT, load.ROOT / "reports" / "live-lead.md")


if __name__ == "__main__":
    main()
