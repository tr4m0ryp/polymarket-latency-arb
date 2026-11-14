**Harness built and verified.** It reproduces the report exactly on every overlapping window and market. Baseline tables are written for `vt_v1_m0.03_any`, `vt_v1_m0.02_trigger` and `micf`.

**TL;DR:** `python3 -m research.predict.improve.harness --arm <module:callable> --out data/out/predict/improve/<name>/`. Building the frozen-reference cache takes about **12 min** once. After that, a fresh 4-variant candidate takes **~10 min**, and a frozen arm takes **~30 s**.

## CLI
```
nice -n 10 python3 -m research.predict.improve.harness --arm <module:callable> \
    --out data/out/predict/improve/<name>/ [--L=0,-40] [--workers 2] [--threads 1] [--no-comp]
```
Each run writes `table.md`, `table.csv` (every set x arm x L x variant), `hours.csv`, `selection_{A,B}.csv` and `meta.json`.

## Plug-in interface (`research/predict/improve/harness/api.py`)
```python
def candidate(fold: Fold) -> Arm | list[Arm]        # or predict sim spec dicts (kind base/vtaker/vmaker)
Arm(name: str, decide: Callable[[Market, int], dict | None], kind="taker", size=60.0, max_open=300.0)
decide(mk: Market, L: int) -> {"t", "side" (+1/-1), "shares", "limit" (0-1)}   # taker, receipt clock, t sorted
                           # maker: {"t", "bid", "ask"} Up-frame ticks, 0 = none
# optional attributes on the callable: FOLD_INVARIANT=True, CRITERION="gain"|"lcb"|"mk", SELECT_L=0
```
- **What a decision can read:** `mk.tab` is the decision table with every `y_*`, `x_*` and `outcome` column removed. `mk.f2` is the strategy v2 table. `mk.pred("v1", L)` returns (up, down) predictions, cached on disk by model hash. `mk.pred({"model","vf"})` does the same for a model the candidate fits. `mk.meta` is also available.
- **Training data:** `fold.load_rows()` is the only training path. It covers run 2 train plus the fold's choose windows and refuses evaluate windows. Calling it scopes that fold's results so they are never reused across folds.
- **More than one arm:** the harness treats them as variants and picks one on the choose windows. The rule is fixed: highest gain over `vt_any` at L = 0, subject to markout > 0 and at least 100 fills/day. Only the picked variant is ever reported on that fold's evaluate windows.
- **Worked examples:** `harness/example.py` has `margin_sweep` (fold-invariant variants) and `retrained` (refits the model per fold).

## Design
- **Folds:**
  - A chooses on {select 144, dev3 120} and evaluates on {test3r1 83, ext 48}.
  - B is the reverse.
  - `CV:all` scores all 395 markets, each by a variant chosen without seeing it.
- **Simulator:** `strategy/sim/taker.py` and `maker.py` are called unchanged. Two variants per run:
  - base: J 10 ms, full level.
  - comp: J 50 ms, half of each level, as in `final_comp`.
- **Sets reported:**
  - each window, and each fold's pooled evaluation;
  - `busy15`: 2026-10-11 starts from 15:00 to 15:55, 12 markets;
  - `busyQ`: hours in the top quartile of trigger-sized perp microprice moves, 107 markets. This is label-free;
  - `unseen251`, to compare with the report's pooled numbers.
- **Seal:**
  - Market lists come from the frozen runs' `markets-*.csv` files. Nothing globs a cache directory.
  - Every list, simulation request and training load asserts `max(start) < 1791744900`. The evaluated maximum is 1791744600.
  - `SafeStore` cannot open hour files at or after the seal, and it drops sealed outcomes and gaps.
  - The paper-cache environment variables are refused, and the v1 model hashes are checked before every run.

## Reproduction (`python3 -m research.predict.improve.harness.check` writes `baseline/reproduction.md`)
- **Per market:** the max absolute difference is 0.000000 on n, cost, pnl and mk10v. This holds for all 4 windows x 3 arms x L 0/-40, and for `final_comp`.
- **Window rows:** fills/day, c/$, $/day and the paired gain vs micf with its CI are identical to `score-*/paired-*` for sel1, dev1, final, ext and final_comp.
- **Only difference, the pooled 251 CIs:** point estimates match (+849, +1,360, +875, +287) but the CIs move by about 30 to 50 $/day. For example, vt_any at L = 0 is [-51, +1,879] here and [-22, +1,926] in the report. The report's pooled numbers were computed ad hoc, with no code in the repo, so a different bootstrap draw is the likely cause. The per-market data is identical.
- **Window boundary:** ext is the 48 markets starting 14:55 to 18:50, which is what `markets-ext.csv` holds. `busy15` reproduces the report's +13.8 c/$ for the 1 s taker in the 15:00 hour.

## Runtime (2 workers x 1 thread, nice 10, box load average about 16 on 8 CPUs)

| job | wall | RSS |
|---|---|---|
| frozen-reference cache, built once (395 markets x 3 arms) | 719 s | 0.97 GB |
| frozen arm as candidate (cache hit) | 29-35 s | 0.2 GB |
| fresh 4-variant candidate (`example:margin_sweep`) | 601 s | 0.98 GB |

Replaying the book costs about 1.2 s per market and dominates. A single fresh arm is bounded by the 4-variant figure. A retraining candidate adds the time to load and fit its training rows.

## Baseline table (10 s markout; gains are paired, 95% market bootstrap, $/day; full table in `baseline/table.md`)

**L = 0, base**

| set (mkts) | arm | fills/day | mk c/$ | mk $/day [CI] | gain vs vt_any | gain vs micf | worst-5 $ |
|---|---|---|---|---|---|---|---|
| A:test3r1 (83) | vt_any | 468 | +13.6 | +1,716 [-419, +4,521] | | +820 [-1,280, +3,533] | -212 |
| A:test3r1 (83) | veto | 201 | +24.1 | +1,043 [+408, +1,826] | -673 [-3,327, +1,396] | +147 [-485, +700] | -36 |
| A:test3r1 (83) | micf | 392 | +6.6 | +896 [+163, +1,769] | -820 [-3,533, +1,280] | | -82 |
| A:ext (48) | vt_any | 948 | +7.7 | +1,450 [+214, +2,839] | | +1,075 [-622, +2,705] | -78 |
| A:ext (48) | veto | 1,428 | +3.5 | +866 [-476, +2,171] | -584 [-1,687, +477] | +491 [-1,257, +2,075] | -101 |
| A:ext (48) | micf | 936 | +1.3 | +375 [-867, +1,976] | -1,075 [-2,705, +622] | | -107 |
| A:busy15 (12) | vt_any | 648 | +13.8 | +1,734 [-1,466, +6,399] | | +2,878 [-542, +6,871] | -41 |
| A:busy15 (12) | veto | 864 | +6.1 | +863 [-855, +3,281] | -871 [-3,398, +1,348] | +2,007 [+52, +4,089] | -22 |
| A:busy15 (12) | micf | 816 | -4.1 | -1,144 [-3,086, +624] | -2,878 [-6,871, +542] | | -76 |
| B:select (144) | vt_any | 574 | +14.3 | +2,082 [+1,158, +3,062] | | +1,266 [+290, +2,380] | -116 |
| B:select (144) | veto | 350 | +21.0 | +1,496 [+891, +2,145] | -586 [-1,463, +160] | +680 [+51, +1,350] | -43 |
| B:select (144) | micf | 714 | +3.5 | +816 [+64, +1,608] | -1,266 [-2,380, -290] | | -188 |
| B:dev3 (120) | vt_any | 425 | +26.0 | +2,102 [+1,149, +3,262] | | +779 [-115, +2,018] | -55 |
| B:dev3 (120) | veto | 463 | +17.0 | +1,626 [+1,087, +2,289] | -476 [-1,521, +321] | +303 [+27, +580] | -13 |
| B:dev3 (120) | micf | 432 | +8.7 | +1,323 [+724, +1,972] | -779 [-2,018, +115] | | -67 |
| CV:busyQ (107) | vt_any | 764 | +13.2 | +1,832 [+945, +2,799] | | +464 [-620, +1,452] | -79 |
| CV:busyQ (107) | veto | 1,071 | +9.2 | +1,755 [+785, +2,756] | -77 [-690, +542] | +387 [-657, +1,357] | -103 |
| CV:busyQ (107) | micf | 875 | +5.1 | +1,368 [+432, +2,370] | -464 [-1,452, +620] | | -115 |
| CV:all (395) | vt_any | 552 | +15.2 | +1,934 [+1,328, +2,610] | | +1,001 [+291, +1,792] | -296 |
| CV:all (395) | veto | 484 | +14.5 | +1,364 [+1,022, +1,707] | -570 [-1,284, +30] | +431 [+67, +790] | -115 |
| CV:all (395) | micf | 588 | +4.8 | +933 [+511, +1,334] | -1,001 [-1,792, -291] | | -202 |
| unseen251 | vt_any | 539 | +15.9 | +1,850 [+1,003, +2,925] | | +849 [-51, +1,879] | -256 |
| unseen251 | veto | 561 | +12.0 | +1,288 [+862, +1,746] | -562 [-1,533, +234] | +287 [-137, +639] | -114 |

**L = -40, base**

| set (mkts) | arm | fills/day | mk c/$ | mk $/day [CI] | gain vs vt_any | gain vs micf | worst-5 $ |
|---|---|---|---|---|---|---|---|
| A:test3r1 (83) | vt_any | 1,270 | +8.5 | +2,524 [-232, +5,365] | | +1,121 [-1,448, +3,952] | -357 |
| A:test3r1 (83) | veto | 857 | +13.4 | +2,612 [+1,641, +3,728] | +88 [-2,670, +2,580] | +1,210 [+686, +1,735] | -55 |
| A:ext (48) | vt_any | 5,148 | +2.6 | +2,301 [+67, +4,467] | | +1,542 [-346, +3,514] | -189 |
| A:ext (48) | veto | 5,154 | +1.0 | +1,081 [-899, +3,131] | -1,221 [-2,935, +429] | +321 [-1,583, +2,065] | -144 |
| A:ext (48) | micf | 1,224 | +2.1 | +760 [-652, +2,453] | -1,542 [-3,514, +346] | | -108 |
| CV:busyQ (107) | vt_any | 3,696 | +5.0 | +3,108 [+1,606, +4,656] | | +1,170 [-117, +2,446] | -191 |
| CV:busyQ (107) | veto | 3,733 | +3.4 | +2,588 [+1,284, +3,856] | -520 [-1,633, +469] | +650 [-472, +1,662] | -153 |
| CV:all (395) | vt_any | 1,936 | +8.0 | +2,994 [+2,218, +3,785] | | +1,499 [+743, +2,293] | -500 |
| CV:all (395) | veto | 1,693 | +6.4 | +2,300 [+1,830, +2,752] | -694 [-1,425, +28] | +805 [+436, +1,178] | -172 |
| CV:all (395) | micf | 761 | +6.3 | +1,495 [+1,040, +1,941] | -1,499 [-2,293, -743] | | -190 |
| unseen251 | veto | 1,954 | +5.8 | +2,406 [+1,770, +3,071] | -485 [-1,506, +483] | +875 [+400, +1,282] | -166 |

**50 ms competition sensitivity (comp)**

| set | arm | L | mk c/$ | mk $/day [CI] | gain vs micf |
|---|---|---|---|---|---|
| CV:all | vt_any | 0 | +10.4 | +984 [+579, +1,435] | +560 [+54, +1,042] |
| CV:all | veto | 0 | +12.5 | +803 [+538, +1,094] | +379 [+102, +660] |
| CV:all | micf | 0 | +2.7 | +424 [+63, +764] | |
| A:ext | vt_any | 0 | +2.5 | +342 [-538, +1,164] | +248 [-1,049, +1,377] |
| A:ext | vt_any | -40 | -1.0 | -540 [-2,292, +1,166] | -754 [-2,650, +1,060] |
| A:ext | veto | -40 | -1.5 | -1,107 [-2,741, +505] | -1,322 [-3,240, +250] |
| A:ext | micf | -40 | +0.8 | +215 [-953, +1,658] | |
| CV:busyQ | vt_any | -40 | +1.7 | +682 [-508, +1,805] | -248 [-1,351, +847] |

## Weak spots the baseline shows (targets for candidates)
- **Busy hours under competition:** at L = -40 with the comp variant, both deployed arms go negative on ext, while micf stays at +0.8 c/$.
- **Veto vs taker:** the veto earns fewer dollars than vt_any almost everywhere. On CV:all at L = 0 the difference is -570 [-1,284, +30].
- **Tails:** vt_any's worst-5 markets sum to -296 $ at L = 0 and -500 $ at L = -40 on CV:all.

**Example run (a harness demo, not a claim):** `example:margin_sweep` picked a 2.5 c margin in both folds. On CV:all at L = 0 it beats vt_any by +284 [+25, +567]. It loses in `A:busy15` by -1,933 [-4,005, -283] and under comp at L = -40, so it is a lead for a volatility-scaled margin, not an improvement.

Nothing is committed.

## Files
- <REPO>/research/predict/improve/harness/ (`__init__.py`, `__main__.py`, `api.py`, `fold.py`, `frozen.py`, `guard.py`, `windows.py`, `run.py`, `report.py`, `check.py`, `example.py`, `sim/{worker,pool,frozen_cache}.py`, `score/{metrics,sets,select}.py`; every file is under 140 lines)
- <REPO>/data/out/predict/improve/baseline/table.md (full baseline, every set, both L, base and comp)
- <REPO>/data/out/predict/improve/baseline/reproduction.md
- <REPO>/data/out/predict/improve/baseline/{vt_any,veto,micf}/ (each with table.md/csv, hours.csv, meta.json)
- <REPO>/data/out/predict/improve/harness_example_margin/
- Caches (gitignored): <REPO>/data/cache/predict/improve/harness/frozen.pkl and pred/
