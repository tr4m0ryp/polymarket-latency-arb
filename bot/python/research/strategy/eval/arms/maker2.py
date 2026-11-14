"""Maker sweep 2 (invention 2b): book-anchored quotes (join or improve the touch on both
sides), pulling the side the perp fair value says is about to be run over. Cancels are not
held, so a pull at L reaches the CLOB before reactive takers (held 150 ms) can match."""
from itertools import product

ARMS = []
for model, pull, improve, tleft, size in product(("pz",), (0.0, 0.01, 0.02, 0.04), (False, True),
                                                 (30.0,), (60.0, 200.0)):
    ARMS.append({"name": f"mkb_{model}_p{pull:g}_i{int(improve)}_t{tleft:g}_s{size:g}", "kind": "maker",
                 "params": dict(model=model, anchor="book", pull=pull, improve=improve,
                                band=(0.10, 0.90), tleft=tleft, size=size, max_open=3 * size),
                 "needs": "perp"})
