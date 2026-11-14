"""Held-out arms on the v2 (microprice) tables: the rebuilt baseline theirs_micro, the old
reconstructions, and the train-selected arm of every v2 family (selection2.json)."""
import json

from ... import OUT
from .micro1 import ARMS as M1

ARMS = [dict(a, keep=True) for a in M1 if a["name"].startswith("theirs_")]
for fam, arm in json.loads((OUT / "selection2.json").read_text()).items():
    p = dict(arm["params"])
    if "band" in p:
        p["band"] = tuple(p["band"])
    ARMS.append(dict(arm, params=p, family=fam, keep=True))
