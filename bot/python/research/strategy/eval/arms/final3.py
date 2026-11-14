"""Held-out arms of the post-hoc books-agree family: the agree-filtered baseline and the
train-selected micfa arm (selection3.json)."""
import json

from ... import OUT
from .micro3 import ARMS as M3

ARMS = [dict(a, keep=True) for a in M3 if a["name"] == "theirs_micro_agree"]
for fam, arm in json.loads((OUT / "selection3.json").read_text()).items():
    p = dict(arm["params"])
    p["band"] = tuple(p["band"])
    ARMS.append(dict(arm, params=p, family=fam, keep=True))
