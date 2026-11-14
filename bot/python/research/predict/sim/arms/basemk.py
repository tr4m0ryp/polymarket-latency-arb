"""Maker baseline from the strategy search (train-selected "maker, fair quotes pulled on
microprice moves"), so the value maker's delta is measured against it; plus micf."""
import json

from ....strategy import OUT as SOUT
from .base import MICF
from .sel1 import ARMS as S1
from .sel2 import ARMS as S2

_m = json.loads((SOUT / "selection2.json").read_text())["maker, fair quotes pulled on microprice moves"]
MKM = dict(_m, params={k: (tuple(v) if k == "band" else v) for k, v in _m["params"].items()})
ARMS = [{"name": "micf", "kind": "base", "arm": MICF},
        {"name": "strategy_maker_mkm", "kind": "basemaker", "arm": MKM}]
ARMS += [a for a in S1 + S2 if a["name"] in ("vm_fair0.03_p-0.03", "vm_v3p_fair0.02_p-0.03")]
