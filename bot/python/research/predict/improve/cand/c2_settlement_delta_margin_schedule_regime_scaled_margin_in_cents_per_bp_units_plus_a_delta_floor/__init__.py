"""C2: settlement-delta margin schedule for the deployed 1 s value taker and trigger veto.

The frozen arms fire when the 1 s model's predicted value >= a fixed cents margin. Here the
margin is a function of the settlement delta (cents of the bought token per bp of BTC, the
channel through which the Binance lead turns into token value, model/derive.py): a lower
margin where delta is high (fills there pay in every window) and no order at all below a
delta floor (low-delta fills lose, and busy hours are a low-delta regime because zscale ~
1/sigma). Everything else of the frozen rule stays (60 sh, seen ask + 2 c, 0.2 s refractory).

    delta.py   settlement delta of a decision table (the live bot's cost: one ndtri, one exp)
    arms.py    the _DM decision rule and the variant families (harness plug-ins)
    run.py     harness runner that also keeps every variant's per-market aggregates
    extra.py   gains vs the frozen veto, the per-window variant sweep, the kill criteria

    nice -n 10 python3 -m research.predict.improve.cand.<this>.run --arm dm_taker \
        --out data/out/predict/improve/cand-dmargin-taker/"""
