"""Selection sweep on run 2 select hours: baselines + value-model takers and makers."""
from itertools import product

from .base import ARMS as BASE

ARMS = list(BASE)
for mdl, margin, req in product(("v1", "v3p"), (0.01, 0.02, 0.03, 0.05), (None, "trigger", "micf")):
    if mdl == "v3p" and req is not None:
        continue
    ARMS.append({"name": f"vt_{mdl}_m{margin}_{req or 'any'}", "kind": "vtaker", "model": mdl,
                 "family": "value taker" if req is None else f"value taker + {req}",
                 "params": dict(margin=margin, require=req)})
for anchor, half, pull in product(("fair", "book"), (0.03, 0.05), (-0.03, -0.01, 0.01)):
    if anchor == "book" and half != 0.03:
        continue
    ARMS.append({"name": f"vm_{anchor}{'' if anchor == 'book' else half}_p{pull}", "kind": "vmaker",
                 "model": "v1", "family": f"value maker ({anchor})",
                 "params": dict(half=half, pull=pull, anchor=anchor)})
