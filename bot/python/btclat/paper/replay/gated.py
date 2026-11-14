"""Reference decisions of the hold-aware veto `v1h_G_h250x_L0` for the Rust parity test.

    BTCLAT_STRATEGY_CACHE=data/paper/dublin-20261012/cache/strategy nice -n 10 \
        python3 -m btclat.paper.replay.gated --root data/paper/dublin-20261012/raw \
        --hours 497750,497751,497752,497753 [--out data/cache/rust/v1h-<h0>-<h1>]

Policy (reports/veto-hold.md section 5, research/vetohold/label): the paper bot's veto arm
`vt_v1_m0.02_trigger` decides every value candidate (trigger + gates + v1 >= 2 c on the trigger
side); each such row, BEFORE the refractory, is scored by the gate on [v1's 98 trigger-side
inputs, v1 value, the 7 `x_*` book features], all float32 as in training. Send iff
gate >= tau (the pre-registered -0.005), then the 0.2 s per-market refractory; limit = seen.

The 7 features are computed by research's own `extras()` (research/vetohold/label/extras.py) on
the research Store of the same tape, at the paper bot's decision times, so the reference is the
research definition itself, not a re-implementation. Writes to --out:
  decisions.jsonl   one line per order: t, slug, side, limit (= seen), seen, pred_up, pred_dn, gate
  gate_rows.jsonl   every v1-pass row before the refractory: t, slug, side, seen, v1, x (7), gate, send
  run.json          root, hours, model, tau, i = 0, counts"""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import time
from pathlib import Path

import numpy as np

from ..engine.core import Engine
from ..model.load import MODELS, ValueModel
from . import source
from .decisions import CACHE

GATE = "v1h_G_h250x_L0"
ARM = "vt_v1_m0.02_trigger"
EXTRA = ("x_dep0", "x_dep2", "x_dep5", "x_ddep0.25", "x_ddep1.0", "x_age", "x_rlag")
REFR = 0.2


class Last(ValueModel):
    """v1 with its last two input vectors kept (the trigger side's is the gate's first 98)."""

    def __call__(self, row: dict) -> tuple[float, float]:
        self.xu, self.xd = self.vec.sides(row)
        return self.tree(self.xu), self.tree(self.xd)


class Capture:
    """Paper executor stand-in: records each v1 order (refractory 0 = every pass row)."""

    def __init__(self, vm: Last):
        self.vm, self.rows = vm, []

    def submit(self, o, m, src, t_venue, lat_us) -> None:
        x = self.vm.xu if o["side"] > 0 else self.vm.xd
        self.rows.append({"t": o["t"], "slug": m.meta["slug"], "side": o["side"], "seen": o["seen"],
                          "pred_up": o["pred_up"], "pred_dn": o["pred_dn"], "src": src, "x": x.copy()})

    def advance(self, now) -> None:
        pass

    def flush(self) -> None:
        pass


def v1_rows(root: Path, hours) -> tuple[list, int]:
    vm = Last("v1_L0")
    eng = Engine(vm, None, "parity", arms=[ARM])
    a = eng.decider.vt[0]
    eng.decider.vt = [dict(a, params=dict(a["params"], refr=0.0))]
    eng.paper = Capture(vm)
    n = 0
    for ev in source.events(root, hours, quantize=False):
        eng.on_event(ev)
        n += 1
    return eng.paper.rows, n


def book_feats(rows: list) -> np.ndarray:
    """research extras() per market on the Store's book events, at the rows' times."""
    from research.strategy.ingest.load import Store
    from research.strategy.sim.grid import Book, _replay
    from research.vetohold.label.extras import extras
    st = Store(keep=4)
    idx = {s: i for i, s in enumerate(st.mk["slug"])}
    out = np.full((len(rows), len(EXTRA)), np.nan, np.float32)
    by: dict[str, list[int]] = {}
    for k, r in enumerate(rows):
        by.setdefault(r["slug"], []).append(k)
    for slug, ks in by.items():
        m = st.market(idx[slug])
        meta, ev = m["meta"], m["ev"]
        book = Book(ev, meta["start"] - 2, meta["end"] + 2, m["gaps"])
        rsz = _replay(ev["t"], ev["side"], ev["tick"].astype(np.int64), ev["size"], meta["start"] - 2, book.n)
        t = np.array([rows[k]["t"] for k in ks])
        side = np.array([rows[k]["side"] for k in ks], float)
        seen = np.array([rows[k]["seen"] for k in ks])
        ex = extras(m, rsz, book, t, side, np.rint(seen * 100).astype(int))
        out[ks] = np.column_stack([ex[c[2:]] for c in EXTRA])
    return out


def gate(rows: list, xb: np.ndarray) -> tuple[np.ndarray, float, dict]:
    path = MODELS / f"{GATE}.pkl"
    blob = path.read_bytes()
    d = pickle.loads(blob)
    assert list(d["vf"][-8:]) == ["v1_value", *EXTRA], d["vf"][-8:]
    pre = json.loads((Path(__file__).resolve().parents[3] / "data/out/vetohold/vmodels/prereg.json").read_text())
    tau = float(d["meta"]["tau"])
    assert tau == pre["variants"][pre["winner"]]["tau"] and pre["export"]["name"] == GATE
    v1 = np.array([r["pred_up"] if r["side"] > 0 else r["pred_dn"] for r in rows])
    X = np.hstack([np.array([r["x"] for r in rows]).astype(np.float32), v1.astype(np.float32)[:, None], xb])
    return d["model"].predict(X), tau, {"pkl": path.name, "pkl_sha256": hashlib.sha256(blob).hexdigest()}


def run(root: Path, hours, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    cache = out / "v1_rows.pkl"   # the slow paper replay, kept for re-scoring
    if cache.exists():
        rows, n = pickle.loads(cache.read_bytes())
    else:
        rows, n = v1_rows(root, hours)
        cache.write_bytes(pickle.dumps((rows, n)))
    xb = book_feats(rows)
    g, tau, info = gate(rows, xb)
    last: dict[str, float] = {}
    orders = []
    with open(out / "gate_rows.jsonl", "w") as fh:
        for r, x, p in zip(rows, xb, g):
            send = bool(p >= tau) and r["t"] - last.get(r["slug"], -np.inf) >= REFR
            if send:
                last[r["slug"]] = r["t"]
                orders.append({"t": r["t"], "slug": r["slug"], "side": r["side"], "limit": r["seen"], "seen": r["seen"],
                               "pred_up": r["pred_up"], "pred_dn": r["pred_dn"], "src": r["src"], "gate": float(p)})
            v1 = r["pred_up"] if r["side"] > 0 else r["pred_dn"]
            fh.write(json.dumps({"t": r["t"], "slug": r["slug"], "side": r["side"], "seen": r["seen"], "v1": v1,
                                 "x": [float(v) for v in x], "gate": float(p), "send": send}) + "\n")
    with open(out / "decisions.jsonl", "w") as fh:
        for o in orders:
            fh.write(json.dumps(o) + "\n")
    st = {"root": str(root), "hours": list(hours), "arm": ARM, "model": GATE, "tau": tau, "i": 0.0, **info,
          "events": n, "v1_rows": len(rows), "gate_pass": int((g >= tau).sum()), "orders": len(orders),
          "wall_s": time.time() - t0}
    (out / "run.json").write_text(json.dumps(st, indent=1))
    return st


def main() -> None:
    from research import strategy
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--hours", required=True, help="comma list of epoch hours; the first is warm-up")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    root = Path(a.root)
    want = root.resolve().parent / "cache" / "strategy"
    assert strategy.CACHE.resolve() == want, f"set BTCLAT_STRATEGY_CACHE={want} (research Store of this tape)"
    hours = [int(h) for h in a.hours.split(",")]
    out = Path(a.out) if a.out else CACHE / f"v1h-{hours[0]}-{hours[-1]}"
    print(json.dumps(run(root, hours, out), indent=1))


if __name__ == "__main__":
    main()
