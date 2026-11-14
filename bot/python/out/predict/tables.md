### Final test (run 3, frozen)

| arm | L ms | fills/day | net $/day | CI lo | CI hi | net c/$ | 10 s mk c/$ | 10 s mk $/day | win | max DD $ |
|---|---|---|---|---|---|---|---|---|---|---|
| predictive taker, 150 sh (2nd look) | -40 | 2,560.8 | -13,255.0 | -65,871.4 | 21,562.0 | -8.6 | 2.2 | 3,352.3 | 0.56 | 7,778.1 |
| **predictive taker (primary, frozen)** | -40 | 2,633.6 | -4,406.3 | -29,603.2 | 12,764.9 | -5.7 | 3.9 | 3,025.8 | 0.56 | 3,596.9 |
| predictive taker, refr 0.1 s (2nd look) | -40 | 3,237.4 | -6,077.9 | -38,143.6 | 16,663.3 | -6.4 | 3.1 | 2,975.9 | 0.57 | 4,912.2 |
| predictive veto on their trigger | -40 | 857.1 | 2,497.2 | -324.8 | 5,124.6 | 12.8 | 13.4 | 2,612.1 | 0.57 | 171.5 |
| predictive taker, 1 s model, margin 3 c | -40 | 1,270.0 | -492.9 | -13,386.5 | 8,518.2 | -1.7 | 8.5 | 2,523.8 | 0.52 | 1,658.4 |
| predictive maker (3 s model pulls, 2nd look) | -40 | 2,127.0 | -115.1 | -3,087.5 | 3,012.7 | -0.5 | 8.2 | 1,712.8 | 0.51 | 236.0 |
| their rule, rebuilt | -40 | 2,699.6 | -305.2 | -8,635.2 | 6,503.6 | -0.4 | 2.1 | 1,692.5 | 0.61 | 1,338.4 |
| predictive veto on micf | -40 | 399.0 | 238.1 | -1,561.2 | 2,031.6 | 2.0 | 13.2 | 1,544.1 | 0.64 | 196.1 |
| micf (strategy winner) | -40 | 555.2 | -20.8 | -2,415.6 | 2,330.7 | -0.1 | 7.8 | 1,402.5 | 0.66 | 221.1 |
| predictive maker (1 s model pulls) | -40 | 1,651.7 | -1,057.8 | -4,072.3 | 1,954.5 | -7.1 | 5.5 | 813.1 | 0.44 | 477.9 |
| predictive taker, 150 sh (2nd look) | 0 | 1,512.9 | -12,437.9 | -55,560.9 | 17,529.1 | -13.1 | 4.1 | 3,900.9 | 0.54 | 7,079.0 |
| predictive taker, refr 0.1 s (2nd look) | 0 | 2,047.2 | -5,962.0 | -34,181.2 | 14,249.4 | -9.9 | 5.9 | 3,560.1 | 0.53 | 4,511.7 |
| **predictive taker (primary, frozen)** | 0 | 1,571.9 | -4,393.1 | -26,022.7 | 11,018.3 | -9.1 | 6.7 | 3,233.5 | 0.55 | 3,429.3 |
| predictive taker, 1 s model, margin 3 c | 0 | 468.4 | 498.0 | -4,954.9 | 5,846.5 | 4.0 | 13.6 | 1,715.8 | 0.60 | 741.1 |
| predictive veto on their trigger | 0 | 201.3 | 740.9 | -796.1 | 2,377.7 | 17.1 | 24.1 | 1,042.6 | 0.53 | 139.6 |
| micf (strategy winner) | 0 | 392.1 | -34.5 | -2,108.8 | 2,062.6 | -0.3 | 6.6 | 895.7 | 0.67 | 177.3 |
| predictive veto on micf | 0 | 138.8 | -278.6 | -1,575.1 | 958.4 | -6.4 | 17.4 | 751.7 | 0.55 | 120.2 |
| their rule, rebuilt | 0 | 2,092.3 | -946.2 | -8,371.3 | 5,572.1 | -1.4 | 0.6 | 402.6 | 0.61 | 1,188.2 |
| predictive maker (1 s model pulls) | 0 | 1,544.1 | -457.7 | -3,396.4 | 2,290.7 | -3.5 | 2.8 | 368.7 | 0.44 | 237.1 |
| predictive maker (3 s model pulls, 2nd look) | 0 | 1,873.7 | -1,453.7 | -4,577.1 | 1,815.5 | -7.1 | 1.4 | 294.9 | 0.47 | 563.7 |
| leader A actual | 0 | 3,261.7 | -2,274.6 | -6,523.1 | 1,386.5 | -5.6 | 0.0 | 0.1 | 0.49 | 1,053.4 |
| leader B actual | 0 | 6,984.9 | 180.1 | -3,954.3 | 4,444.0 | 0.3 | -0.5 | -334.9 | 0.45 | 707.3 |
| **predictive taker (primary, frozen)** | 50 | 1,297.7 | -5,978.7 | -28,201.7 | 9,303.7 | -14.0 | 4.3 | 1,815.8 | 0.54 | 3,595.9 |
| predictive taker, refr 0.1 s (2nd look) | 50 | 1,717.6 | -7,833.4 | -34,926.6 | 11,334.6 | -14.6 | 3.3 | 1,798.1 | 0.54 | 4,644.4 |
| predictive taker, 150 sh (2nd look) | 50 | 1,238.7 | -15,808.2 | -63,023.2 | 16,833.9 | -18.0 | 1.9 | 1,668.3 | 0.54 | 7,826.7 |
| predictive taker, 1 s model, margin 3 c | 50 | 281.1 | -416.2 | -4,879.5 | 3,589.8 | -4.8 | 10.9 | 941.7 | 0.59 | 702.6 |
| micf (strategy winner) | 50 | 350.5 | -266.8 | -2,357.4 | 1,892.6 | -2.2 | 5.5 | 670.8 | 0.63 | 220.3 |
| predictive veto on their trigger | 50 | 62.5 | -89.2 | -1,108.5 | 932.5 | -6.8 | 41.8 | 546.3 | 0.39 | 168.5 |
| predictive veto on micf | 50 | 48.6 | 413.2 | -328.4 | 1,374.8 | 34.3 | 39.8 | 479.8 | 0.57 | 48.9 |
| their rule, rebuilt | 50 | 1,911.9 | -723.3 | -7,805.2 | 5,463.8 | -1.2 | -0.1 | -33.1 | 0.60 | 1,108.9 |
| predictive maker (1 s model pulls) | 50 | 1,204.0 | -209.1 | -2,319.9 | 1,858.2 | -2.0 | -1.8 | -188.5 | 0.46 | 259.2 |
| predictive maker (3 s model pulls, 2nd look) | 50 | 1,783.5 | -1,695.8 | -4,589.5 | 1,012.6 | -9.9 | -2.9 | -491.4 | 0.48 | 536.2 |

| arm | L | 10 s mk gain vs micf $/day | CI lo | CI hi |
|---|---|---|---|---|
| their rule, rebuilt | -40 | 290 | -1,131 | 1,713 |
| their rule, rebuilt | 0 | -493 | -1,895 | 868 |
| their rule, rebuilt | 50 | -704 | -2,092 | 687 |
| predictive maker (1 s model pulls) | -40 | -589 | -2,170 | 994 |
| predictive maker (1 s model pulls) | 0 | -527 | -2,360 | 1,341 |
| predictive maker (1 s model pulls) | 50 | -859 | -2,142 | 314 |
| predictive maker (3 s model pulls, 2nd look) | -40 | 310 | -1,104 | 1,862 |
| predictive maker (3 s model pulls, 2nd look) | 0 | -601 | -2,687 | 1,561 |
| predictive maker (3 s model pulls, 2nd look) | 50 | -1,162 | -2,784 | 400 |
| predictive veto on micf | -40 | 142 | -144 | 433 |
| predictive veto on micf | 0 | -144 | -752 | 320 |
| predictive veto on micf | 50 | -191 | -809 | 313 |
| predictive veto on their trigger | -40 | 1,210 | 686 | 1,735 |
| predictive veto on their trigger | 0 | 147 | -485 | 700 |
| predictive veto on their trigger | 50 | -125 | -752 | 413 |
| predictive taker, 1 s model, margin 3 c | -40 | 1,121 | -1,448 | 3,952 |
| predictive taker, 1 s model, margin 3 c | 0 | 820 | -1,280 | 3,533 |
| predictive taker, 1 s model, margin 3 c | 50 | 271 | -1,704 | 2,441 |
| **predictive taker (primary, frozen)** | -40 | 1,623 | -4,864 | 7,599 |
| **predictive taker (primary, frozen)** | 0 | 2,338 | -3,486 | 8,054 |
| **predictive taker (primary, frozen)** | 50 | 1,145 | -4,188 | 6,812 |
| predictive taker, refr 0.1 s (2nd look) | -40 | 1,573 | -9,005 | 10,194 |
| predictive taker, refr 0.1 s (2nd look) | 0 | 2,664 | -5,212 | 9,663 |
| predictive taker, refr 0.1 s (2nd look) | 50 | 1,127 | -6,546 | 8,259 |
| predictive taker, 150 sh (2nd look) | -40 | 1,950 | -10,916 | 13,075 |
| predictive taker, 150 sh (2nd look) | 0 | 3,005 | -8,203 | 12,801 |
| predictive taker, 150 sh (2nd look) | 50 | 997 | -9,861 | 11,596 |


### Final test, 50 ms race window + half of each level

| arm | L ms | fills/day | net $/day | CI lo | CI hi | net c/$ | 10 s mk c/$ | 10 s mk $/day | win | max DD $ |
|---|---|---|---|---|---|---|---|---|---|---|
| **predictive taker (primary, frozen)** | 0 | 1,394.9 | -5,310.9 | -22,245.4 | 6,554.6 | -14.4 | 3.6 | 1,337.7 | 0.54 | 2,868.5 |
| predictive taker, refr 0.1 s (2nd look) | 0 | 1,717.6 | -7,025.7 | -28,423.6 | 8,282.6 | -15.8 | 3.0 | 1,333.9 | 0.52 | 3,669.9 |
| predictive taker, 150 sh (2nd look) | 0 | 1,335.9 | -13,393.8 | -49,572.2 | 9,721.1 | -19.8 | 1.8 | 1,192.8 | 0.54 | 5,835.4 |
| predictive veto on their trigger | 0 | 135.3 | 120.0 | -1,242.7 | 1,553.8 | 3.8 | 19.8 | 633.1 | 0.49 | 182.7 |
| predictive taker, 1 s model, margin 3 c | 0 | 392.1 | -904.0 | -5,018.5 | 2,538.7 | -10.0 | 6.4 | 574.9 | 0.58 | 662.3 |
| predictive veto on micf | 0 | 121.4 | 40.8 | -923.0 | 1,156.7 | 1.3 | 16.3 | 504.9 | 0.54 | 65.3 |
| micf (strategy winner) | 0 | 340.0 | -49.3 | -1,763.6 | 1,751.5 | -0.5 | 4.4 | 452.6 | 0.65 | 175.5 |
| predictive maker (1 s model pulls) | 0 | 1,544.1 | -457.7 | -3,396.4 | 2,290.7 | -3.5 | 2.8 | 368.7 | 0.44 | 237.1 |
| predictive maker (3 s model pulls, 2nd look) | 0 | 1,873.7 | -1,453.7 | -4,577.1 | 1,815.5 | -7.1 | 1.4 | 294.9 | 0.47 | 563.7 |
| their rule, rebuilt | 0 | 1,884.1 | -546.9 | -6,899.4 | 4,970.4 | -1.0 | -1.0 | -558.2 | 0.60 | 977.3 |

| arm | L | 10 s mk gain vs micf $/day | CI lo | CI hi |
|---|---|---|---|---|
| their rule, rebuilt | 0 | -1,011 | -2,263 | 242 |
| predictive maker (1 s model pulls) | 0 | -84 | -1,835 | 1,723 |
| predictive maker (3 s model pulls, 2nd look) | 0 | -158 | -2,201 | 1,968 |
| predictive veto on micf | 0 | 52 | -283 | 359 |
| predictive veto on their trigger | 0 | 180 | -183 | 541 |
| predictive taker, 1 s model, margin 3 c | 0 | 122 | -1,201 | 1,353 |
| **predictive taker (primary, frozen)** | 0 | 885 | -3,336 | 4,550 |
| predictive taker, refr 0.1 s (2nd look) | 0 | 881 | -4,713 | 5,670 |
| predictive taker, 150 sh (2nd look) | 0 | 740 | -5,405 | 6,261 |


### Extension of the frozen test (15:00-19:00 UTC)

| arm | L ms | fills/day | net $/day | CI lo | CI hi | net c/$ | 10 s mk c/$ | 10 s mk $/day | win | max DD $ |
|---|---|---|---|---|---|---|---|---|---|---|
| predictive taker, 1 s model, margin 3 c | -40 | 5,148.0 | 9,827.9 | -2,387.5 | 23,182.6 | 11.0 | 2.6 | 2,301.4 | 0.43 | 457.7 |
| predictive veto on their trigger | -40 | 5,154.0 | 5,274.6 | -3,718.7 | 15,250.0 | 4.9 | 1.0 | 1,080.8 | 0.46 | 533.7 |
| predictive veto on micf | -40 | 618.0 | -228.4 | -2,270.9 | 1,660.9 | -1.3 | 5.4 | 910.7 | 0.59 | 118.1 |
| micf (strategy winner) | -40 | 1,224.0 | 834.7 | -2,773.3 | 4,048.9 | 2.4 | 2.1 | 759.5 | 0.60 | 208.3 |
| predictive maker (3 s model pulls, 2nd look) | -40 | 2,184.0 | 1,112.5 | -1,901.4 | 3,849.5 | 5.7 | 1.7 | 340.6 | 0.47 | 151.6 |
| predictive maker (1 s model pulls) | -40 | 1,434.0 | 249.1 | -2,407.8 | 2,934.0 | 2.4 | 0.0 | 4.5 | 0.36 | 230.3 |
| **predictive taker (primary, frozen)** | -40 | 8,166.0 | 3,605.3 | -10,823.2 | 16,380.7 | 1.9 | -0.7 | -1,227.1 | 0.49 | 990.1 |
| predictive taker, refr 0.1 s (2nd look) | -40 | 8,964.0 | 555.1 | -19,336.2 | 17,345.3 | 0.3 | -0.9 | -1,777.7 | 0.48 | 1,554.2 |
| predictive taker, 150 sh (2nd look) | -40 | 8,016.0 | 116.4 | -28,130.9 | 25,916.3 | 0.0 | -1.6 | -5,733.1 | 0.49 | 1,913.6 |
| their rule, rebuilt | -40 | 19,632.0 | -20,103.8 | -44,565.7 | 5,560.7 | -3.6 | -2.1 | -11,568.2 | 0.53 | 3,523.6 |
| predictive taker, 1 s model, margin 3 c | 0 | 948.0 | 4,343.7 | 350.3 | 8,184.7 | 23.0 | 7.7 | 1,450.2 | 0.50 | 169.3 |
| predictive veto on their trigger | 0 | 1,428.0 | 4,053.1 | -1,411.7 | 9,605.3 | 16.2 | 3.5 | 866.4 | 0.42 | 241.1 |
| predictive veto on micf | 0 | 198.0 | 1,326.7 | 101.8 | 2,712.7 | 24.2 | 9.3 | 512.2 | 0.67 | 34.3 |
| leader A actual | 0 | 4,554.0 | 4,939.4 | -2,995.5 | 12,503.5 | 7.6 | 0.7 | 471.3 | 0.49 | 504.7 |
| micf (strategy winner) | 0 | 936.0 | 243.2 | -3,283.3 | 3,376.1 | 0.8 | 1.3 | 375.2 | 0.60 | 190.2 |
| predictive maker (3 s model pulls, 2nd look) | 0 | 1,794.0 | -110.5 | -3,365.4 | 2,785.8 | -0.6 | 1.2 | 223.9 | 0.45 | 154.6 |
| predictive maker (1 s model pulls) | 0 | 1,044.0 | -364.2 | -2,242.4 | 1,313.9 | -4.8 | -1.1 | -83.0 | 0.35 | 117.4 |
| leader B actual | 0 | 10,026.0 | 4,205.3 | -1,799.0 | 11,648.2 | 3.5 | -0.3 | -316.7 | 0.48 | 454.6 |
| **predictive taker (primary, frozen)** | 0 | 3,186.0 | 6,319.9 | -5,873.2 | 16,879.4 | 7.7 | -1.6 | -1,268.8 | 0.55 | 852.0 |
| predictive taker, refr 0.1 s (2nd look) | 0 | 3,534.0 | 6,463.1 | -9,043.3 | 19,603.2 | 7.0 | -2.0 | -1,829.3 | 0.56 | 1,197.3 |
| predictive taker, 150 sh (2nd look) | 0 | 3,102.0 | 11,828.1 | -11,809.9 | 32,030.0 | 7.2 | -2.9 | -4,756.3 | 0.54 | 1,590.7 |
| their rule, rebuilt | 0 | 17,886.0 | -23,171.5 | -47,503.2 | 1,089.4 | -4.4 | -2.5 | -13,471.1 | 0.53 | 4,039.0 |
| predictive taker, 1 s model, margin 3 c | 50 | 150.0 | 606.7 | -833.5 | 1,975.9 | 20.3 | 8.2 | 243.9 | 0.44 | 53.7 |
| predictive veto on micf | 50 | 60.0 | 444.5 | -207.3 | 1,160.2 | 24.9 | 12.0 | 213.5 | 0.70 | 32.8 |
| micf (strategy winner) | 50 | 876.0 | -435.5 | -4,011.1 | 2,755.8 | -1.5 | 0.4 | 111.9 | 0.58 | 193.1 |
| predictive maker (3 s model pulls, 2nd look) | 50 | 1,824.0 | -531.0 | -4,461.9 | 2,719.0 | -3.2 | 0.4 | 62.0 | 0.42 | 278.8 |
| predictive veto on their trigger | 50 | 210.0 | 1,443.4 | -409.4 | 3,275.5 | 44.1 | -2.9 | -94.4 | 0.43 | 92.8 |
| predictive maker (1 s model pulls) | 50 | 906.0 | -1,122.3 | -3,081.0 | 601.3 | -19.2 | -1.9 | -109.2 | 0.25 | 272.3 |
| **predictive taker (primary, frozen)** | 50 | 1,632.0 | 3,844.6 | -7,001.3 | 14,372.4 | 8.3 | -8.0 | -3,701.6 | 0.61 | 699.9 |
| predictive taker, refr 0.1 s (2nd look) | 50 | 2,190.0 | 4,238.5 | -11,671.6 | 20,170.0 | 6.9 | -7.6 | -4,717.5 | 0.61 | 1,105.6 |
| predictive taker, 150 sh (2nd look) | 50 | 1,560.0 | 6,390.7 | -15,959.5 | 27,735.8 | 7.1 | -8.2 | -7,447.1 | 0.60 | 1,592.9 |
| their rule, rebuilt | 50 | 17,040.0 | -23,182.0 | -46,250.1 | 951.2 | -4.5 | -2.8 | -14,265.3 | 0.53 | 4,037.0 |

| arm | L | 10 s mk gain vs micf $/day | CI lo | CI hi |
|---|---|---|---|---|
| their rule, rebuilt | -40 | -12,328 | -17,888 | -7,340 |
| their rule, rebuilt | 0 | -13,846 | -19,332 | -8,844 |
| their rule, rebuilt | 50 | -14,377 | -19,851 | -9,621 |
| predictive maker (1 s model pulls) | -40 | -755 | -2,750 | 928 |
| predictive maker (1 s model pulls) | 0 | -458 | -2,221 | 1,026 |
| predictive maker (1 s model pulls) | 50 | -221 | -1,714 | 1,089 |
| predictive maker (3 s model pulls, 2nd look) | -40 | -419 | -2,393 | 1,334 |
| predictive maker (3 s model pulls, 2nd look) | 0 | -151 | -2,087 | 1,618 |
| predictive maker (3 s model pulls, 2nd look) | 50 | -50 | -2,093 | 1,760 |
| predictive veto on micf | -40 | 151 | -1,032 | 1,101 |
| predictive veto on micf | 0 | 137 | -1,229 | 1,208 |
| predictive veto on micf | 50 | 102 | -1,232 | 1,178 |
| predictive veto on their trigger | -40 | 321 | -1,583 | 2,065 |
| predictive veto on their trigger | 0 | 491 | -1,257 | 2,075 |
| predictive veto on their trigger | 50 | -206 | -1,645 | 965 |
| predictive taker, 1 s model, margin 3 c | -40 | 1,542 | -346 | 3,514 |
| predictive taker, 1 s model, margin 3 c | 0 | 1,075 | -622 | 2,705 |
| predictive taker, 1 s model, margin 3 c | 50 | 132 | -1,281 | 1,310 |
| **predictive taker (primary, frozen)** | -40 | -1,987 | -9,939 | 4,088 |
| **predictive taker (primary, frozen)** | 0 | -1,644 | -5,996 | 2,287 |
| **predictive taker (primary, frozen)** | 50 | -3,814 | -11,461 | 2,220 |
| predictive taker, refr 0.1 s (2nd look) | -40 | -2,537 | -11,567 | 5,260 |
| predictive taker, refr 0.1 s (2nd look) | 0 | -2,204 | -8,249 | 3,248 |
| predictive taker, refr 0.1 s (2nd look) | 50 | -4,829 | -15,172 | 3,754 |
| predictive taker, 150 sh (2nd look) | -40 | -6,493 | -19,677 | 4,784 |
| predictive taker, 150 sh (2nd look) | 0 | -5,131 | -13,153 | 2,233 |
| predictive taker, 150 sh (2nd look) | 50 | -7,559 | -21,058 | 3,533 |


### Run 3 dev hours (transfer check before the freeze)

| arm | L ms | fills/day | net $/day | CI lo | CI hi | net c/$ | 10 s mk c/$ | 10 s mk $/day | win | max DD $ |
|---|---|---|---|---|---|---|---|---|---|---|
| **predictive taker (primary, frozen)** | -40 | 2,805.6 | 8,676.3 | -709.2 | 20,305.6 | 13.5 | 7.8 | 4,991.4 | 0.57 | 779.0 |
| predictive taker, 1 s model, margin 3 c | -40 | 1,444.8 | 5,920.8 | 1,469.2 | 11,141.8 | 24.0 | 13.7 | 3,381.4 | 0.52 | 166.4 |
| predictive veto on their trigger | -40 | 1,432.8 | 3,782.4 | 1,643.8 | 6,191.7 | 12.1 | 9.0 | 2,794.3 | 0.58 | 123.4 |
| predictive veto on micf | -40 | 494.4 | 1,463.5 | -125.9 | 3,053.7 | 9.9 | 13.4 | 1,989.4 | 0.71 | 270.7 |
| micf (strategy winner) | -40 | 614.4 | 1,343.4 | -265.5 | 2,980.3 | 6.7 | 9.6 | 1,928.2 | 0.73 | 241.8 |
| their rule, rebuilt | -40 | 2,565.6 | 5,670.5 | 1,699.9 | 9,233.6 | 8.0 | 2.7 | 1,927.0 | 0.64 | 261.3 |
| vm_book_p-0.03 | -40 | 1,838.4 | 1,008.7 | -846.6 | 2,888.3 | 7.1 | 12.4 | 1,768.1 | 0.50 | 318.0 |
| predictive maker (1 s model pulls) | -40 | 1,432.8 | 690.1 | -1,355.1 | 2,637.1 | 5.7 | 10.0 | 1,208.3 | 0.52 | 426.1 |
| **predictive taker (primary, frozen)** | 0 | 1,579.2 | 4,121.1 | -4,170.7 | 14,243.6 | 10.5 | 10.8 | 4,232.3 | 0.54 | 972.9 |
| predictive taker, 1 s model, margin 3 c | 0 | 424.8 | 2,476.0 | 856.4 | 4,256.9 | 30.6 | 26.0 | 2,101.7 | 0.53 | 165.3 |
| predictive veto on their trigger | 0 | 463.2 | 1,559.7 | 235.4 | 3,010.5 | 16.4 | 17.0 | 1,626.0 | 0.51 | 135.5 |
| predictive veto on micf | 0 | 240.0 | 809.3 | -383.9 | 1,956.1 | 11.2 | 18.5 | 1,335.6 | 0.68 | 240.0 |
| micf (strategy winner) | 0 | 432.0 | 589.6 | -806.2 | 1,981.3 | 3.9 | 8.7 | 1,322.9 | 0.74 | 236.2 |
| vm_book_p-0.03 | 0 | 1,622.4 | -749.5 | -2,959.3 | 1,158.8 | -5.5 | 8.8 | 1,202.3 | 0.45 | 899.9 |
| their rule, rebuilt | 0 | 1,941.6 | 4,357.9 | 458.2 | 7,792.1 | 7.6 | 1.6 | 936.4 | 0.65 | 333.1 |
| predictive maker (1 s model pulls) | 0 | 1,413.6 | 36.6 | -2,273.4 | 2,164.0 | 0.3 | 6.5 | 768.0 | 0.48 | 576.9 |
| **predictive taker (primary, frozen)** | 50 | 1,166.4 | 5,541.0 | -3,385.0 | 17,792.4 | 20.0 | 12.4 | 3,444.5 | 0.60 | 977.4 |
| predictive taker, 1 s model, margin 3 c | 50 | 189.6 | 1,319.7 | 171.6 | 2,666.3 | 36.4 | 40.9 | 1,480.2 | 0.57 | 83.5 |
| vm_book_p-0.03 | 50 | 1,360.8 | -486.6 | -2,704.2 | 1,549.5 | -3.9 | 8.8 | 1,094.7 | 0.47 | 656.5 |
| predictive veto on micf | 50 | 120.0 | 948.1 | 268.7 | 1,578.8 | 32.7 | 34.2 | 991.2 | 0.66 | 55.4 |
| micf (strategy winner) | 50 | 372.0 | 496.5 | -998.6 | 1,931.9 | 3.8 | 7.5 | 988.1 | 0.72 | 255.2 |
| predictive veto on their trigger | 50 | 139.2 | 436.1 | -263.2 | 1,190.8 | 16.9 | 36.8 | 949.3 | 0.48 | 115.1 |
| their rule, rebuilt | 50 | 1,682.4 | 3,365.0 | -391.6 | 6,788.4 | 6.6 | 1.4 | 729.8 | 0.64 | 345.8 |
| predictive maker (1 s model pulls) | 50 | 1,108.8 | 549.0 | -1,320.4 | 2,220.9 | 5.9 | 7.5 | 694.5 | 0.49 | 418.3 |

| arm | L | 10 s mk gain vs micf $/day | CI lo | CI hi |
|---|---|---|---|---|
| their rule, rebuilt | -40 | -1 | -912 | 960 |
| their rule, rebuilt | 0 | -386 | -1,193 | 417 |
| their rule, rebuilt | 50 | -258 | -1,004 | 501 |
| vm_book_p-0.03 | -40 | -160 | -1,474 | 1,273 |
| vm_book_p-0.03 | 0 | -121 | -1,534 | 1,353 |
| vm_book_p-0.03 | 50 | 107 | -1,106 | 1,437 |
| predictive maker (1 s model pulls) | -40 | -720 | -1,900 | 533 |
| predictive maker (1 s model pulls) | 0 | -555 | -1,685 | 558 |
| predictive maker (1 s model pulls) | 50 | -294 | -1,308 | 786 |
| predictive veto on micf | -40 | 61 | -79 | 203 |
| predictive veto on micf | 0 | 13 | -216 | 219 |
| predictive veto on micf | 50 | 3 | -338 | 370 |
| predictive veto on their trigger | -40 | 866 | 471 | 1,247 |
| predictive veto on their trigger | 0 | 303 | 27 | 580 |
| predictive veto on their trigger | 50 | -39 | -466 | 373 |
| predictive taker, 1 s model, margin 3 c | -40 | 1,453 | 599 | 2,480 |
| predictive taker, 1 s model, margin 3 c | 0 | 779 | -115 | 2,018 |
| predictive taker, 1 s model, margin 3 c | 50 | 492 | -423 | 1,539 |
| **predictive taker (primary, frozen)** | -40 | 3,063 | -2,870 | 9,966 |
| **predictive taker (primary, frozen)** | 0 | 2,909 | -2,246 | 9,198 |
| **predictive taker (primary, frozen)** | 50 | 2,456 | -2,264 | 8,418 |


### Run 2 select hours (selection)

| arm | L ms | fills/day | net $/day | CI lo | CI hi | net c/$ | 10 s mk c/$ | 10 s mk $/day | win | max DD $ |
|---|---|---|---|---|---|---|---|---|---|---|
| **predictive taker (primary, frozen)** | -40 | 3,870.0 | 14,609.3 | 3,351.4 | 28,611.1 | 13.3 | 4.6 | 5,087.9 | 0.68 | 915.2 |
| predictive taker, 1 s model, margin 3 c | -40 | 1,658.0 | 6,268.2 | 1,793.6 | 11,590.4 | 17.6 | 8.9 | 3,174.3 | 0.59 | 545.1 |
| predictive veto on their trigger | -40 | 1,238.0 | 2,143.2 | 130.2 | 4,265.3 | 8.5 | 8.4 | 2,114.6 | 0.56 | 435.4 |
| predictive veto on micf | -40 | 544.0 | 2,666.9 | 1,210.8 | 4,116.1 | 17.8 | 11.8 | 1,768.5 | 0.71 | 101.6 |
| micf (strategy winner) | -40 | 848.0 | 3,964.3 | 2,344.4 | 5,706.9 | 14.9 | 5.4 | 1,432.4 | 0.74 | 93.3 |
| their rule, rebuilt | -40 | 3,742.0 | 3,651.3 | -2,503.9 | 9,880.5 | 3.6 | 0.5 | 510.0 | 0.59 | 905.8 |
| predictive maker (1 s model pulls) | -40 | 2,148.0 | 1,047.9 | -728.9 | 3,009.7 | 5.8 | 1.9 | 340.6 | 0.53 | 270.2 |
| **predictive taker (primary, frozen)** | 0 | 2,642.0 | 17,688.0 | 3,966.2 | 36,427.2 | 22.2 | 4.3 | 3,434.9 | 0.75 | 410.0 |
| leader B actual | 0 | 10,904.0 | 4,167.9 | -1,454.6 | 10,969.5 | 3.0 | 1.6 | 2,211.0 | 0.49 | 582.8 |
| predictive taker, 1 s model, margin 3 c | 0 | 574.0 | 4,175.1 | 1,353.8 | 7,548.2 | 28.6 | 14.3 | 2,081.9 | 0.69 | 149.3 |
| predictive veto on their trigger | 0 | 350.0 | 1,113.5 | -236.1 | 2,270.1 | 15.7 | 21.0 | 1,496.2 | 0.52 | 164.1 |
| predictive veto on micf | 0 | 230.0 | 1,828.2 | 933.9 | 2,787.7 | 31.0 | 21.4 | 1,263.5 | 0.75 | 52.7 |
| leader A actual | 0 | 5,454.0 | 1,737.7 | -2,068.5 | 5,737.6 | 2.5 | 1.5 | 1,049.4 | 0.46 | 1,055.0 |
| predictive maker (1 s model pulls) | 0 | 1,966.0 | 1,718.5 | 222.3 | 3,470.0 | 10.9 | 5.9 | 933.3 | 0.54 | 139.1 |
| micf (strategy winner) | 0 | 714.0 | 3,131.2 | 1,498.5 | 4,863.3 | 13.3 | 3.5 | 816.2 | 0.74 | 96.5 |
| their rule, rebuilt | 0 | 3,096.0 | 2,309.5 | -3,325.7 | 8,221.4 | 2.6 | -0.8 | -725.0 | 0.59 | 1,024.6 |
| **predictive taker (primary, frozen)** | 50 | 1,950.0 | 11,843.9 | 1,708.1 | 23,882.8 | 20.3 | 3.9 | 2,292.2 | 0.72 | 786.3 |
| predictive taker, 1 s model, margin 3 c | 50 | 246.0 | 2,164.0 | 613.8 | 4,248.5 | 29.1 | 13.7 | 1,017.9 | 0.80 | 68.7 |
| predictive veto on micf | 50 | 72.0 | 924.9 | 354.8 | 1,540.9 | 54.6 | 35.6 | 602.2 | 0.78 | 19.9 |
| predictive veto on their trigger | 50 | 74.0 | 664.6 | 58.4 | 1,266.1 | 44.6 | 39.7 | 591.7 | 0.62 | 37.6 |
| micf (strategy winner) | 50 | 600.0 | 2,477.9 | 1,051.4 | 3,905.5 | 11.8 | 1.7 | 367.9 | 0.74 | 98.8 |
| predictive maker (1 s model pulls) | 50 | 1,600.0 | -499.0 | -2,257.7 | 1,236.4 | -3.7 | -4.7 | -637.9 | 0.50 | 517.2 |
| their rule, rebuilt | 50 | 2,758.0 | 1,818.1 | -3,396.7 | 7,519.4 | 2.2 | -1.6 | -1,317.6 | 0.59 | 992.6 |

| arm | L | 10 s mk gain vs micf $/day | CI lo | CI hi |
|---|---|---|---|---|
| their rule, rebuilt | -40 | -922 | -2,003 | 158 |
| their rule, rebuilt | 0 | -1,541 | -2,557 | -545 |
| their rule, rebuilt | 50 | -1,686 | -2,728 | -666 |
| predictive maker (1 s model pulls) | -40 | -1,092 | -2,632 | 289 |
| predictive maker (1 s model pulls) | 0 | 117 | -1,243 | 1,459 |
| predictive maker (1 s model pulls) | 50 | -1,006 | -2,814 | 592 |
| predictive veto on micf | -40 | 336 | -52 | 736 |
| predictive veto on micf | 0 | 447 | -100 | 987 |
| predictive veto on micf | 50 | 234 | -383 | 821 |
| predictive veto on their trigger | -40 | 682 | 42 | 1,336 |
| predictive veto on their trigger | 0 | 680 | 51 | 1,350 |
| predictive veto on their trigger | 50 | 224 | -473 | 885 |
| predictive taker, 1 s model, margin 3 c | -40 | 1,742 | 554 | 2,962 |
| predictive taker, 1 s model, margin 3 c | 0 | 1,266 | 290 | 2,380 |
| predictive taker, 1 s model, margin 3 c | 50 | 650 | -138 | 1,393 |
| **predictive taker (primary, frozen)** | -40 | 3,655 | 1,307 | 5,979 |
| **predictive taker (primary, frozen)** | 0 | 2,619 | 489 | 4,894 |
| **predictive taker (primary, frozen)** | 50 | 1,924 | -927 | 4,764 |


### Makers, run 2 select

| arm | L ms | fills/day | net $/day | CI lo | CI hi | net c/$ | 10 s mk c/$ | 10 s mk $/day | win | max DD $ |
|---|---|---|---|---|---|---|---|---|---|---|
| micf (strategy winner) | -40 | 848.0 | 3,964.3 | 2,344.4 | 5,706.9 | 14.9 | 5.4 | 1,432.4 | 0.74 | 93.3 |
| strategy maker (microprice pulls) | -40 | 2,786.0 | 1,414.2 | -414.5 | 3,364.8 | 5.7 | 3.6 | 891.6 | 0.48 | 296.3 |
| predictive maker (3 s model pulls, 2nd look) | -40 | 2,598.0 | 943.6 | -1,453.8 | 3,297.0 | 4.0 | 3.4 | 802.9 | 0.54 | 486.9 |
| predictive maker (1 s model pulls) | -40 | 2,148.0 | 1,047.9 | -728.9 | 3,009.7 | 5.8 | 1.9 | 340.6 | 0.53 | 270.2 |
| predictive maker (3 s model pulls, 2nd look) | 0 | 2,208.0 | 1,525.7 | -525.8 | 3,768.8 | 7.2 | 5.3 | 1,118.5 | 0.55 | 347.8 |
| predictive maker (1 s model pulls) | 0 | 1,966.0 | 1,718.5 | 222.3 | 3,470.0 | 10.9 | 5.9 | 933.3 | 0.54 | 139.1 |
| micf (strategy winner) | 0 | 714.0 | 3,131.2 | 1,498.5 | 4,863.3 | 13.3 | 3.5 | 816.2 | 0.74 | 96.5 |
| strategy maker (microprice pulls) | 0 | 2,770.0 | 387.3 | -1,365.4 | 2,504.9 | 1.7 | 1.7 | 393.5 | 0.47 | 542.7 |
| micf (strategy winner) | 50 | 600.0 | 2,477.9 | 1,051.4 | 3,905.5 | 11.8 | 1.7 | 367.9 | 0.74 | 98.8 |
| predictive maker (3 s model pulls, 2nd look) | 50 | 2,578.0 | -900.8 | -2,953.0 | 1,333.5 | -4.0 | -0.7 | -147.0 | 0.49 | 892.4 |
| predictive maker (1 s model pulls) | 50 | 1,600.0 | -499.0 | -2,257.7 | 1,236.4 | -3.7 | -4.7 | -637.9 | 0.50 | 517.2 |
| strategy maker (microprice pulls) | 50 | 3,634.0 | -2,330.0 | -4,246.1 | 14.0 | -6.8 | -2.3 | -794.8 | 0.45 | 1,218.1 |

| arm | L | 10 s mk gain vs micf $/day | CI lo | CI hi |
|---|---|---|---|---|
| strategy maker (microprice pulls) | -40 | -541 | -1,758 | 623 |
| strategy maker (microprice pulls) | 0 | -423 | -1,688 | 793 |
| strategy maker (microprice pulls) | 50 | -1,163 | -2,689 | 208 |
| predictive maker (1 s model pulls) | -40 | -1,092 | -2,632 | 289 |
| predictive maker (1 s model pulls) | 0 | 117 | -1,243 | 1,459 |
| predictive maker (1 s model pulls) | 50 | -1,006 | -2,814 | 592 |
| predictive maker (3 s model pulls, 2nd look) | -40 | -629 | -1,953 | 686 |
| predictive maker (3 s model pulls, 2nd look) | 0 | 302 | -1,080 | 1,655 |
| predictive maker (3 s model pulls, 2nd look) | 50 | -515 | -1,892 | 802 |


### Makers, run 3 dev

| arm | L ms | fills/day | net $/day | CI lo | CI hi | net c/$ | 10 s mk c/$ | 10 s mk $/day | win | max DD $ |
|---|---|---|---|---|---|---|---|---|---|---|
| micf (strategy winner) | -40 | 614.4 | 1,343.4 | -265.5 | 2,980.3 | 6.7 | 9.6 | 1,928.2 | 0.73 | 241.8 |
| strategy maker (microprice pulls) | -40 | 1,663.2 | 1,240.3 | -619.9 | 3,008.0 | 7.6 | 8.4 | 1,369.7 | 0.48 | 206.3 |
| predictive maker (3 s model pulls, 2nd look) | -40 | 1,814.4 | 312.1 | -2,468.2 | 2,953.2 | 1.9 | 8.1 | 1,358.9 | 0.53 | 512.2 |
| predictive maker (1 s model pulls) | -40 | 1,432.8 | 690.1 | -1,355.1 | 2,637.1 | 5.7 | 10.0 | 1,208.3 | 0.52 | 426.1 |
| micf (strategy winner) | 0 | 432.0 | 589.6 | -806.2 | 1,981.3 | 3.9 | 8.7 | 1,322.9 | 0.74 | 236.2 |
| predictive maker (3 s model pulls, 2nd look) | 0 | 1,620.0 | 193.1 | -2,278.2 | 2,723.2 | 1.4 | 7.2 | 1,020.7 | 0.50 | 337.7 |
| strategy maker (microprice pulls) | 0 | 1,660.8 | 214.4 | -1,944.7 | 2,111.9 | 1.3 | 4.6 | 791.0 | 0.48 | 362.2 |
| predictive maker (1 s model pulls) | 0 | 1,413.6 | 36.6 | -2,273.4 | 2,164.0 | 0.3 | 6.5 | 768.0 | 0.48 | 576.9 |
| micf (strategy winner) | 50 | 372.0 | 496.5 | -998.6 | 1,931.9 | 3.8 | 7.5 | 988.1 | 0.72 | 255.2 |
| predictive maker (3 s model pulls, 2nd look) | 50 | 1,646.4 | 460.9 | -2,105.5 | 2,800.6 | 3.1 | 6.3 | 917.5 | 0.50 | 357.0 |
| predictive maker (1 s model pulls) | 50 | 1,108.8 | 549.0 | -1,320.4 | 2,220.9 | 5.9 | 7.5 | 694.5 | 0.49 | 418.3 |
| strategy maker (microprice pulls) | 50 | 2,169.6 | 694.9 | -1,719.2 | 3,138.7 | 2.8 | 1.6 | 401.4 | 0.48 | 511.7 |

| arm | L | 10 s mk gain vs micf $/day | CI lo | CI hi |
|---|---|---|---|---|
| strategy maker (microprice pulls) | -40 | -558 | -1,619 | 615 |
| strategy maker (microprice pulls) | 0 | -532 | -1,430 | 411 |
| strategy maker (microprice pulls) | 50 | -587 | -1,742 | 593 |
| predictive maker (1 s model pulls) | -40 | -720 | -1,900 | 533 |
| predictive maker (1 s model pulls) | 0 | -555 | -1,685 | 558 |
| predictive maker (1 s model pulls) | 50 | -294 | -1,308 | 786 |
| predictive maker (3 s model pulls, 2nd look) | -40 | -569 | -1,937 | 809 |
| predictive maker (3 s model pulls, 2nd look) | 0 | -302 | -1,442 | 982 |
| predictive maker (3 s model pulls, 2nd look) | 50 | -71 | -1,597 | 1,382 |


### Makers, run 3 test

| arm | L ms | fills/day | net $/day | CI lo | CI hi | net c/$ | 10 s mk c/$ | 10 s mk $/day | win | max DD $ |
|---|---|---|---|---|---|---|---|---|---|---|
| predictive maker (3 s model pulls, 2nd look) | -40 | 2,127.0 | -115.1 | -3,087.5 | 3,012.7 | -0.5 | 8.2 | 1,712.8 | 0.51 | 236.0 |
| micf (strategy winner) | -40 | 555.2 | -20.8 | -2,415.6 | 2,330.7 | -0.1 | 7.8 | 1,402.5 | 0.66 | 221.1 |
| predictive maker (1 s model pulls) | -40 | 1,651.7 | -1,057.8 | -4,072.3 | 1,954.5 | -7.1 | 5.5 | 813.1 | 0.44 | 477.9 |
| strategy maker (microprice pulls) | -40 | 1,800.9 | 822.9 | -1,316.0 | 3,390.7 | 5.1 | 1.5 | 244.5 | 0.44 | 307.4 |
| micf (strategy winner) | 0 | 392.1 | -34.5 | -2,108.8 | 2,062.6 | -0.3 | 6.6 | 895.7 | 0.67 | 177.3 |
| predictive maker (1 s model pulls) | 0 | 1,544.1 | -457.7 | -3,396.4 | 2,290.7 | -3.5 | 2.8 | 368.7 | 0.44 | 237.1 |
| predictive maker (3 s model pulls, 2nd look) | 0 | 1,873.7 | -1,453.7 | -4,577.1 | 1,815.5 | -7.1 | 1.4 | 294.9 | 0.47 | 563.7 |
| strategy maker (microprice pulls) | 0 | 2,036.8 | -910.0 | -3,798.4 | 1,834.8 | -4.5 | -3.9 | -791.5 | 0.43 | 337.5 |
| micf (strategy winner) | 50 | 350.5 | -266.8 | -2,357.4 | 1,892.6 | -2.2 | 5.5 | 670.8 | 0.63 | 220.3 |
| predictive maker (1 s model pulls) | 50 | 1,204.0 | -209.1 | -2,319.9 | 1,858.2 | -2.0 | -1.8 | -188.5 | 0.46 | 259.2 |
| predictive maker (3 s model pulls, 2nd look) | 50 | 1,783.5 | -1,695.8 | -4,589.5 | 1,012.6 | -9.9 | -2.9 | -491.4 | 0.48 | 536.2 |
| strategy maker (microprice pulls) | 50 | 3,119.4 | -401.0 | -3,283.7 | 2,753.4 | -1.3 | -3.3 | -1,063.1 | 0.43 | 426.3 |

| arm | L | 10 s mk gain vs micf $/day | CI lo | CI hi |
|---|---|---|---|---|
| strategy maker (microprice pulls) | -40 | -1,158 | -2,672 | 287 |
| strategy maker (microprice pulls) | 0 | -1,687 | -3,758 | 298 |
| strategy maker (microprice pulls) | 50 | -1,734 | -3,816 | 262 |
| predictive maker (1 s model pulls) | -40 | -589 | -2,170 | 994 |
| predictive maker (1 s model pulls) | 0 | -527 | -2,360 | 1,341 |
| predictive maker (1 s model pulls) | 50 | -859 | -2,142 | 314 |
| predictive maker (3 s model pulls, 2nd look) | -40 | 310 | -1,104 | 1,862 |
| predictive maker (3 s model pulls, 2nd look) | 0 | -601 | -2,687 | 1,561 |
| predictive maker (3 s model pulls, 2nd look) | 50 | -1,162 | -2,784 | 400 |

