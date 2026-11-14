"""Held-out arms: the two baselines plus the train-selected arm of every family
(data/out/strategy/selection.json, written by eval/select.py before any test run)."""
import json

from ... import OUT
from .sweep1 import ARMS as S1

ARMS = [dict(a, keep=True) for a in S1 if a["name"] in ("theirs_spot", "theirs_perp")]
for fam, arm in json.loads((OUT / "selection.json").read_text()).items():
    p = dict(arm["params"])
    if "band" in p:
        p["band"] = tuple(p["band"])
    ARMS.append(dict(arm, params=p, family=fam, keep=True))
