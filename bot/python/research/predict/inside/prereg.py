"""The frozen pre-registration of the inside gate (written once, BEFORE any sealed scoring).

    python3 -m research.predict.inside.prereg [--out <path>]   # refuses to overwrite

The JSON carries the config, its sha256, the sha256 of every file that decides a number
(rules, engine, runner, report) and of the model. `load()` refuses to score when any of them
changed since the freeze."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FROZEN = ROOT / "data" / "out" / "predict" / "inside-prereg.json"
CODE = ["research/predict/sim/rules.py", "research/predict/inside/engine.py",
        "research/predict/inside/run.py", "research/predict/inside/report.py",
        "research/predict/inside/prereg.py", "research/strategy/sim/maker.py", "research/predict/sim/fills.py"]
MODEL = "data/out/predict/models/v1_L50.pkl"
SEALED_FROM = 1791842700   # 2026-10-12 22:05 UTC: first Dublin market after the local recorder stopped (22:03)

CONFIG = {
    "model": "v1_L50", "k": 2, "xhold": 0.27, "L_ms": [50, 100, 150], "sizes": [[60.0, 300.0], [5.0, 20.0]],
    "rebate": 0.014,
    "arms": [
        {"name": "base_lat2", "rule": "vmaker", "params": {"half": 0.03, "pull": -0.03, "anchor": "fair"},
         "haircut": [False, True]},
        {"name": "inside", "rule": "vinside", "params": {"half": 0.04, "pull": -0.02, "h": 0.0},
         "haircut": [True, False]},
        {"name": "inside_h0.005", "rule": "vinside", "params": {"half": 0.04, "pull": -0.02, "h": 0.005},
         "haircut": [True, False]},
    ],
    "sets": {
        "dublin": {"start_min": SEALED_FROM, "source": "data/paper/dublin-20261012 (Dublin paper recording), "
                   "5m markets starting >= 2026-10-12 22:05 UTC; earlier Dublin hours overlap the local "
                   "recorder hours the fill-improve study selected on"},
        "dry": {"start_min": 0, "source": "data/trade/dublin-makerdry-20261014/raw (4 h dry run, "
                "2026-10-14 08:18-12:18 UTC), every market with a table and an outcome"},
    },
    "latency": "insert / cancel = min of k=2 draws from the warm Dublin probe quantiles (p50 56 / 50 ms) "
               "+ (L - 50 ms); the cancel waits for the insert ack",
    "haircut": "queue ahead = largest depth at our price from our decision to one insert latency after "
               "our order went live; eaten by crossing orders and prints at our price; prints through "
               "our price still fill",
    "analysis": {"boot": 2000, "seed": 0, "metric": "10 s venue-mid markout (mk10v), maker fee 0",
                 "baseline": {"arm": "base_lat2", "hc": False}, "primary_set": "pooled",
                 "drop_top5": "remove the 5 markets with the largest paired gain"},
    "criteria": {
        "P1_gain_ci": {"primary": True, "set": "pooled", "size": 60.0, "L": 50, "arm": "inside", "hc": True,
                       "col": "g_lo", "gt": 0.0},
        "P2_markout_ci": {"primary": True, "set": "pooled", "size": 60.0, "L": 50, "arm": "inside", "hc": True,
                          "col": "lo", "gt": 0.0},
        "P3_drop5": {"primary": True, "set": "pooled", "size": 60.0, "L": 50, "arm": "inside", "hc": True,
                     "col": "gain_drop5", "gt": 0.0},
        "S1_L100": {"set": "pooled", "size": 60.0, "L": 100, "arm": "inside", "hc": True, "col": "gain_day", "gt": 0.0},
        "S1_L150": {"set": "pooled", "size": 60.0, "L": 150, "arm": "inside", "hc": True, "col": "gain_day", "gt": 0.0},
        "S2_dublin": {"set": "dublin", "size": 60.0, "L": 50, "arm": "inside", "hc": True, "col": "g_lo", "gt": 0.0},
        "S2_dry": {"set": "dry", "size": 60.0, "L": 50, "arm": "inside", "hc": True, "col": "gain_day", "gt": 0.0},
        "S3_live_size": {"set": "pooled", "size": 5.0, "L": 50, "arm": "inside", "hc": True, "col": "mk10_cpd", "gt": 0.0},
        "S4_hyst_L50": {"set": "pooled", "size": 60.0, "L": 50, "arm": "inside_h0.005", "hc": True, "col": "gain_day", "gt": 0.0},
        "S4_hyst_L150": {"set": "pooled", "size": 60.0, "L": 150, "arm": "inside_h0.005", "hc": True, "col": "gain_day", "gt": 0.0},
    },
    "incidence_before_freeze": "test 1 on the dry run (replay of every decision row, no fills or outcomes "
                                "read): inside inserts 675 in 4.1 h (~166/h; full hours 154-224/h), h=0.005 "
                                "~139/h, above the ~130/h capacity line",
    "decision_rule": "GO live 1 h (5 sh, --rule inside) if P1-P3 pass. CONDITIONAL GO (1 h at 5 sh as a "
                     "fill-rate / haircut calibration, not as evidence of edge) if P2 and P3 pass and P1 "
                     "fails. NO-GO if the pooled L=50 haircut markout point estimate <= 0. The h=0.005 arm "
                     "replaces h=0 for the live test only if its gain beats h=0 at L=100 and L=150.",
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _hashes() -> dict:
    return {"code": {c: sha(ROOT / c) for c in CODE}, "model_sha256": sha(ROOT / MODEL)}


def freeze(out: Path = FROZEN) -> dict:
    if out.exists():
        raise SystemExit(f"refusing: {out} exists (frozen)")
    blob = json.dumps(CONFIG, sort_keys=True).encode()
    d = {"frozen_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "config": CONFIG,
         "config_sha256": hashlib.sha256(blob).hexdigest(), **_hashes()}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(d, indent=1))
    return d


def load(path: str | None = None) -> dict:
    """The frozen config; refuses when the frozen code, model or config changed since."""
    p = Path(path) if path else FROZEN
    d = json.loads(p.read_text())
    if path is None:
        now = _hashes()
        bad = [c for c, h in d["code"].items() if now["code"].get(c) != h]
        if bad or now["model_sha256"] != d["model_sha256"]:
            raise SystemExit(f"refusing: changed since the freeze: {bad or 'model'}")
        if hashlib.sha256(json.dumps(d["config"], sort_keys=True).encode()).hexdigest() != d["config_sha256"]:
            raise SystemExit("refusing: config sha mismatch")
    return d["config"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    d = freeze(Path(a.out) if a.out else FROZEN)
    print("frozen", d["frozen_utc"], "config", d["config_sha256"][:16])


if __name__ == "__main__":
    main()
