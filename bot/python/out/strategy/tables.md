held-out: 143 markets, 11.9 h

## Main (hold 150 ms)

| arm | L ms | fills/day | net $/day | 95% CI $/day | net c/$ | 10 s mk c/$ | win | max DD $ |
|---|---|---|---|---|---|---|---|---|
| (a) their rule, rebuilt (microprice trigger) | 50 | 2,771 | +1,827 | -3,435 .. +6,983 | +2.2 | -1.6 | 0.59 | 993 |
| (a) their rule, rebuilt (microprice trigger) | 100 | 2,634 | +1,677 | -3,771 .. +6,720 | +2.1 | -1.7 | 0.58 | 994 |
| (a) their rule, rebuilt (microprice trigger) | 150 | 2,578 | +1,057 | -4,385 .. +6,104 | +1.3 | -2.0 | 0.58 | 1,048 |
| (a') their rule, first read (3 s spot move) | 50 | 14,394 | -15,163 | -27,697 .. -2,899 | -3.7 | -4.3 | 0.50 | 9,063 |
| (a') their rule, first read (3 s spot move) | 100 | 14,227 | -16,193 | -28,220 .. -4,221 | -4.0 | -4.3 | 0.50 | 9,425 |
| (a') their rule, first read (3 s spot move) | 150 | 14,068 | -14,701 | -26,548 .. -2,545 | -3.6 | -4.3 | 0.50 | 8,733 |
| (b) their rule on the perp mid | 50 | 1,813 | +663 | -3,596 .. +5,303 | +1.1 | -2.9 | 0.61 | 605 |
| (b) their rule on the perp mid | 100 | 1,762 | +351 | -3,973 .. +4,769 | +0.6 | -3.1 | 0.61 | 591 |
| (b) their rule on the perp mid | 150 | 1,732 | +76 | -4,221 .. +4,465 | +0.1 | -3.2 | 0.61 | 617 |
| **microprice trigger + fair filter (micf)** | 50 | 604 | +2,495 | +1,058 .. +3,886 | +11.8 | +1.7 | 0.74 | 99 |
| **microprice trigger + fair filter (micf)** | 100 | 568 | +2,360 | +1,060 .. +3,607 | +11.7 | +1.0 | 0.73 | 111 |
| **microprice trigger + fair filter (micf)** | 150 | 544 | +2,161 | +847 .. +3,416 | +10.9 | +0.5 | 0.73 | 103 |
| microprice trigger, selective | 50 | 258 | +44 | -1,009 .. +1,007 | +0.6 | +4.6 | 0.63 | 419 |
| microprice trigger, selective | 100 | 234 | -225 | -1,282 .. +706 | -3.0 | +2.9 | 0.62 | 475 |
| microprice trigger, selective | 150 | 224 | -275 | -1,350 .. +634 | -3.7 | +0.9 | 0.61 | 455 |
| momentum, tuned (spot mid 0.2 s) | 50 | 262 | +75 | -1,074 .. +940 | +0.9 | +3.8 | 0.67 | 195 |
| momentum, tuned (spot mid 0.2 s) | 100 | 238 | +69 | -1,057 .. +919 | +0.9 | +2.8 | 0.67 | 195 |
| momentum, tuned (spot mid 0.2 s) | 150 | 228 | +39 | -1,035 .. +875 | +0.5 | +1.1 | 0.68 | 182 |
| fair taker, 60 sh (inv. 1) | 50 | 1,635 | +2,701 | -1,500 .. +7,388 | +5.2 | -2.8 | 0.64 | 947 |
| fair taker, 60 sh (inv. 1) | 100 | 1,563 | +2,370 | -1,772 .. +6,827 | +4.8 | -3.0 | 0.63 | 922 |
| fair taker, 60 sh (inv. 1) | 150 | 1,539 | +2,024 | -1,975 .. +6,516 | +4.1 | -3.3 | 0.62 | 1,027 |
| fair taker, depth-sized | 50 | 207 | -208 | -7,037 .. +4,276 | -1.4 | +4.1 | 0.49 | 1,814 |
| fair taker, depth-sized | 100 | 195 | -687 | -6,962 .. +3,490 | -4.6 | +0.6 | 0.49 | 1,700 |
| fair taker, depth-sized | 150 | 189 | -1,386 | -8,127 .. +2,907 | -9.0 | -1.6 | 0.49 | 1,851 |
| fair taker refit on v2 | 50 | 171 | +501 | -3,353 .. +3,859 | +2.4 | +0.8 | 0.60 | 827 |
| fair taker refit on v2 | 100 | 155 | -637 | -4,514 .. +2,666 | -3.3 | -3.5 | 0.60 | 825 |
| fair taker refit on v2 | 150 | 147 | -455 | -4,025 .. +2,425 | -2.4 | -2.7 | 0.59 | 685 |
| fair taker + microprice buckets | 50 | 189 | +129 | -4,047 .. +3,774 | +0.6 | +1.0 | 0.59 | 909 |
| fair taker + microprice buckets | 100 | 175 | -946 | -4,860 .. +2,439 | -4.5 | -3.0 | 0.59 | 886 |
| fair taker + microprice buckets | 150 | 165 | -819 | -4,324 .. +2,110 | -3.9 | -3.0 | 0.59 | 730 |
| fair taker + perp imbalance (inv. 3) | 50 | 1,678 | -965 | -18,855 .. +13,256 | -0.9 | -6.7 | 0.56 | 4,367 |
| fair taker + perp imbalance (inv. 3) | 100 | 1,633 | -1,343 | -18,375 .. +12,681 | -1.3 | -6.5 | 0.55 | 4,502 |
| fair taker + perp imbalance (inv. 3) | 150 | 1,609 | -1,761 | -19,464 .. +12,367 | -1.7 | -6.2 | 0.54 | 4,685 |
| maker, fair quotes, perp pulls (inv. 2) | 50 | 3,637 | -3,447 | -5,683 .. -1,199 | -9.7 | -4.3 | 0.44 | 1,724 |
| maker, fair quotes, perp pulls (inv. 2) | 100 | 4,252 | -3,231 | -5,245 .. -1,210 | -8.2 | -4.8 | 0.44 | 1,617 |
| maker, fair quotes, perp pulls (inv. 2) | 150 | 4,781 | -3,380 | -5,691 .. -1,166 | -8.1 | -4.7 | 0.43 | 1,934 |
| maker, microprice pulls | 50 | 3,639 | -2,427 | -4,436 .. -366 | -7.0 | -2.4 | 0.44 | 1,218 |
| maker, microprice pulls | 100 | 4,143 | -2,411 | -4,424 .. -485 | -6.4 | -2.9 | 0.44 | 1,291 |
| maker, microprice pulls | 150 | 4,636 | -2,513 | -4,789 .. -284 | -6.1 | -3.6 | 0.43 | 1,413 |
| maker, book-anchored (inv. 2b) | 50 | 28,522 | -9,293 | -11,940 .. -6,473 | -3.1 | -2.6 | 0.45 | 4,659 |
| maker, book-anchored (inv. 2b) | 100 | 27,406 | -10,161 | -12,874 .. -7,209 | -3.5 | -3.2 | 0.46 | 5,045 |
| maker, book-anchored (inv. 2b) | 150 | 37,374 | -17,593 | -20,497 .. -14,584 | -3.6 | -3.4 | 0.46 | 8,736 |
| micf, 150 sh, 50 ms window (ceiling, 2nd look) | 50 | 564 | +5,840 | +2,863 .. +8,835 | +13.3 | +1.9 | 0.76 | 247 |
| micf, 150 sh, 50 ms window (ceiling, 2nd look) | 100 | 528 | +5,420 | +2,685 .. +8,308 | +12.8 | +1.6 | 0.75 | 300 |
| micf, 150 sh, 50 ms window (ceiling, 2nd look) | 150 | 508 | +5,238 | +2,411 .. +7,989 | +12.4 | +1.2 | 0.75 | 309 |
| micf + books agree, 150 sh (post-hoc, 3rd look) | 50 | 377 | +4,160 | +1,834 .. +6,407 | +14.3 | +3.8 | 0.76 | 141 |
| micf + books agree, 150 sh (post-hoc, 3rd look) | 100 | 356 | +3,729 | +1,504 .. +5,943 | +12.8 | +2.6 | 0.77 | 229 |
| micf + books agree, 150 sh (post-hoc, 3rd look) | 150 | 342 | +3,670 | +1,341 .. +5,941 | +12.5 | +2.1 | 0.76 | 212 |
| (a+) their rule + books-agree filter (post-hoc) | 50 | 2,050 | +738 | -3,288 .. +4,089 | +1.2 | -0.8 | 0.59 | 997 |
| (a+) their rule + books-agree filter (post-hoc) | 100 | 1,931 | +455 | -3,849 .. +4,005 | +0.8 | -1.0 | 0.59 | 1,046 |
| (a+) their rule + books-agree filter (post-hoc) | 150 | 1,877 | -9 | -4,331 .. +3,586 | -0.0 | -1.4 | 0.58 | 1,064 |
| (c) leader A actual, all fills | actual | 5,492 | +1,750 | -1,911 .. +5,924 | +2.5 | +1.5 | 0.46 | 1,055 |
| (c) leader B actual, all fills | actual | 10,980 | +4,197 | -2,076 .. +10,190 | +3.0 | +1.6 | 0.49 | 583 |


## Infrastructure points (L = -40 split Tokyo build, 0 Dublin)

| arm | L ms | fills/day | net $/day | 95% CI $/day | net c/$ | 10 s mk c/$ | win | max DD $ |
|---|---|---|---|---|---|---|---|---|
| (a) their rule, rebuilt (microprice trigger) | -40 | 3,760 | +3,595 | -2,126 .. +9,516 | +3.5 | +0.5 | 0.59 | 906 |
| (a) their rule, rebuilt (microprice trigger) | 0 | 3,112 | +2,293 | -3,196 .. +7,752 | +2.6 | -0.8 | 0.59 | 1,025 |
| (a') their rule, first read (3 s spot move) | -40 | 14,756 | -14,869 | -27,478 .. -2,429 | -3.5 | -4.2 | 0.50 | 9,168 |
| (a') their rule, first read (3 s spot move) | 0 | 14,575 | -14,858 | -27,486 .. -2,413 | -3.6 | -4.3 | 0.50 | 9,015 |
| (b) their rule on the perp mid | -40 | 2,219 | +1,685 | -2,867 .. +6,833 | +2.5 | -1.6 | 0.62 | 597 |
| (b) their rule on the perp mid | 0 | 1,915 | +1,062 | -3,216 .. +6,088 | +1.7 | -2.5 | 0.61 | 563 |
| **microprice trigger + fair filter (micf)** | -40 | 852 | +3,943 | +2,240 .. +5,754 | +14.7 | +5.3 | 0.74 | 93 |
| **microprice trigger + fair filter (micf)** | 0 | 719 | +3,153 | +1,486 .. +4,838 | +13.3 | +3.5 | 0.74 | 97 |
| microprice trigger, selective | -40 | 429 | +683 | -694 .. +1,780 | +5.9 | +8.2 | 0.65 | 384 |
| microprice trigger, selective | 0 | 326 | +446 | -611 .. +1,363 | +4.7 | +7.2 | 0.64 | 332 |
| momentum, tuned (spot mid 0.2 s) | -40 | 417 | +143 | -1,202 .. +1,239 | +1.2 | +5.5 | 0.65 | 237 |
| momentum, tuned (spot mid 0.2 s) | 0 | 310 | +18 | -1,268 .. +1,001 | +0.2 | +4.4 | 0.65 | 285 |
| fair taker, 60 sh (inv. 1) | -40 | 1,861 | +3,891 | -899 .. +8,996 | +6.8 | -1.2 | 0.65 | 855 |
| fair taker, 60 sh (inv. 1) | 0 | 1,722 | +3,209 | -1,366 .. +8,124 | +5.9 | -1.8 | 0.64 | 881 |
| fair taker, depth-sized | -40 | 240 | +2,338 | -5,155 .. +7,912 | +12.0 | +11.4 | 0.59 | 1,805 |
| fair taker, depth-sized | 0 | 238 | +910 | -6,417 .. +6,072 | +5.2 | +8.1 | 0.56 | 1,879 |
| fair taker refit on v2 | -40 | 220 | +2,164 | -2,075 .. +6,094 | +8.8 | +5.5 | 0.67 | 848 |
| fair taker refit on v2 | 0 | 195 | +1,094 | -3,224 .. +4,945 | +4.9 | +2.6 | 0.64 | 904 |
| fair taker + microprice buckets | -40 | 242 | +2,133 | -2,964 .. +6,546 | +7.9 | +5.2 | 0.65 | 995 |
| fair taker + microprice buckets | 0 | 213 | +982 | -3,794 .. +4,902 | +4.0 | +2.2 | 0.62 | 993 |
| fair taker + perp imbalance (inv. 3) | -40 | 1,891 | +1,157 | -17,296 .. +16,167 | +1.0 | -4.7 | 0.58 | 3,705 |
| fair taker + perp imbalance (inv. 3) | 0 | 1,770 | +340 | -17,582 .. +14,639 | +0.3 | -5.4 | 0.57 | 3,906 |
| maker, fair quotes, perp pulls (inv. 2) | -40 | 2,628 | +1,276 | -703 .. +3,387 | +5.6 | +3.4 | 0.48 | 361 |
| maker, fair quotes, perp pulls (inv. 2) | 0 | 2,729 | -189 | -2,303 .. +2,089 | -0.8 | -0.3 | 0.46 | 805 |
| maker, microprice pulls | -40 | 2,803 | +1,429 | -461 .. +3,528 | +5.8 | +3.6 | 0.48 | 296 |
| maker, microprice pulls | 0 | 2,785 | +401 | -1,502 .. +2,528 | +1.7 | +1.7 | 0.47 | 543 |
| maker, book-anchored (inv. 2b) | -40 | 28,645 | -1,748 | -4,431 .. +1,295 | -0.7 | -0.6 | 0.45 | 1,239 |
| maker, book-anchored (inv. 2b) | 0 | 28,053 | -4,594 | -7,256 .. -1,654 | -1.7 | -1.6 | 0.45 | 2,393 |
| micf, 150 sh, 50 ms window (ceiling, 2nd look) | -40 | 804 | +8,439 | +4,554 .. +12,136 | +15.6 | +5.5 | 0.75 | 248 |
| micf, 150 sh, 50 ms window (ceiling, 2nd look) | 0 | 675 | +6,555 | +2,921 .. +10,049 | +13.5 | +3.2 | 0.76 | 254 |
| micf + books agree, 150 sh (post-hoc, 3rd look) | -40 | 584 | +6,594 | +3,669 .. +9,500 | +17.1 | +6.6 | 0.76 | 135 |
| micf + books agree, 150 sh (post-hoc, 3rd look) | 0 | 475 | +5,058 | +2,197 .. +7,788 | +15.1 | +4.6 | 0.76 | 161 |
| (a+) their rule + books-agree filter (post-hoc) | -40 | 2,872 | +2,693 | -2,130 .. +6,775 | +3.5 | +1.3 | 0.60 | 812 |
| (a+) their rule + books-agree filter (post-hoc) | 0 | 2,318 | +1,386 | -2,825 .. +4,834 | +2.1 | -0.1 | 0.59 | 1,052 |


## Sensitivity: 50 ms race window, half of each level (takers only; makers unchanged)

| arm | L ms | fills/day | net $/day | 95% CI $/day | net c/$ | 10 s mk c/$ | win | max DD $ |
|---|---|---|---|---|---|---|---|---|
| (a) their rule, rebuilt (microprice trigger) | 0 | 2,739 | +1,334 | -3,431 .. +5,878 | +1.9 | -1.6 | 0.59 | 860 |
| (a) their rule, rebuilt (microprice trigger) | 50 | 2,564 | +1,431 | -3,324 .. +5,943 | +2.1 | -1.8 | 0.59 | 859 |
| (a) their rule, rebuilt (microprice trigger) | 100 | 2,536 | +809 | -4,142 .. +5,453 | +1.2 | -2.1 | 0.58 | 938 |
| (a') their rule, first read (3 s spot move) | 0 | 14,360 | -15,776 | -27,235 .. -4,176 | -4.2 | -4.7 | 0.50 | 9,178 |
| (a') their rule, first read (3 s spot move) | 50 | 14,189 | -15,876 | -27,394 .. -4,327 | -4.2 | -4.7 | 0.50 | 9,229 |
| (a') their rule, first read (3 s spot move) | 100 | 14,013 | -15,854 | -27,036 .. -4,359 | -4.3 | -4.8 | 0.50 | 9,183 |
| (b) their rule on the perp mid | 0 | 1,803 | +76 | -3,742 .. +4,171 | +0.1 | -3.6 | 0.61 | 633 |
| (b) their rule on the perp mid | 50 | 1,754 | -210 | -3,989 .. +3,662 | -0.4 | -3.6 | 0.61 | 675 |
| (b) their rule on the perp mid | 100 | 1,726 | -497 | -4,256 .. +3,438 | -0.9 | -3.7 | 0.61 | 732 |
| **microprice trigger + fair filter (micf)** | 0 | 596 | +2,078 | +769 .. +3,373 | +11.0 | +1.2 | 0.73 | 93 |
| **microprice trigger + fair filter (micf)** | 50 | 552 | +2,191 | +1,032 .. +3,339 | +12.2 | +1.0 | 0.74 | 84 |
| **microprice trigger + fair filter (micf)** | 100 | 536 | +1,962 | +840 .. +3,032 | +11.0 | +0.4 | 0.73 | 103 |
| microprice trigger, selective | 0 | 254 | -69 | -1,078 .. +791 | -1.0 | +4.7 | 0.62 | 393 |
| microprice trigger, selective | 50 | 226 | -3 | -897 .. +775 | -0.0 | +3.7 | 0.63 | 318 |
| microprice trigger, selective | 100 | 218 | -237 | -1,113 .. +554 | -3.6 | +0.9 | 0.62 | 374 |
| momentum, tuned (spot mid 0.2 s) | 0 | 274 | -6 | -1,062 .. +801 | -0.1 | +3.2 | 0.66 | 206 |
| momentum, tuned (spot mid 0.2 s) | 50 | 240 | +61 | -909 .. +807 | +0.9 | +2.4 | 0.66 | 191 |
| momentum, tuned (spot mid 0.2 s) | 100 | 226 | -61 | -997 .. +724 | -0.9 | +0.6 | 0.66 | 182 |
| fair taker, 60 sh (inv. 1) | 0 | 1,569 | +1,017 | -2,791 .. +5,181 | +2.3 | -4.0 | 0.63 | 1,229 |
| fair taker, 60 sh (inv. 1) | 50 | 1,502 | +844 | -2,858 .. +4,907 | +2.0 | -4.8 | 0.62 | 1,153 |
| fair taker, 60 sh (inv. 1) | 100 | 1,472 | +478 | -3,283 .. +4,431 | +1.1 | -5.2 | 0.61 | 1,185 |
| fair taker, depth-sized | 0 | 205 | +1,076 | -1,832 .. +3,327 | +10.9 | +6.2 | 0.55 | 777 |
| fair taker, depth-sized | 50 | 169 | +287 | -2,728 .. +2,490 | +3.0 | +0.1 | 0.51 | 801 |
| fair taker, depth-sized | 100 | 177 | -9 | -2,852 .. +2,070 | -0.1 | -2.2 | 0.49 | 770 |
| fair taker refit on v2 | 0 | 171 | +348 | -2,284 .. +2,738 | +2.2 | -1.9 | 0.61 | 559 |
| fair taker refit on v2 | 50 | 155 | -403 | -2,952 .. +1,827 | -2.7 | -4.9 | 0.60 | 577 |
| fair taker refit on v2 | 100 | 143 | -942 | -3,401 .. +1,122 | -6.5 | -6.3 | 0.59 | 614 |
| fair taker + microprice buckets | 0 | 191 | +222 | -2,526 .. +2,732 | +1.3 | -2.0 | 0.60 | 578 |
| fair taker + microprice buckets | 50 | 173 | -747 | -3,328 .. +1,555 | -4.5 | -4.5 | 0.58 | 569 |
| fair taker + microprice buckets | 100 | 163 | -1,377 | -3,840 .. +735 | -8.7 | -6.2 | 0.58 | 755 |
| fair taker + perp imbalance (inv. 3) | 0 | 1,621 | -1,075 | -14,332 .. +9,860 | -1.3 | -7.1 | 0.56 | 3,627 |
| fair taker + perp imbalance (inv. 3) | 50 | 1,579 | -2,611 | -16,640 .. +8,451 | -3.2 | -8.3 | 0.55 | 4,118 |
| fair taker + perp imbalance (inv. 3) | 100 | 1,543 | -3,376 | -16,570 .. +7,255 | -4.2 | -8.3 | 0.55 | 4,077 |


## Sensitivity: 250 ms hold (makers; for takers a 250 ms hold equals L + 100 ms in the main table)

| arm | L ms | fills/day | net $/day | 95% CI $/day | net c/$ | 10 s mk c/$ | win | max DD $ |
|---|---|---|---|---|---|---|---|---|
| maker, fair quotes, perp pulls (inv. 2) | 0 | 2,717 | -83 | -2,217 .. +2,121 | -0.4 | -0.3 | 0.46 | 763 |
| maker, fair quotes, perp pulls (inv. 2) | 50 | 3,633 | -3,505 | -5,736 .. -1,237 | -10.0 | -4.3 | 0.44 | 1,754 |
| maker, fair quotes, perp pulls (inv. 2) | 100 | 4,217 | -3,297 | -5,352 .. -1,252 | -8.5 | -4.9 | 0.44 | 1,650 |
| maker, microprice pulls | 0 | 2,783 | +473 | -1,390 .. +2,594 | +2.0 | +1.7 | 0.47 | 523 |
| maker, microprice pulls | 50 | 3,641 | -2,419 | -4,428 .. -362 | -7.0 | -2.4 | 0.44 | 1,214 |
| maker, microprice pulls | 100 | 4,127 | -2,421 | -4,389 .. -470 | -6.4 | -3.1 | 0.44 | 1,309 |
| maker, book-anchored (inv. 2b) | 0 | 27,626 | -3,840 | -6,486 .. -857 | -1.5 | -1.3 | 0.45 | 2,000 |
| maker, book-anchored (inv. 2b) | 50 | 28,137 | -9,056 | -11,659 .. -6,177 | -3.1 | -2.7 | 0.45 | 4,509 |
| maker, book-anchored (inv. 2b) | 100 | 26,488 | -9,504 | -12,160 .. -6,493 | -3.5 | -3.2 | 0.46 | 4,719 |


## Sensitivity: pessimistic maker fills (crossing orders fill at once, not after the hold)

| arm | L ms | fills/day | net $/day | 95% CI $/day | net c/$ | 10 s mk c/$ | win | max DD $ |
|---|---|---|---|---|---|---|---|---|
| maker, fair quotes, perp pulls (inv. 2) | -40 | 2,818 | +1,299 | -1,003 .. +3,727 | +4.9 | +2.5 | 0.49 | 386 |
| maker, fair quotes, perp pulls (inv. 2) | 0 | 3,438 | -975 | -3,277 .. +1,134 | -2.6 | -2.2 | 0.48 | 1,030 |
| maker, fair quotes, perp pulls (inv. 2) | 50 | 4,481 | -4,237 | -6,899 .. -1,551 | -8.1 | -4.9 | 0.46 | 2,118 |
| maker, microprice pulls | -40 | 3,043 | +1,623 | -626 .. +3,956 | +5.7 | +3.2 | 0.49 | 294 |
| maker, microprice pulls | 0 | 3,512 | -157 | -2,222 .. +2,113 | -0.4 | -0.6 | 0.49 | 629 |
| maker, microprice pulls | 50 | 4,499 | -3,300 | -5,480 .. -1,028 | -6.5 | -3.7 | 0.46 | 1,759 |
| maker, book-anchored (inv. 2b) | -40 | 31,251 | -4,404 | -7,055 .. -1,395 | -1.4 | -1.2 | 0.46 | 2,254 |
| maker, book-anchored (inv. 2b) | 0 | 48,070 | -21,648 | -25,348 .. -17,781 | -3.1 | -2.9 | 0.47 | 10,749 |
| maker, book-anchored (inv. 2b) | 50 | 42,201 | -22,001 | -25,594 .. -18,233 | -3.5 | -3.3 | 0.47 | 10,924 |
