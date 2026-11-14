# Reverse-engineered triggers, 5m leaders (taker buys, block-time resolution)


## Leader A

### Does it fire this second?
rows train 129,300 test 43,200; base rate 0.089
held-out AUC 0.852, accuracy 0.913
importance (AUC drop): book 0.210, since_last 0.043, secs_left 0.040, r3 0.024, r5 0.021, r2 0.012, pair_up 0.002, gap 0.002
depth-3 tree (class 1 = fires):
```
|--- since_last <= 12.50
|   |--- book <= 0.86
|   |   |--- r3 <= 0.53
|   |   |   |--- class: 0
|   |   |--- r3 >  0.53
|   |   |   |--- class: 0
|   |--- book >  0.86
|   |   |--- r5 <= -0.45
|   |   |   |--- class: 0
|   |   |--- r5 >  -0.45
|   |   |   |--- class: 0
|--- since_last >  12.50
|   |--- since_last <= 30.50
|   |   |--- book <= 0.89
|   |   |   |--- class: 0
|   |   |--- book >  0.89
|   |   |   |--- class: 0
|   |--- since_last >  30.50
|   |   |--- gap <= -0.11
|   |   |   |--- class: 0
|   |   |--- gap >  -0.11
|   |   |   |--- class: 0
```

### Which side, given it fires?
rows train 12,081 test 3,621; base rate 0.496
held-out AUC 0.752, accuracy 0.685
importance (AUC drop): r3 0.234, secs_left 0.010, book 0.010, r10 0.009, r2 0.008, r5 0.007, r1 0.006, book_chg2 0.004
depth-3 tree (class 1 = Up):
```
|--- r3 <= -0.00
|   |--- secs_left <= 161.50
|   |   |--- pair_up <= 0.05
|   |   |   |--- class: 0
|   |   |--- pair_up >  0.05
|   |   |   |--- class: 0
|   |--- secs_left >  161.50
|   |   |--- r1 <= -0.28
|   |   |   |--- class: 0
|   |   |--- r1 >  -0.28
|   |   |   |--- class: 0
|--- r3 >  -0.00
|   |--- r3 <= 0.00
|   |   |--- r10 <= -0.16
|   |   |   |--- class: 1
|   |   |--- r10 >  -0.16
|   |   |   |--- class: 0
|   |--- r3 >  0.00
|   |   |--- secs_left <= 111.50
|   |   |   |--- class: 1
|   |   |--- secs_left >  111.50
|   |   |   |--- class: 1
```

### Simple rules
single-rule side accuracy on fires (share where the rule picks the side bought):
- sign r1: 0.594 on 57% of fires
- sign r3: 0.693 on 78% of fires
- sign r10: 0.597 on 91% of fires
- sign gap (fair - book): 0.582 on 100% of fires
- against position: 0.500 on 96% of fires
- same as last side: 0.523 on 96% of fires
- better pair gain: 0.498 on 100% of fires
no-move fires (|r3| < 0.2 bp, 46%):
- sign gap: 0.524
- against position: 0.524
- same as last side: 0.485
- better pair gain: 0.538

## Leader B

### Does it fire this second?
rows train 129,300 test 43,200; base rate 0.138
held-out AUC 0.847, accuracy 0.868
importance (AUC drop): book 0.185, since_last 0.064, secs_left 0.031, r5 0.020, r3 0.011, r2 0.005, book_chg2 0.004, r10 0.002
depth-3 tree (class 1 = fires):
```
|--- since_last <= 9.50
|   |--- since_last <= -499.00
|   |   |--- secs_left <= 296.50
|   |   |   |--- class: 0
|   |   |--- secs_left >  296.50
|   |   |   |--- class: 0
|   |--- since_last >  -499.00
|   |   |--- since_last <= 3.50
|   |   |   |--- class: 0
|   |   |--- since_last >  3.50
|   |   |   |--- class: 0
|--- since_last >  9.50
|   |--- since_last <= 21.50
|   |   |--- book <= 0.88
|   |   |   |--- class: 0
|   |   |--- book >  0.88
|   |   |   |--- class: 0
|   |--- since_last >  21.50
|   |   |--- gap <= 0.08
|   |   |   |--- class: 0
|   |   |--- gap >  0.08
|   |   |   |--- class: 0
```

### Which side, given it fires?
rows train 18,796 test 5,783; base rate 0.511
held-out AUC 0.712, accuracy 0.657
importance (AUC drop): r3 0.189, r2 0.013, secs_left 0.012, r10 0.009, r1 0.007, pos 0.006, book_chg2 0.004, pair_dn 0.004
depth-3 tree (class 1 = Up):
```
|--- r3 <= -0.00
|   |--- secs_left <= 113.50
|   |   |--- class: 0
|   |--- secs_left >  113.50
|   |   |--- r1 <= -1.11
|   |   |   |--- class: 0
|   |   |--- r1 >  -1.11
|   |   |   |--- class: 0
|--- r3 >  -0.00
|   |--- r3 <= 0.00
|   |   |--- r10 <= -0.00
|   |   |   |--- class: 1
|   |   |--- r10 >  -0.00
|   |   |   |--- class: 0
|   |--- r3 >  0.00
|   |   |--- book_chg2 <= 0.05
|   |   |   |--- class: 1
|   |   |--- book_chg2 >  0.05
|   |   |   |--- class: 1
```

### Simple rules
single-rule side accuracy on fires (share where the rule picks the side bought):
- sign r1: 0.571 on 57% of fires
- sign r3: 0.651 on 75% of fires
- sign r10: 0.562 on 90% of fires
- sign gap (fair - book): 0.555 on 100% of fires
- against position: 0.514 on 98% of fires
- same as last side: 0.518 on 98% of fires
- better pair gain: 0.500 on 100% of fires
no-move fires (|r3| < 0.2 bp, 51%):
- sign gap: 0.513
- against position: 0.534
- same as last side: 0.489
- better pair gain: 0.534
