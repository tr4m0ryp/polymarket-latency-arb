"""Maker sweep 4: past the edge of sweep 3 (wider quotes, more sensitive pulls, longer pull
windows). The maker only pays when its quotes sit beyond the noise of the fair value and are
pulled for the whole time the perp is moving."""
from itertools import product

ARMS = []
for half, pull, win in product((0.05, 0.06, 0.08), (0.05, 0.1), (0.5, 1.0, 3.0)):
    ARMS.append({"name": f"mk_pz_h{half:g}_t30_p{pull:g}_w{win:g}", "kind": "maker",
                 "params": dict(model="pz", half=half, band=(0.10, 0.90), tleft=30.0,
                                pull_bp=pull, pull_win=win, size=60.0, max_open=300.0),
                 "needs": "perp"})
