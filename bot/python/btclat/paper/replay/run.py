"""Paper run on recorded hours: the live engine (state, arms, paper fills) fed from a
recording instead of sockets, at live semantics (no grid quantization).

    nice -n 10 python3 -m btclat.paper.replay.run --hours 497697,497698 [--root data/live]
        [--run replay-497697] [--latency-ms 0]

The first hour of --hours is warm-up only (settlement needs 300 s of spot trades before a
market's start; markets starting in it are traded only if the history covers them).
Writes data/paper/<run>/orders-*.tsv.gz and settle-*.tsv.gz like a live run."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from recorder.live.sink import Sink

from ..engine.core import Engine
from ..model.load import ValueModel
from . import source

PAPER = source.LIVE.parent / "paper"
OUTCOMES = source.LIVE.parent / "cache" / "strategy" / "outcomes.json"


def gaps(root: Path, hours) -> dict[str, list]:
    """CLOB socket errors -> [error t, reconnect t] per market slug (recorder events)."""
    out: dict[str, list] = {}
    for t, raw in source.lines(root, "events", hours):
        j = json.loads(raw)
        feed = j.get("feed", "")
        if not feed.startswith("clob:"):
            continue
        g = out.setdefault(feed[5:], [])
        if j["kind"] == "error" and (not g or g[-1][1] is not None):
            g.append([t, None])
        elif j["kind"] == "connect" and g and g[-1][1] is None:
            g[-1][1] = t
    return out


def replay(root: Path, hours, run: str, L: float = 0.0, model: str = "v1_L0") -> dict:
    out = PAPER / run
    orders, settle = Sink("orders", root=out, flush_s=1.0), Sink("settle", root=out, flush_s=0)
    eng = Engine(ValueModel(model), orders, run, L=L)
    gp = gaps(root, hours)
    mk = source.markets(root, hours)
    t0, n = time.time(), 0
    for ev in source.events(root, hours, quantize=False, mk=mk):
        eng.on_event(ev)
        if ev[0] == "mk":
            eng.world.mkts[ev[2]["slug"]].gaps = gp.get(ev[2]["slug"], [])
        n += 1
    eng.paper.flush()
    oc = json.loads(OUTCOMES.read_text()) if OUTCOMES.exists() else {}
    for s, m in mk.items():
        if s in oc:
            settle.write(int(m["end"] * 1e9), json.dumps({"slug": s, "outcome": oc[s], "end": m["end"]}))
    st = eng.stats(reset=False) | {"n_events": n, "wall_s": time.time() - t0, "hours": list(hours), "root": str(root)}
    Sink.close_all()
    (out / "replay.json").write_text(json.dumps(st, indent=1))
    return st


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", required=True, help="comma list of epoch hours; the first is warm-up")
    ap.add_argument("--root", default=str(source.LIVE))
    ap.add_argument("--run", default=None)
    ap.add_argument("--latency-ms", type=float, default=0.0)
    ap.add_argument("--model", default="v1_L0")
    a = ap.parse_args()
    hours = [int(h) for h in a.hours.split(",")]
    run = a.run or f"replay-{hours[1] if len(hours) > 1 else hours[0]}"
    print(json.dumps(replay(Path(a.root), hours, run, a.latency_ms / 1000, a.model), indent=1))


if __name__ == "__main__":
    main()
