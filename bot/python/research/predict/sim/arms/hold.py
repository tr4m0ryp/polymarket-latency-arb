"""Hold sensitivity (2026-10-13): live FAK acks take ~270 ms vs 56 ms for a resting insert, so
the venue holds takers longer than the 150 ms the sim assumed. The prereg2 takers and every
maker arm (strategy maker + all value makers of sel1/sel2), run at --hold 0.15 and 0.27."""
from .basemk import ARMS as MK
from .prereg2 import ARMS as P2
from .sel1 import ARMS as S1
from .sel2 import ARMS as S2

ARMS = list(P2) + [a for a in MK if a["kind"] == "basemaker"]
ARMS += [a for a in S1 + S2 if a["kind"] == "vmaker"]
assert len({a["name"] for a in ARMS}) == len(ARMS)
