"""Sweep 3: ceiling of the winning family (fair-value taker): order size up to 2000 shares
(the limit price, not the size, then decides how much stale depth is taken), refractory,
margin and the post-fee fill floor."""
from itertools import product

ARMS = []
for model, margin, m_fill, refr, size in product(("pz", "pzx"), (0.04, 0.05, 0.06), (0.01, 0.02),
                                                 (0.05, 0.1), (300.0, 600.0, 1000.0, 2000.0)):
    ARMS.append({"name": f"fair_{model}_m{margin:g}_f{m_fill:g}_r{refr:g}_s{size:g}", "kind": "fair",
                 "params": dict(model=model, margin=margin, m_fill=m_fill, refr=refr, base=size,
                                max_sh=size), "needs": "perp"})
