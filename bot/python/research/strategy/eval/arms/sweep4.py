"""Sweep 4: push the fair-value taker past the edges of sweep 3's grid (margin above 0.06,
refractory below 0.05 s, size between 150 and 450 shares, fill floor up to 0.03)."""
from itertools import product

ARMS = []
for model, margin, m_fill, refr, size in product(("pz",), (0.06, 0.07, 0.08, 0.10), (0.02, 0.03),
                                                 (0.02, 0.05), (150.0, 300.0, 450.0)):
    ARMS.append({"name": f"fair_{model}_m{margin:g}_f{m_fill:g}_r{refr:g}_s{size:g}", "kind": "fair",
                 "params": dict(model=model, margin=margin, m_fill=m_fill, refr=refr, base=size,
                                max_sh=size), "needs": "perp"})
