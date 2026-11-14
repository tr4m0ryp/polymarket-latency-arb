"""Post-test improvement round (select hours, a later look, labelled): the frozen primary's
markout is fat-tailed (top 5 markets > 100% of the total on dev3 and test3), so cap its
exposure: orders per market, orders per burst window, and a wider margin late in bursts."""
from .base import ARMS as BASE

ARMS = [a for a in BASE if a["name"] == "micf"]


def vt(name, **kw):
    return {"name": name, "kind": "vtaker", "model": "v3p", "family": "value taker, capped",
            "params": dict(margin=0.02, **kw)}


ARMS += [vt("vt_v3p_m0.02_any")]
ARMS += [vt(f"vt_v3p_cap{n}", max_fills=n) for n in (5, 10, 20, 40)]
ARMS += [vt(f"vt_v3p_burst{n}_{w}", burst=(n, w)) for n, w in ((2, 5.0), (3, 10.0), (5, 10.0), (5, 30.0))]
ARMS += [vt("vt_v3p_m0.03_burst3_10", burst=(3, 10.0))]
ARMS[-1]["params"]["margin"] = 0.03
