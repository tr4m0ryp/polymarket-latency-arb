"""Maker sweep on the v2 tables: fair-value quotes (pzm) pulled while the perp MICROPRICE moves
(the leaders' trigger, which fires ~0.27 s before their prints), at L = -40 / 0 ms."""
from itertools import product

ARMS = []
for half, pull, win in product((0.03, 0.05), (0.002, 0.01, 0.05), (0.1, 0.5, 1.0)):
    ARMS.append({"name": f"mkm_h{half:g}_p{pull:g}_w{win:g}", "kind": "maker", "needs": "perp",
                 "params": dict(model="pzm", half=half, band=(0.10, 0.90), tleft=30.0,
                                pull_bp=pull, pull_win=win, pull_src="pmic", size=60.0,
                                max_open=300.0)})
