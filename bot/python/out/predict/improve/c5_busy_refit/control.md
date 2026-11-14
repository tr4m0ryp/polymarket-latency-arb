# C5 paired comparisons between refits (10 s markout $/day, 95% market bootstrap, L = 0)

| candidate | control | isolates | var | A:eval | B:eval | CV:all | A:ext | A:busy15 | CV:busyQ |
|---|---|---|---|---|---|---|---|---|---|
| rf_plain_m3 | rf_tronly_m3 | added choose-window rows (unweighted) | base | -209 [-639, +200] | -256 [-736, +139] | -241 [-583, +64] | -210 [-1,000, +476] | +513 [-793, +1,772] | +175 [-383, +780] |
| rf_plain_m3 | rf_tronly_m3 | added choose-window rows (unweighted) | comp | -187 [-537, +144] | -169 [-572, +156] | -175 [-460, +69] | -328 [-1,042, +311] | +596 [-631, +1,847] | +25 [-474, +521] |
| rf_bal_m3 | rf_tronly_m3 | added rows + regime-balanced weights | base | -186 [-690, +270] | -196 [-703, +235] | -193 [-569, +143] | +70 [-554, +708] | +475 [-505, +1,534] | +452 [-39, +1,020] |
| rf_bal_m3 | rf_tronly_m3 | added rows + regime-balanced weights | comp | -206 [-685, +207] | -127 [-523, +228] | -154 [-465, +136] | -155 [-813, +482] | +509 [-363, +1,546] | +248 [-184, +741] |
| rf_bal_coh_m3 | rf_tronly_m3 | added rows + weights + projection | base | -243 [-805, +279] | -98 [-597, +339] | -146 [-530, +208] | +44 [-724, +768] | +326 [-883, +1,641] | +419 [-148, +1,059] |
| rf_bal_coh_m3 | rf_tronly_m3 | added rows + weights + projection | comp | -318 [-791, +98] | -80 [-485, +275] | -159 [-480, +127] | -158 [-820, +499] | +268 [-859, +1,530] | +218 [-267, +723] |
| rf_bal_m3 | rf_plain_m3 | regime-balanced weights alone | base | +23 [-234, +280] | +60 [-114, +228] | +48 [-100, +190] | +280 [-117, +774] | -38 [-621, +610] | +277 [-30, +610] |
| rf_bal_m3 | rf_plain_m3 | regime-balanced weights alone | comp | -20 [-276, +220] | +42 [-112, +192] | +21 [-113, +159] | +173 [-180, +587] | -87 [-741, +599] | +223 [-72, +537] |
| rf_bal_coh_m3 | rf_bal_m3 | identity projection alone (kill test 3) | base | -56 [-441, +366] | +98 [-83, +274] | +47 [-124, +232] | -26 [-370, +301] | -149 [-720, +378] | -33 [-316, +242] |
| rf_bal_coh_m3 | rf_bal_m3 | identity projection alone (kill test 3) | comp | -111 [-479, +292] | +48 [-116, +208] | -5 [-169, +163] | -2 [-314, +298] | -241 [-713, +263] | -29 [-309, +230] |
| rf_bal_f50_m3 | rf_plain_f50_m3 | weights alone, v1's rows + choose rows (frac 0.5) | base | +85 [-347, +722] | -70 [-233, +69] | -19 [-191, +208] | -375 [-905, +91] | +41 [-179, +338] | -166 [-495, +153] |
| rf_bal_f50_m3 | rf_plain_f50_m3 | weights alone, v1's rows + choose rows (frac 0.5) | comp | +10 [-267, +365] | -116 [-278, +21] | -74 [-213, +76] | -325 [-846, +128] | +39 [-317, +498] | -118 [-418, +169] |
| rf_bal_coh_f50_m3 | rf_bal_f50_m3 | projection alone, frac 0.5 | base | +218 [-358, +1,028] | +211 [-9, +449] | +213 [-23, +503] | -2 [-426, +466] | +104 [-200, +456] | +312 [-37, +684] |
| rf_bal_coh_f50_m3 | rf_bal_f50_m3 | projection alone, frac 0.5 | comp | +69 [-407, +745] | +207 [+8, +417] | +162 [-34, +413] | -56 [-446, +381] | +61 [-225, +400] | +233 [-82, +570] |
