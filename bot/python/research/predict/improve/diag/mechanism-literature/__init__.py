"""Phenomenon diagnostic: how the Polymarket 5m book follows Binance when Binance gets busy.

Question: when the leading venue is busy, do the follower's makers requote faster, do rival
takers snipe the stale quotes first, does the Binance move persist less, and does our own feed
lag more? Each is a mechanism by which a value model calibrated on quiet hours over-predicts
in busy ones. Unit = a Binance perp move that implies >= 1 c of Polymarket fair value within
100 ms (an "event"); every response is timed on the venue clocks (Binance T, Polymarket ts).

Sealed data: market lists come only from earlier frozen runs' markets-<tag>.csv, every list is
asserted to start before SEALED, and hour files are opened by explicit path only when they END
at or before SEALED (the 18:00 hour is never opened, so ext stops at the 17:50 market).

The directory name has a hyphen, so it runs as a directory, registered as `mech_lit`:

    OMP_NUM_THREADS=2 nice -n 10 python3 research/predict/improve/diag/mechanism-literature build
    python3 research/predict/improve/diag/mechanism-literature analyze
    OMP_NUM_THREADS=2 nice -n 10 python3 research/predict/improve/diag/mechanism-literature calib
    OMP_NUM_THREADS=2 nice -n 10 python3 research/predict/improve/diag/mechanism-literature fills
    python3 research/predict/improve/diag/mechanism-literature posthoc
    OMP_NUM_THREADS=2 nice -n 10 python3 research/predict/improve/diag/mechanism-literature sidecheck
    python3 research/predict/improve/diag/mechanism-literature deciles
    OMP_NUM_THREADS=2 nice -n 10 python3 research/predict/improve/diag/mechanism-literature calib --windows select --tag calib_select
    python3 research/predict/improve/diag/mechanism-literature surprise
    python3 research/predict/improve/diag/mechanism-literature gate

Second pass (race/): requote lag by activity decile at fixed level size, maker cancel vs trade
consumption, rival excess over matched quiet instants, the hold as a last look, maker-speed
memory, the feed's trade-direction labels, and the frozen model's calibration by surprise."""
from research.predict import CACHE as PCACHE, OUT as POUT  # noqa: F401
from research.strategy import CACHE as SCACHE  # noqa: F401

SEALED = 1791744900              # 2026-10-11 18:55 UTC: prereg2 test segment starts here
WINDOWS = {"select": "sel1", "dev3": "dev1", "test3r1": "final", "ext": "ext"}
OUT = POUT / "improve"
WORK = PCACHE / "improve" / "mechanism-literature"

THR_C = 1.0          # event: perp mid move implying >= 1 c of P(Up) within LOOK s
LOOK = 0.100
REFR = 1.0           # >= 1 s between events of one market
TLEFT = 20.0         # same time gate as the arms (secs_left >= 20)
BAND = (0.10, 0.90)  # venue mid band at the event
CENSOR = 10.0        # response clocks censored at 10 s
LS = (-40, 0, 50)
HOLD = 0.150
RUN_HOURS = range(1791583200 // 3600, SEALED // 3600)   # run 2 start .. last hour ending before SEALED
