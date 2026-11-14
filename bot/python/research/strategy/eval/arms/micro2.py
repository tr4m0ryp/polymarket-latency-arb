"""Ceiling sweep of the held-out winner (microprice trigger + fair-value filter, micf): margin,
trigger size and window, refractory, and order size, on training markets only."""
from itertools import product

ARMS = []
for margin, thr, win, refr, sh in product((0.0, 0.01, 0.02, 0.03, 0.05), (0.002, 0.01, 0.05),
                                          (0.05, 0.1, 0.25), (0.1, 0.2, 0.5), (60.0, 150.0)):
    ARMS.append({"name": f"micf_pzm_m{margin:g}_t{thr:g}_w{win:g}_r{refr:g}_s{sh:g}", "kind": "micro",
                 "needs": "perp",
                 "params": dict(model="pzm", margin=margin, win=win, thr=thr, refr=refr,
                                band=(0.05, 0.95), tleft=20.0, fav_max=0.97, shares=sh, slip=0.02)})
