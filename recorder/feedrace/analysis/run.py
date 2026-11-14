"""Analyse one feed-race run: python3 recorder/feedrace/analysis/run.py data/cache/feedrace/<label>

Parses (cached), then (a) id race across Binance connections, (b) per-move race across venues,
(c) venue-time-to-receipt, plus cross-correlation lead vs the baseline.
Optional 2nd arg: a UTC window for the move/PM sections, e.g. 13:30-15:00.
Writes data/out/feedrace/<label>[-<window>].json and prints the headline tables."""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import ids  # noqa: E402
import latency  # noqa: E402
import moves  # noqa: E402
import pmresp  # noqa: E402
import venueclock  # noqa: E402
import xcorr  # noqa: E402
from parse import parse_stream  # noqa: E402
from signals import all_signals  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
THRESHOLDS = (5.0, 10.0, 20.0)


def events(run: Path) -> dict:
    """Per feed: connects (with remote ips), errors, skips (e.g. SBE without a key)."""
    out: dict = {}
    for f in sorted(run.glob("events-*.jsonl")):
        for e in map(json.loads, f.read_text().splitlines()):
            r = out.setdefault(e.get("feed", "?"), {"connect": 0, "error": 0, "ips": [], "notes": []})
            k = e.get("kind")
            if k in ("connect", "error"):
                r[k] += 1
            if e.get("ip") and e["ip"] not in r["ips"]:
                r["ips"].append(e["ip"])
            if k == "skip" or (k == "error" and len(r["notes"]) < 3):
                r["notes"].append(e.get("probe") or e.get("err") or e.get("why"))
    return out


def mono_window(run: Path, spec: str | None) -> tuple[int, int] | None:
    """'13:30-15:00' (UTC, on the run's first day) -> CLOCK_MONOTONIC ns range."""
    if not spec:
        return None
    from parse import load
    c = load(run, "spot_comb_a")
    off = int(np.median(c["wall"] - c["mono"]))
    day = int(c["wall"][0] // 86_400_000_000_000 * 86_400_000_000_000)
    hm = [tuple(map(int, x.split(":"))) for x in spec.split("-")]
    return tuple(day + (h * 3600 + m * 60) * 10**9 - off for h, m in hm)


def main(run: Path, spec: str | None = None) -> None:
    names = sorted({p.name.rsplit("-", 1)[0] for p in run.glob("*.tsv.gz")})
    with ProcessPoolExecutor(6) as ex:
        list(ex.map(parse_stream, [run] * len(names), names))
    names = [n for n in names if (run / "parsed" / f"{n}.npz").stat().st_size > 400]
    res = {"run": run.name, "meta": json.loads((run / "meta.json").read_text()),
           "events": events(run)}
    res["a_ids"] = ids.run_all(run)
    sigs = all_signals(run, mono_window(run, spec))
    res["span_h"] = round((max(t[-1] for t, _ in sigs.values() if len(t))
                           - min(t[0] for t, _ in sigs.values() if len(t))) / 3.6e12, 3)
    res["b_moves"] = {f"{x:g}": moves.race(sigs, x) for x in THRESHOLDS}
    res["b_venueclock"] = {f"{x:g}": venueclock.split(sigs, x) for x in THRESHOLDS}
    if (run / "parsed" / "pm.npz").exists():
        book = pmresp.Book(run)
        allsig = list(sigs) + list(moves.COMPOSITES)
        res["d_pm_own"] = {f"{x:g}": pmresp.own(book, sigs, x) for x in THRESHOLDS}
        res["d_pm_move"] = {f"{x:g}": pmresp.per_move(book, sigs, x, allsig) for x in THRESHOLDS}
    res["b_xcorr_vs_BASE_spot_comb_a"] = xcorr.lead(sigs, "BASE_spot_comb_a")
    res["c_latency"] = {n: latency.stream(run, n) for n in names}
    res["c_chrony"] = latency.chrony(run)
    tag = "-" + spec.replace(":", "").replace("-", "_") if spec else ""
    res["window_utc"] = spec
    out = ROOT / "data/out/feedrace" / f"{run.name}{tag}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1, default=float))
    print("wrote", out)
    for x, r in res["b_moves"].items():
        print(f"\n## moves >= ${x}: {r['moves']}")
        print("signal | fired | first | delay p50 | gain vs spot_comb_a p25/p50/p75 | vs bn_best p50 | share earlier than bn_best")
        for n, s in r["signals"].items():
            g, gb = s["gain_vs_BASE_spot_comb_a_ms"], s["gain_vs_bn_best_ms"]
            print(n, s["fired"], s["first_share"], s["delay_vs_first_venue_ms"].get("p50"),
                  g.get("p25"), g.get("p50"), g.get("p75"), gb.get("p50"),
                  s["earlier_than_bn_best_share"], sep=" | ")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve(), sys.argv[2] if len(sys.argv) > 2 else None)
