"""Shared evaluation harness for candidate improvements of the deployed predictive arms.

    nice -n 10 python3 -m research.predict.improve.harness --arm <module:callable> \
        --out data/out/predict/improve/<name>/

Plug-in interface (api.py): a candidate is

    def candidate(fold: Fold) -> Arm | list[Arm]          # or predict sim spec dicts
    Arm(name: str, decide: Callable[[Market, int], dict | None], kind="taker")
    decide(mk: Market, L: int) -> {"t", "side", "shares", "limit"}   # taker orders, receipt clock

`Market` gives the market's decision table without targets (`mk.tab`), the strategy v2 table
(`mk.f2`), value predictions of a saved or candidate-fitted model (`mk.pred("v1", L)` ->
(up, down) per row) and `mk.meta`. `Fold` gives the fold's choose windows and the only
training-data path (`fold.load_rows()`: run 2 train + choose windows). Several Arms = variants
chosen on the fold's choose windows by a fixed rule (score/select.py). Optional attributes on
the callable: FOLD_INVARIANT, CRITERION, SELECT_L (run.py).

Evaluation: fold A chooses on {select, dev3} and evaluates on {test3r1, ext}; fold B the
reverse. Reported at L = 0 and -40, base fills and the 50 ms competition variant: fills/day,
10 s markout c/$ and $/day [CI], paired gain vs vt_v1_m0.03_any and vs micf [95% market
bootstrap], worst-5-market sum, busy-hour rows. No sealed market (start >= 1791744900) is
ever listed, loaded or simulated (guard.py)."""
from .api import Arm, Market
from .fold import Fold
from .frozen import from_spec
from .run import evaluate

__all__ = ["Arm", "Market", "Fold", "from_spec", "evaluate"]
