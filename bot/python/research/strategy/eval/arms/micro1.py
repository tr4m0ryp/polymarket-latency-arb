"""Microprice sweep (v2 feature tables, `sim --micro`).

theirs_micro is the rebuilt baseline, the leaders' trigger as read in reports/hidden-trigger.md:
fire when the perp microprice moved >= 0.002 bp over the last 0.1 s, buy the side of the perp
+ spot microprice change, bursts at most every 0.2 s, favourite <= 0.90, >= 30 s left, 60
shares, marketable limit = seen ask + 2 c. Our arms add selective thresholds, price band and
time-left filters, a fair-value filter, and the fair taker refit on these candidates (pz2) or
with microprice lag buckets (pzm)."""
from itertools import product

from .sweep1 import THEIRS

ARMS = [
    {"name": "theirs_micro", "kind": "micro", "keep": True, "needs": "perp",
     "params": dict(win=0.1, thr=0.002, refr=0.2, band=(0.01, 0.99), tleft=30.0, fav_max=0.9,
                    shares=60.0, slip=0.02)},
    {"name": "theirs_spot", "kind": "momentum", "params": dict(src="spot", **THEIRS), "keep": True},
    {"name": "theirs_perp", "kind": "momentum", "params": dict(src="perp", **THEIRS),
     "needs": "perp", "keep": True},
]
for win, thr, band, tleft, refr in product((0.05, 0.1, 0.25), (0.002, 0.01, 0.05, 0.2, 0.5),
                                           ((0.01, 0.99), (0.10, 0.70), (0.20, 0.80)), (30.0, 90.0),
                                           (0.2, 1.0)):
    ARMS.append({"name": f"mic_w{win:g}_t{thr:g}_b{band[0]:g}-{band[1]:g}_l{tleft:g}_r{refr:g}",
                 "kind": "micro", "needs": "perp",
                 "params": dict(win=win, thr=thr, refr=refr, band=band, tleft=tleft, fav_max=0.9,
                                shares=60.0, slip=0.02)})
for margin, thr in product((0.0, 0.01, 0.02, 0.03), (0.002, 0.05)):
    ARMS.append({"name": f"micf_pzm_m{margin:g}_t{thr:g}", "kind": "micro", "needs": "perp",
                 "params": dict(model="pzm", margin=margin, win=0.1, thr=thr, refr=0.2,
                                band=(0.05, 0.95), tleft=20.0, fav_max=0.97, shares=60.0, slip=0.02)})
for model, margin, refr, base in product(("pz2", "pzm"), (0.02, 0.03, 0.05, 0.08), (0.25, 1.0),
                                         (60.0, 300.0)):
    ARMS.append({"name": f"fair_{model}_m{margin:g}_r{refr:g}_s{base:g}", "kind": "fair", "needs": "perp",
                 "params": dict(model=model, margin=margin, m_fill=0.0, refr=refr, base=base,
                                max_sh=base)})
