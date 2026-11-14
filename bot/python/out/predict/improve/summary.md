# Improvement round 2026-10-12: summary

**TL;DR.** Five invented candidates were tested against the two frozen arms (`vt_v1_m0.03_any`, `vt_v1_m0.02_trigger`) using only allowed data: 395 markets (select 144, dev3 120, test3 run 1 83, ext 48), with max start 1791744600 < 1791744900. **None survived verification, so no prereg3.json is written.** The sealed prereg2 segment is evaluated with the frozen arms alone, as prereg2 specified. The strongest candidate is C1 (conviction-keyed size), with a large pooled gain. In fold A, the most recent regime, its taker gain is unproven and its veto gain is carried by the top 5 markets. Its constants were designed on screens that read every evaluate window. C2's veto floor gets 63% of its gain from a single market. C3, C4 and C5 lost to the frozen arms by their own kill tests.

**Units and terms:**
- Gains are paired 10 s markout gains in $/day against the frozen arm, with 95% market-bootstrap CIs. Taker arms are compared with `vt_v1_m0.03_any` and veto arms with `vt_v1_m0.02_trigger`.
- Fold A evaluates on test3r1 + ext; fold B evaluates on select + dev3.
- CV:all scores each market under the pick of the fold that did not choose on it.
- base = 10 ms race at the full level; comp = 50 ms race at half the level.
- All results use the 0% fee tier.

## 1. Results vs the frozen arms

| candidate (pick) | vs | A:eval L0 | B:eval L0 | CV:all L0 | CV:all L-40 | A:ext L0 (busy) | A:busy15 L0 | CV:all L0 comp | worst-5 $ cand / frozen | verification |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 taker `ek_pred_2000` (pre-declared) | taker | +158 [-135, +457] | +716 [+442, +1,038] | +531 [+306, +767] | +1,173 [+733, +1,651] | +148 [-121, +484] | +363 [-292, +1,417] | +155 [+58, +254] | -369 / -296 | failed (1 of 3 refuted: fold A not positive, top-5 carried) |
| C1 veto `vk_vstar_3000(_d8)` (pre-declared) | veto | +517 [-81, +1,213] | +1,414 [+878, +2,011] | +1,117 [+701, +1,593] | +1,713 [+1,156, +2,347] | +152 [-669, +979] | -428 [-1,082, +210] | +274 [+115, +462] | n/a | failed (same verification as the C1 taker) |
| C1 veto `vk_vstar_4000_d6` (post-hoc design) | veto | +795 [+131, +1,635] | +1,706 [+1,098, +2,371] | +1,404 [+937, +1,960] | +2,291 [+1,631, +3,021] | +526 [-230, +1,437] | -255 [-882, +349] | +393 [+197, +608] | -193 / -115 | post-hoc: K, cap and selection column chosen after scoring |
| C2 taker `dm25_f3` (pre-reg) | taker | +158 [-125, +453] | +398 [+71, +791] | +318 [+84, +592] | +287 [+52, +544] | -17 [-595, +507] | -713 [-2,329, +434] | +221 [+19, +470] | -316 / -296 | failed (3 of 3 refuted: own PASS missed; drop-top-5 +107 [-62, +275]) |
| C2 veto `dmv_f3` (pre-reg) | veto | +191 [+7, +495] | +6 [+0, +18] | +68 [+6, +161] | +99 [+13, +206] | +522 [+15, +1,381] | +515 [-165, +1,395] | +71 [+10, +164] | -67 / -115 | failed (3 of 3 refuted: market 555 = 63% of the gain; drop-top-5 -1 [-8, +5]) |
| C3 coherence taker (pre-reg) | taker | -1,161 [-2,256, -305] | +48 [-357, +454] | -353 [-793, +42] | -18 [-411, +374] | n/a | -2,874 [-5,653, -713] | -204 [-514, +117] | -350 / -296 | killed by its own tests 1-3 |
| C3 coherence veto (pre-reg) | veto | -223 [-637, +188] | -18 [-108, +77] | -86 [-240, +68] | +118 [-101, +365] | n/a | -1,679 [-3,380, -441] | -90 [-228, +47] | -202 / -115 | killed by its own tests 1-3 |
| C4 race-clock taker (pre-declared r1) | taker | -160 [-792, +466] | -32 [-64, -7] | -74 [-289, +122] | n/a | -211 | -1,111 | +17 [-53, +97] | -321 / -296 | killed by its own test 2 |
| C5 balanced refit `rf_bal_m3` (pre-reg) | taker | -900 [-2,497, +298] | -647 [-1,314, -74] | -731 [-1,444, -142] | n/a | -814 [-2,140, +245] | -2,086 [-6,502, +807] | -346 [-759, +32] | -202 / -296 | killed by its own tests 1-2 |

**Frozen references (CV:all, L0 base):**
- `vt_any`: 552 fills/day, +15.2 c/$, +1,934 [+1,328, +2,610] $/day. Comp +984, worst-5 -296.
- Veto: 484 fills/day, +14.5 c/$, +1,364 [+1,022, +1,707] $/day. Worst-5 -115.

### Verification detail for the near-misses

**C1 taker, fold A.**
- The fold A gain is +158 [-135, +457] base and +15 [-152, +183] comp.
- Without its top 5 markets, fold A reads -73 [-317, +114] base and -108 [-260, +4] comp.
- The gain decays window by window in time order. At L0 base, taker / veto: select +677 / +1,643, dev3 +762 / +1,782, test3r1 +164 / +950, ext +148 / +526.
- Under comp with the top 5 markets dropped, ext is significantly negative: taker -148 [-283, -32], veto -344 [-645, -84].

**C1 design leakage.** The "pre-declared" constants (K 2000/3000, the 30-200 and 100-300 bounds, the delta cap and the v* key) come from fill-level screens. Those screens read unseen251 and ext, which are evaluate windows of both folds. The 2-fold CV is therefore not an out-of-sample test of the design.

**C1 fill-model dependence.**
- Under a harsher fill model (50 ms window, a quarter of each level), the taker gain is +53 [-15, +125].
- The veto gain is partly just larger orders: at matched size, conviction vs flat is only +85 [+17, +167] under comp.

**C2 veto.**
- Only 9 of 395 markets differ from the frozen veto, and 8 of those 9 are in ext.
- The 3 c/bp floor was read off the loss-anatomy screen on test3r1 + ext.
- The A:ext gain (+522) equals the diagnostic number (+522 [+13, +1,342]) that motivated the floor.

**C2 taker.**
- It misses its own pre-registered PASS (A:ext >= 0) at -17.
- Its busy-hour sign flips between margins of 2.25 and 2.75 c: A:ext reads -345 / -17 / +70.

## 2. What holds within the seen data (no out-of-sample claim)

- **Conviction beats flat size at matched size (C1):**
  - Taker: +260 [+109, +432] on CV:all L0 base, +59 [+4, +119] comp.
  - Veto: +614 [+361, +924] base, +85 [+17, +167] comp.
  - The extra shares on high-value orders earn more per share than the base ones: 10-24 c/sh outside ext with the v* key.
- **For the veto, the v* key beats the pred key at the same K:** +215 [+79, +388] (comp +32 [-5, +80]), and +221 [+83, +396] when both carry the cap.
- **The delta-floor screen (C2) removes the veto's worst busy fills.** Ext markout rises from +3.5 to +7.1 c/$. The effect is confined to a few markets with volatility spikes or extreme mids.
- **The race clock (C4) is predictable but adds nothing.** Its event AUC is 0.69 and stable across windows. In this simulator it carries no information beyond seen depth or plain size.
- **C5 refits lose to v1 even in-sample.** Adding rows compresses the top predictions, and lowering margins to recover volume adds losing fills.

## 3. Classification of every abandoned idea

| idea | class | premises / reason | reopen if |
|---|---|---|---|
| C1 conviction-keyed size (taker `ek_pred_2000`, veto `vk_vstar_3000` / `4000_d6`) | **never tested out of sample** (failed verification) | Design screens read every allowed window. Fold A is not positive for the taker and is top-5-carried for the veto | Freeze the round-1 picks before new hours are recorded or opened (post-run-3 recording or the paper run), with drop-top-5 >= 0 and comp >= 0 gates |
| C1 v* key for the taker | **lost a comparison** to the pred key | +15 [-196, +232] | none planned |
| C1 vmin = min(pred, v*) key | **lost a comparison** to v* and pred | +337 vs +545 at K 2000 | none |
| C1 variance-aware Kelly size | **lost a comparison** in an earlier round; not retested | n/a | n/a |
| C2 veto floor `dmv_f3` (3 c/bp) | **never tested out of sample** (failed verification) | 63% of the gain is in market 555; the floor value was read off ext | Fresh hours, plus mid-band and sigma-only baseline arms to isolate delta as the mechanism |
| C2 taker `dm25_f3` | **lost a comparison** in busy hours | Missed its own PASS (A:ext -17); the busy-hour sign depends on the margin parameter | A busy-hour-only test with the margin fixed in advance |
| C2 continuous margin (25/delta)^a | **lost a comparison** to the step schedule | A:ext -1,096, busy15 -3,529 | none |
| C2 2 c margin at delta >= 40 | **lost a comparison** | busy15 -3,310; the model over-predicts at high delta | none |
| C2 band cap 25-80 c/bp; veto lowering `dmv25@1.5_f3` | **never tested** (designed post-hoc) | Designed after the CV breakdown | prereg4 candidates |
| C2 refractory preemption | **proven closed** | Premise: same-side bursts fall inside the 0.2 s refractory | The refractory changes |
| C3 identity-projected firing score (lam > 0) | **lost a comparison** to the independent-side score; lam = 0 is the sweep optimum | The common-mode premise holds (true error +0.6 to +2.5 c), but the orders the projection removes earn more than the orders it admits | A fill-conditional value target |
| C3 inverted sign `anticm_veto` | **never tested** (post-hoc) | Its planned parent family gave -24 | Fresh hours |
| C4 cap and tighten direction (rc_size, rc_lim, vlim_tight) | **proven closed** | Premises: (1) the unfilled rest of a FAK (fill-and-kill) order is free; (2) walked shares mark +2.2 to +30 c/sh in every P_alive x v* cell on run-2 train; (3) the depth model has no price impact | A fill model with impact or maker repricing, or paper fills where walked levels mark <= 0 |
| C4 race-keyed walk and boost | **lost a comparison** to the race-free twins | vs vlw_ek -179 [-399, -6]; ties or losses vs dq_vlw / max_vlw | Same as the C4 cap and tighten row |
| C4 max-size arms (max_vlw, heat_vlw) | **lost a comparison** on tails and busy comp | c/$ falls from 15 to 10, worst-5 reaches -1,441, ext L-40 comp -3,259 | none |
| vlw_ek (C1 size + value walk, race-free, found inside C4) | **never tested** as a registered candidate | CV:all +941 [+552, +1,357], comp +463 [+220, +739]; fold A +551 [-40, +1,208]; in-sample design | Next round, in the C1 family |
| C5 busy-inclusive balanced refit (22 variants) | **lost a comparison** to frozen v1 | Premises: a 1 s best-level target (no depth, no race), GBDT 200x15, the frozen rule | A retrain on a target aligned with the simulated fill markout |
| C5 H6 (busy calibration slope moves toward 1) | **never tested** | Needs busy hours outside the allowed data | Post-run-3 hours |

## 4. Novel Contributions

| claim | what it beats | falsifiable test |
|---|---|---|
| **Conviction-keyed sizing on the identity-projected value v*, for a veto on a known trigger.** Each added share earns more than under flat upsizing. | Flat upsizing at matched mean size: +614 [+361, +924] $/day (veto). Pred-keyed size: +215 [+79, +388]. Both are in-sample. | On hours not used in the design (post-run-3 or paper): at L = 0 comp, conviction vs flat at matched size has LCB > 0 and stays >= 0 after dropping the top 5 markets. |
| **Under FAK semantics without impact, a taker cannot gain by predicting the stale maker's cancel.** Capping or tightening only removes fills with positive expected value. Any race-keyed size information is already in seen depth. | The race-clock family (C4), an inversion of the default | Holds by the premises in section 3. It breaks if paper fills show walked levels marking <= 0, or if our orders measurably move the book. |
| **The two-side identity v_up + v_dn = -c holds on the match book, not the seen book.** The 150 ms hold widens the spread by 1-3 c at firing moments, so a projection on the seen book lowers the effective margin. | The naive coherence projection (C3) | On new hours, at firing rows: mean c_seen - c_match <= -1 c, and corr(e_seen, dc) > corr(e_seen, true error). |
| **A refit that ranks rows better can still lose on simulated fills (C5).** The 1 s best-level target is misaligned with the fill-conditional objective. | The busy-inclusive retrain hypothesis | A refit on a fill-aligned target beats v1 in CV markout, where the best-level refit did not. |

**Honest publication assessment.** This round produced negative and mechanism results, not a new deployable arm.

The most useful pieces are the FAK closure argument (C4) and the seen-vs-match identity finding (C3). Together they explain why two natural inventions fail at a 150 ms hold. That is enough for a short section in the existing workshop-level paper, not a paper on its own.

C1's sizing result is a plausible positive but in-sample by design and fragile in fold A. It cannot be claimed until it passes on hours that played no part in choosing its constants.

All numbers are simulator results on 395 markets from about 2.5 days. None comes from real fills.

## 5. Decision for the sealed segment

No candidate survived, so **prereg3.json is not written**. The prereg2 segment can now be opened under prereg2 as registered: frozen arms only, simulated once. At decision time no prereg2 evaluation output existed: `git log` on `data/out/predict/*prereg2*` shows only prereg2.json.

The leads for the next pre-registration are C1's round-1 picks (`ek_pred_2000`, `vk_vstar_3000`) and C2's `dmv_f3`. That registration must be frozen before the hours it is tested on are recorded or opened. It must carry the drop-top-5 and comp gates that the verifiers proposed.

Sources: data/out/predict/improve/c1-size/summary.md, cand-dmargin-summary.md, c3_coherence/summary.md, cand-race/summary.md, c5_busy_refit/final.md.
