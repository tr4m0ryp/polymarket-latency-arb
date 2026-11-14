"""Export a frozen value model (sklearn HistGradientBoostingRegressor in the {model, vf, meta}
pickle) to JSON for the Rust live bot (rust/crates/model), with sha256 checks on both ends.

    python3 -m research.predict.infer.export --model v1_L0 [--sha256 <hex of the .pkl>]
    python3 -m research.predict.infer.export --path data/out/predict/models/<new>.pkl --sha256 <hex>

The pickle's sha256 must match either --sha256 or, for the pre-registered v1 models, the first
16 hex of data/out/predict/prereg2.json `models_sha256_16`; otherwise the export is refused.

Output data/out/predict/models/<name>.trees.json:
  format, name, source, source_sha256, vf (feature names in model input order), meta,
  baseline (float), n_features, trees: [{feature, threshold, left, right, is_leaf, value,
  missing_left, bin_threshold}] (sklearn `_predictors[i][0].nodes`, node indices per tree),
  bin_thresholds (per feature, sklearn `_bin_mapper.bin_thresholds_`).
Floats are written with repr (exact round trip). The sha256 of the JSON file itself is written to
<name>.trees.json.sha256 and printed: the Rust bot refuses a model whose file hash differs from
the one it is given (--model-sha256)."""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path

from research.predict import OUT as POUT

MODELS = POUT / "models"
PREREG = POUT / "prereg2.json"
FORMAT = "btclat-hgb-v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(path: Path, want: str | None) -> str:
    got = sha256(path)
    if want:
        if got != want.lower():
            raise SystemExit(f"refusing: {path.name} sha256 {got} != given {want}")
        return got
    pre = json.loads(PREREG.read_text())["models_sha256_16"].get(path.name)
    if pre is None or got[:16] != pre:
        raise SystemExit(f"refusing: {path.name} sha256[:16] {got[:16]} != pre-registered {pre}; pass --sha256")
    return got


def trees(model) -> list[dict]:
    out = []
    for pred in model._predictors:
        if len(pred) != 1:
            raise SystemExit("refusing: multi-output model")
        nd = pred[0].nodes
        if nd["is_categorical"].any():
            raise SystemExit("refusing: categorical splits are not supported by the Rust evaluator")
        out.append({"feature": [int(x) for x in nd["feature_idx"]],
                    "threshold": [float(x) for x in nd["num_threshold"]],
                    "left": [int(x) for x in nd["left"]], "right": [int(x) for x in nd["right"]],
                    "is_leaf": [int(x) for x in nd["is_leaf"]], "value": [float(x) for x in nd["value"]],
                    "missing_left": [int(x) for x in nd["missing_go_to_left"]],
                    "bin_threshold": [int(x) for x in nd["bin_threshold"]]})
    return out


def export(path: Path, want: str | None, out: Path | None = None) -> tuple[Path, str]:
    src_sha = check(path, want)
    with open(path, "rb") as fh:
        d = pickle.load(fh)
    m = d["model"]
    name = path.stem
    doc = {"format": FORMAT, "name": name, "source": path.name, "source_sha256": src_sha,
           "vf": list(d["vf"]), "meta": d.get("meta", {}),
           "baseline": float(m._baseline_prediction.ravel()[0]), "n_features": int(m.n_features_in_),
           "trees": trees(m),
           "bin_thresholds": [[float(x) for x in b] for b in m._bin_mapper.bin_thresholds_]}
    if doc["n_features"] != len(doc["vf"]):
        raise SystemExit(f"refusing: model has {doc['n_features']} inputs, vf lists {len(doc['vf'])}")
    out = out or path.with_name(f"{name}.trees.json")
    out.write_text(json.dumps(doc, default=float))
    h = sha256(out)
    out.with_name(out.name + ".sha256").write_text(h + "\n")
    return out, h


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None, help="name under data/out/predict/models, e.g. v1_L0")
    ap.add_argument("--path", default=None, help="explicit .pkl path (new models)")
    ap.add_argument("--sha256", default=None, help="expected sha256 of the .pkl (required unless pre-registered)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if bool(a.model) == bool(a.path):
        raise SystemExit("give exactly one of --model / --path")
    path = Path(a.path) if a.path else MODELS / f"{a.model}.pkl"
    out, h = export(path, a.sha256, Path(a.out) if a.out else None)
    print(f"{out}  sha256 {h}")


if __name__ == "__main__":
    main()
