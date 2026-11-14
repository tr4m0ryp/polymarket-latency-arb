"""Sweep 5 (ceiling): the depth-sized fair taker selected after sweep 4 sat on two grid edges
(margin 0.10, refractory 0.02 s). Push margin to 0.20, refractory to 0, size to 600."""
from itertools import product

ARMS = []
for margin, m_fill, refr, size in product((0.10, 0.12, 0.15, 0.20), (0.02, 0.04), (0.0, 0.01, 0.02),
                                          (200.0, 300.0, 600.0)):
    ARMS.append({"name": f"fair_pz_m{margin:g}_f{m_fill:g}_r{refr:g}_s{size:g}", "kind": "fair",
                 "params": dict(model="pz", margin=margin, m_fill=m_fill, refr=refr, base=size,
                                max_sh=size), "needs": "perp"})
