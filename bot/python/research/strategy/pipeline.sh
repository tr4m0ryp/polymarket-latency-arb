#!/bin/bash
# Full strategy-search chain (reports/strategy-search.md). Read-only research: no orders.
# Heavy steps run under nice with 2 workers; at most one heavy step at a time.
#   bash research/strategy/pipeline.sh
set -e
cd "$(dirname "$0")/../.."
N="nice -n 10 python3 -m research.strategy"
S="$N.eval.sim --workers 2 --hold 0.15"
$N.ingest.run --workers 2                      # recorded hours -> npz, Gamma outcomes
$N.eval.prep --workers 2                       # v1 feature tables
$N.eval.prep --micro --workers 2               # v2 tables (microprice candidates)
$N.eval.fit && $N.eval.fit --micro             # fair-value models, training hours only
# training sweeps (L = receipt -> CLOB; 0 ~ Dublin host, -40 ~ split Tokyo build)
$N.eval.sim --workers 2 --hold 0 --arms sweep1 --tag s1 --L=50,100,150 --split train  # no-hold contrast
$S --arms sweep1 --tag h1 --L=0,50,100,150 --split train
$S --arms sweep2 --tag h2 --L=0,50,100,150 --split train
$S --arms sweep3 --tag h3 --L=0,50,100 --split train
$S --arms sweep4 --tag h4 --L=0,50,100 --split train
$S --arms sweep5 --tag h5 --L=0,50,100 --split train
$S --arms maker1 --tag mkh --L=0,50,100 --split train
$S --arms maker2 --tag mkb --L=0,50,100 --split train
$S --arms maker3 --tag mk3 --L=-40,0 --split train
$S --arms maker4 --tag mk4 --L=-40,0 --split train
$S --micro --arms micro1 --tag m1 --L=0,50,100 --split train
$S --micro --arms makerm --tag mm --L=-40,0 --split train
$S --micro --arms micro2 --tag m2 --L=0,50 --split train
$S --micro --arms micro3 --tag m3 --L=0,50,100 --split train
python3 -m research.strategy.eval.select && python3 -m research.strategy.eval.select --v2
python3 -m research.strategy.eval.select --v3
# held-out: frozen selections, then sensitivities
$S --arms final --tag final --L=-40,0,25,50,100,150,200 --split test
$S --micro --arms final2 --tag final2 --L=-40,0,25,50,100,150,200 --split test
$S --micro --arms ceiling --tag ceil --L=-40,0,50,100,150 --split test
$S --micro --arms final3 --tag final3 --L=-40,0,50,100,150 --split test
$N.eval.sim --workers 2 --arms final --tag final_h25 --L=0,50,100 --hold 0.25 --split test
$N.eval.sim --workers 2 --micro --arms final2 --tag final2_h25 --L=0,50,100 --hold 0.25 --split test
$S --arms final --tag final_comp --L=0,50,100 --J 0.05 --cap 0.5 --split test
$S --micro --arms final2 --tag final2_comp --L=0,50,100 --J 0.05 --cap 0.5 --split test
$S --arms final --tag final_x0 --L=-40,0,50 --xhold 0 --split test
$S --micro --arms final2 --tag final2_x0 --L=-40,0,50 --xhold 0 --split test
$S --arms sweep1 --tag d1 --L=0 --split test     # diagnostics only, never used to select
$S --arms maker3 --tag d3 --L=-40,0 --split test
$N.eval.leaders && $N.eval.leaders --markout   # leaders' actual fills (Data API)
for x in "" _h25 _comp _x0; do python3 -m research.strategy.eval.summary --split test --suffix "$x"; done
python3 -m research.strategy.eval.tables
