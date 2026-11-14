"""How much earlier does a USD-M perp trigger fire than the spot trigger, on Binance's clocks?

Spot onset T0: first spot trade whose trailing 1 s move reaches 1 bp (latency/leadlag/spot.bursts,
the onset every live study uses). Perp onset: first perp bookTicker update (stamp T) within
[T0 - 1 s, T0 + 0.5 s] whose trailing 1 s mid move reaches `thr` bp in the same direction.
lead = T0 - perp onset (positive: the perp fired first). Both stamps are Binance matching-engine
times in Tokyo, so the result does not depend on where we listen; it is the head start an
order could get by triggering on the perp. Also: perp onsets per hour that no spot burst
follows within 1 s (false-alarm rate of the earlier trigger).

    python3 latency/infra/perp_lead.py <hour> [...]   (hour = unix_ts // 3600; run-2 hours)"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "latency" / "leadlag"))
import load  # noqa: E402
import spot  # noqa: E402

OUT = ROOT / "data/out/infra/perp_lead.json"
THRS = (0.5, 0.75, 1.0)


def _perp(hours: list[int]) -> pd.DataFrame:
    rows = []
    for p in [p for h in hours for p in load.LIVE.glob(f"*/binance_fut-{h}.tsv.gz")]:
        for _, raw in load._lines(p):
            d = json.loads(raw)["data"]
            if d.get("e") == "bookTicker":
                rows.append((d["T"] / 1e3, (float(d["b"]) + float(d["a"])) / 2))
    return pd.DataFrame(rows, columns=["ts", "px"]).sort_values("ts", kind="stable").reset_index(drop=True)


def _onsets(ts: np.ndarray, px: np.ndarray, thr: float) -> tuple[np.ndarray, np.ndarray]:
    j = np.searchsorted(ts, ts - 1.0, side="left")
    r = 1e4 * np.log(px / px[j])
    return r, np.flatnonzero(np.abs(r) >= thr)


def study(hours: list[int]) -> dict:
    bn = pd.concat([load._binance(p) for h in hours for p in load.LIVE.glob(f"*/binance-{h}.tsv.gz")])
    b = spot.bursts(spot.trades(bn), 1.0)
    fu = _perp(hours)
    ts, px = fu["ts"].to_numpy(), fu["px"].to_numpy()
    b = b[(b["T0"] > ts[0] + 2) & (b["T0"] < ts[-1] - 1)]
    out: dict = {"hours": hours, "spot_bursts": int(len(b)), "by_thr": {}}
    for thr in THRS:
        r, hit = _onsets(ts, px, thr)
        hit_ts = ts[hit]
        leads = []
        for e in b.itertuples():
            lo, hi = np.searchsorted(hit_ts, [e.T0 - 1.0, e.T0 + 0.5])
            k = [i for i in hit[lo:hi] if np.sign(r[i]) == e.d]
            leads.append(e.T0 - ts[k[0]] if k else np.nan)
        lead = np.asarray(leads)
        ok = lead[~np.isnan(lead)]
        # false alarms: perp onsets (3 s refractory) with no spot burst in [t - 0.5, t + 1.0]
        ons, last = [], -np.inf
        for i in hit:
            if ts[i] - last >= 3.0:
                ons.append((ts[i], np.sign(r[i])))
                last = ts[i]
        bt, bd = b["T0"].to_numpy(), b["d"].to_numpy()
        fa = sum(1 for t, d in ons if not np.any((bt > t - 0.5) & (bt < t + 1.0) & (bd == d)))
        span_h = (ts[-1] - ts[0]) / 3600
        out["by_thr"][str(thr)] = {
            "perp_seen_share": round(len(ok) / max(1, len(lead)), 3),
            "perp_first_share": round(float((ok > 0).mean()), 3) if len(ok) else None,
            "lead_ms_p25_p50_p75_p90": [round(1e3 * float(np.percentile(ok, q)), 1) for q in (25, 50, 75, 90)] if len(ok) else None,
            "perp_onsets_per_h": round(len(ons) / span_h, 1),
            "false_alarm_share": round(fa / max(1, len(ons)), 3),
        }
    return out


def main(hours: list[int]) -> None:
    res = study(hours)
    print(json.dumps(res, indent=1))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main([int(h) for h in sys.argv[1:]])
