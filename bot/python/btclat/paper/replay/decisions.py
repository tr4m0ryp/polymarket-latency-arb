"""Reference decisions of the Python paper bot for the Rust parity tests (rust/crates/bot replay).

    nice -n 10 python3 -m btclat.paper.replay.decisions --root data/paper/dublin-20261012/raw \
        --hours 497750,497751,497752 [--arm vt_v1_m0.02_trigger] [--out data/cache/rust/<name>]

Runs the paper engine's world and decider (no paper fills) over recorded raw hours, exactly the
event order of replay/run.py, and writes to --out:
  decisions.jsonl   one line per order of the arm: t, slug, side, limit, seen, pred_up, pred_dn
  rows.jsonl        the decision row (every model input before vectorizing) of each value
                    candidate whose leaders' trigger fires (|p_dmic0.1| >= 0.002), with pu, pdn
  model_rows.bin    float64 LE: per model call the up and down input vectors, then sklearn's
                    predict for both; model_rows.json describes the layout
The first hour is warm-up for settlement inputs, as in replay/run.py."""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np

from ..engine.core import Engine
from ..model.load import ValueModel
from . import source

CACHE = source.LIVE.parent / "cache" / "rust"


class Recorder(ValueModel):
    def __init__(self, name: str, cap: int):
        super().__init__(name)
        self.xu, self.xd, self.cap = [], [], cap

    def __call__(self, row: dict) -> tuple[float, float]:
        xu, xd = self.vec.sides(row)
        if len(self.xu) < self.cap:
            self.xu.append(xu.copy())
            self.xd.append(xd.copy())
        return self.tree(xu), self.tree(xd)


class NoPaper:
    def __init__(self, out):
        self.out, self.n, self.jobs = out, {}, []

    def submit(self, o, m, src, t_venue, lat_us) -> None:
        self.out.append({"t": o["t"], "slug": m.meta["slug"], "side": o["side"], "limit": o["limit"],
                         "seen": o["seen"], "pred_up": o["pred_up"], "pred_dn": o["pred_dn"], "src": src})

    def advance(self, now) -> None:
        pass

    def flush(self) -> None:
        pass


def _num(x):
    return None if isinstance(x, float) and not math.isfinite(x) else x


def run(root: Path, hours, arm: str, out: Path, model: str, cap: int) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    vm = Recorder(model, cap)
    orders: list = []
    eng = Engine(vm, None, "parity", arms=[arm])
    eng.paper = NoPaper(orders)
    rows = []
    from ..features import raw
    row_fn = raw.row

    def row_spy(q, c, m):   # the row of every value candidate the trigger lets through
        r = row_fn(q, c, m)
        if abs(r.get("p_dmic0.1", float("nan"))) >= 0.002:
            rows.append({"slug": m.meta["slug"], **{k: _num(v) for k, v in r.items()}})
        return r
    import btclat.paper.arms.decide as dmod
    dmod.row = row_spy
    t0 = time.time()
    n = 0
    for ev in source.events(root, hours, quantize=False):
        eng.on_event(ev)
        n += 1
    dmod.row = row_fn
    with open(out / "decisions.jsonl", "w") as fh:
        for o in orders:
            fh.write(json.dumps(o) + "\n")
    with open(out / "rows.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    xu, xd = np.array(vm.xu), np.array(vm.xd)
    pu, pd_ = vm.sk.predict(xu), vm.sk.predict(xd)
    blob = np.concatenate([xu, xd, pu[:, None], pd_[:, None]], axis=1).astype("<f8")
    blob.tofile(out / "model_rows.bin")
    info = {"model": model, "sha16": vm.sha16, "rows": int(len(xu)), "n_features": int(xu.shape[1]),
            "layout": "per row: x_up[n_features], x_dn[n_features], sklearn_up, sklearn_dn (float64 LE)",
            "vf": vm.vec.vf}
    (out / "model_rows.json").write_text(json.dumps(info, indent=1))
    st = {"root": str(root), "hours": list(hours), "arm": arm, "events": n, "orders": len(orders),
          "trigger_rows": len(rows), "model_rows": len(xu), "wall_s": time.time() - t0, "model": model}
    (out / "run.json").write_text(json.dumps(st, indent=1))
    return st


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--hours", required=True, help="comma list of epoch hours; the first is warm-up")
    ap.add_argument("--arm", default="vt_v1_m0.02_trigger")
    ap.add_argument("--model", default="v1_L0")
    ap.add_argument("--cap", type=int, default=50_000, help="max model calls kept for model_rows.bin")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    hours = [int(h) for h in a.hours.split(",")]
    out = Path(a.out) if a.out else CACHE / f"dec-{hours[0]}-{hours[-1]}"
    print(json.dumps(run(Path(a.root), hours, a.arm, out, a.model, a.cap), indent=1))


if __name__ == "__main__":
    main()
