"""Winner sweep on run 2 select hours (second look at the select hours, labelled as such):
the value taker's margin, refractory, size, slippage and model variants; the value maker's
half width, pull threshold and pull model."""
from itertools import product

from .base import ARMS as BASE

ARMS = list(BASE)


def vt(mdl, margin=0.02, refr=0.2, shares=60.0, slip=0.02):
    return {"name": f"vt_{mdl}_m{margin}_r{refr}_s{shares:g}_sl{slip}", "kind": "vtaker", "model": mdl,
            "family": "value taker", "params": dict(margin=margin, refr=refr, shares=shares, slip=slip)}


for margin, refr in product((0.015, 0.02, 0.025), (0.1, 0.2, 0.5)):
    ARMS.append(vt("v3p", margin, refr))
ARMS += [vt("v3p", shares=s) for s in (30.0, 150.0, 300.0)]
ARMS += [vt("v3p", slip=s) for s in (0.01, 0.03, 0.05)]
ARMS += [vt(m) for m in ("v3", "v3pl", "v3pb", "v10p")]
for mdl, half, pull in product(("v1", "v3p"), (0.02, 0.03, 0.04), (-0.05, -0.04, -0.03, -0.02)):
    if mdl == "v3p" and pull in (-0.05, -0.02):
        continue
    ARMS.append({"name": f"vm_{mdl}_fair{half}_p{pull}", "kind": "vmaker", "model": mdl,
                 "family": "value maker", "params": dict(half=half, pull=pull, anchor="fair")})
