"""Maker sweep 3: around the best fair-quote maker (half 0.03, pull on a 0.3 bp perp move):
wider quotes, more sensitive and longer pulls. Run at L = -40 (split Tokyo build) and 0
(Dublin): the maker only breaks even when its cancels are fast."""
from itertools import product

ARMS = []
for half, pull, win in product((0.03, 0.04, 0.05), (0.1, 0.2, 0.3), (0.2, 0.5)):
    ARMS.append({"name": f"mk_pz_h{half:g}_t30_p{pull:g}_w{win:g}", "kind": "maker",
                 "params": dict(model="pz", half=half, band=(0.10, 0.90), tleft=30.0,
                                pull_bp=pull, pull_win=win, size=60.0, max_open=300.0),
                 "needs": "perp"})
