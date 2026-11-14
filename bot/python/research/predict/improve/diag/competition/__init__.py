"""Competition and fill-realism diagnostic of the deployed predictive arms (post-freeze).

Question: in the losing fills and bad markets, was the edge gone because rivals (other takers,
the leaders, fast makers requoting) cleared or repriced the depth during or right after our
150 ms hold? Reads only allowed markets (select, dev3, test3 run 1, ext); every entry point
asserts max(market start) < SEALED (prereg2 test segment). Outputs data/out/predict/improve/.

Layout: data/ (sealed-data guard, taker prints), sim/ (instrumented taker, decisions, fill
scenarios, per-order measurements, runner, reproduction check), report/ (bootstrap tables),
race/ (race-aware value label, hypothesis 1).

    OMP_NUM_THREADS=2 nice -n 10 python3 -m research.predict.improve.diag.competition.sim.run \
        --win select,dev3,final,ext [--kind main|sweep|edge|edge2|race|vlim]
    OMP_NUM_THREADS=2 nice -n 10 python3 -m research.predict.improve.diag.competition.race.label
    python3 -m research.predict.improve.diag.competition.sim.check --win ext
    python3 -m research.predict.improve.diag.competition.report.analyze      # round 1 tables
    python3 -m research.predict.improve.diag.competition.report.sweep --kind sweep
    python3 -m research.predict.improve.diag.competition.report.extra        # jitter, losers
    python3 -m research.predict.improve.diag.competition.report.sizesel      # value-keyed size
    python3 -m research.predict.improve.diag.competition.report.vlim         # chase limits
    python3 -m research.predict.improve.diag.competition.report.race         # race label
    python3 -m research.predict.improve.diag.competition.report.cadence      # rival timing"""
from ..... import predict

SEALED = 1791744900          # 2026-10-11 18:55 UTC: prereg2 test segment starts here
OUT = predict.OUT / "improve"
CACHE = predict.CACHE / "improve" / "competition"

# window name -> market list of an earlier frozen run (data/out/predict/markets-<tag>.csv)
WINDOWS = {"select": "sel1", "dev3": "dev1", "final": "final", "ext": "ext"}
