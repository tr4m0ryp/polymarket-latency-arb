"""Score the frozen fixes ONCE on the test hours (t >= 2026-10-13 00:00 UTC).

Checks the frozen models' sha256 against prereg.json, predicts on test veto orders, applies
each pre-registered rule, and reports fill, 10 s markout c/$, resolution c/$, $/day with a
market bootstrap CI and the gain over the plain veto at i = 0 (60 sh) paired by market.
Every fixed offset i = 0..10 is listed too (reference rows, not selected).

    PYTHONPATH=. python3 -m research.vetohold.fixes.score -> data/out/vetohold/fixes.md"""
from __future__ import annotations

import hashlib
import json
import pickle

import pandas as pd

from research.predict.report.md import md

from .. import OUT, SPLIT, VETO
from ..tables.common import ci, paired, stats
from .models import predict
from .rules import apply

RULES = ("plain", "fixed", "surv", "istar", "size", "fresh", "ev", "surv_size")


def test_rows() -> pd.DataFrame:
    d = pd.read_pickle(OUT / "rows.pkl")
    return d[(d["arm"] == VETO) & (d["scen"] == "real") & (d["t"] >= SPLIT)].reset_index(drop=True)


def row(name: str, r: pd.DataFrame, rr: pd.DataFrame, base: pd.DataFrame, mk: list[str], n: int) -> dict:
    s, sr = stats(r, "pnl", "cost", mk), stats(rr, "pnl", "cost", mk)
    p = paired(r, "pnl", base, "pnl", mk)
    return {"rule": name, "sent %": r["sent"].mean() * 100, "fill %": r["fill"].sum() / n * 100,
            "mk10 c/$": ci(s, "c_per_$", "c_lo", "c_hi"), "res c/$": ci(sr, "c_per_$", "c_lo", "c_hi"),
            "$/day": ci(s, "usd_day", "d_lo", "d_hi", 0), "gain vs plain $/day": ci(p, "gain_day", "g_lo", "g_hi", 0)}


def main():
    meta = json.loads((OUT / "prereg.json").read_text())
    blob = (OUT / "prereg.pkl").read_bytes()
    assert hashlib.sha256(blob).hexdigest() == meta["models_sha256"], "frozen models changed"
    fz = pickle.loads(blob)
    d = test_rows()
    mk = sorted(d["slug"].unique())
    pr = predict(fz["models"], d, fz["cols"])
    base = apply("plain", d, pr, {})
    out = [f"# Fixes on test hours (frozen {meta['frozen_utc']} UTC, before scoring)\n",
           f"test veto orders {len(d)}, markets {len(mk)}; params {json.dumps(meta['params'])}\n"]
    t = []
    for rule in RULES:
        par = meta["params"].get(rule, {})
        t.append(row(f"{rule} {par}" if par else rule, apply(rule, d, pr, par), apply(rule, d, pr, par, "res"),
                     base, mk, len(d)))
    out += ["## Pre-registered rules\n", md(pd.DataFrame(t), 1)]
    t = [row(f"fixed i = {i}", apply("fixed", d, pr, {"i": i}), apply("fixed", d, pr, {"i": i}, "res"), base, mk, len(d))
         for i in range(11)]
    out += ["\n## Every fixed offset on the same test orders (reference)\n", md(pd.DataFrame(t), 1)]
    (OUT / "fixes.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
