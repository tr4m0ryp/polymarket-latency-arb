"""Baseline arms from the strategy search: the rebuilt leader rule (theirs_micro) and the
frozen winner micf (selection2.json), decided on the strategy v2 tables."""
import json

from ....strategy import OUT as SOUT
from ....strategy.eval.arms.micro1 import ARMS as M1

THEIRS = next(a for a in M1 if a["name"] == "theirs_micro")
_sel = json.loads((SOUT / "selection2.json").read_text())["microprice trigger + fair-value filter"]
MICF = dict(_sel, params={k: (tuple(v) if k == "band" else v) for k, v in _sel["params"].items()})

ARMS = [{"name": "theirs_micro", "kind": "base", "arm": THEIRS},
        {"name": "micf", "kind": "base", "arm": MICF}]
