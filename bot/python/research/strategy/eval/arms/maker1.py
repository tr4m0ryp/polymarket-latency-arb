"""Maker sweep (invention 2): two-sided resting quotes at the perp fair value -/+ half,
re-priced on every perp / spot / book change (cancel + replace at latency L), optionally
pulled while the perp is moving. 60 shares per quote, unpaired inventory capped at 300."""
from itertools import product

ARMS = []
for model, half, tleft, pull in product(("pz",), (0.0, 0.01, 0.02, 0.03), (30.0,), (None, 0.3, 1.0)):
    ARMS.append({"name": f"mk_{model}_h{half:g}_t{tleft:g}_p{pull}", "kind": "maker",
                 "params": dict(model=model, half=half, band=(0.10, 0.90), tleft=tleft,
                                pull_bp=pull, pull_win=0.2, size=60.0, max_open=300.0),
                 "needs": "perp"})
