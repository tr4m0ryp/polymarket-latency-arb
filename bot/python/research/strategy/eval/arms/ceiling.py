"""Train-selected ceiling of the winner's family (micro2 sweep, same objective as select.py:
10 s-markout $ per day at L = 0 on training markets), run once on the held-out hours."""
from .micro2 import ARMS as M2

ARMS = [dict(a, keep=True) for a in M2 if a["name"] == "micf_pzm_m0.01_t0.002_w0.05_r0.2_s150"]
