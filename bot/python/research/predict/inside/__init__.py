"""Inside-gate maker (reports/fill-improve.md idea 1): incidence on a dry run, the frozen
pre-registration (data/out/predict/inside-prereg.json) and its sealed-hours scoring.

    python3 -m research.predict.inside.incidence --run dublin-makerdry-20261014
    python3 -m research.predict.inside.prereg            # writes the frozen JSON, refuses to overwrite
    python3 -m research.predict.inside.run --set dublin   # then --set dry; scores into data/out/predict/inside/
    python3 -m research.predict.inside.report

Rules: research/predict/sim/rules.py `vinside` / `hysteresis`. Engine: engine.py (the mk engine
of the fill-improve study plus probe latency shifted to L and the rival-improver haircut)."""
