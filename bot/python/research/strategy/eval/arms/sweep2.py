"""Sweep 2: refine the fair-value taker (sizing, refractory, margin, band, time left, model
incl. the perp-imbalance variants) and the best momentum family, plus the two baselines."""
from itertools import product

from .sweep1 import ARMS as S1

ARMS = [a for a in S1 if a["name"] in ("theirs_spot", "theirs_perp")]

for model, margin, m_fill, refr, base in product(("pz", "pzx", "pzi", "pzxi"), (0.02, 0.03, 0.04, 0.05),
                                                 (0.0, 0.01), (0.1, 0.25), (60.0, 150.0, 300.0)):
    ARMS.append({"name": f"fair_{model}_m{margin:g}_f{m_fill:g}_r{refr:g}_s{base:g}", "kind": "fair",
                 "params": dict(model=model, margin=margin, m_fill=m_fill, refr=refr, base=base,
                                max_sh=base), "needs": "perp"})

for model, margin, kelly in product(("pz", "pzxi"), (0.02, 0.03, 0.05), (2000.0, 5000.0)):
    ARMS.append({"name": f"fairk_{model}_m{margin:g}_k{kelly:g}", "kind": "fair",
                 "params": dict(model=model, margin=margin, m_fill=0.0, refr=0.25, base=20.0,
                                kelly=kelly, max_sh=600.0), "needs": "perp"})

for model, band, tleft in product(("pz", "pzxi"), ((0.10, 0.90), (0.20, 0.80), (0.05, 0.70)),
                                  (20.0, 45.0, 90.0)):
    ARMS.append({"name": f"fairb_{model}_b{band[0]:g}-{band[1]:g}_t{tleft:g}", "kind": "fair",
                 "params": dict(model=model, margin=0.03, m_fill=0.0, refr=0.25, base=150.0,
                                max_sh=150.0, band=band, tleft=tleft), "needs": "perp"})

for src, win, thr, refr in product(("perp", "smid"), (0.2, 0.5), (0.2, 0.3, 0.5), (0.5, 2.0)):
    ARMS.append({"name": f"mom_{src}_w{win:g}_t{thr:g}_r{refr:g}_b0.7", "kind": "momentum",
                 "params": dict(src=src, win=win, thr=thr, refr=refr, band=(0.10, 0.70), tleft=30.0,
                                fav_max=0.9, shares=60.0, slip=0.02),
                 "needs": "perp" if src == "perp" else None})
