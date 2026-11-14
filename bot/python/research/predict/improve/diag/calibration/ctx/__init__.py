"""Activity context of every decision-table row (causal, data at or before the row only):
the regime columns of rows/regime.py plus the slow scales the adaptive-gain features divide
by. One npz per market under CACHE/ctx/, built once from the store (ctx/build.py) and read
by the harness candidates and the retraining code (ctx/load.py)."""
from .. import CACHE

DIR = CACHE / "ctx"
