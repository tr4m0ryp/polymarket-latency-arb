"""One bankroll path: markets in path order, each market's orders in time.

Cash flow: an order reserves its worst cost (shares x (limit + fee)) from send until its ack
(match + 14 ms); at the ack the filled cost + fee leave the cash and become open cost, and the
bot learns of the fill (fill count and side per market). A market's winning shares pay $1 at
its end + the redeem delay. Fills use the stored ladder of a random hold draw minus our own
takes of the last 3 s in that market. Equity E = cash + open cost (cost basis until paid).

out: [0] final equity, [1] min equity, [2] max drawdown (fraction of peak), [3] sent,
[4] orders with a fill, [5] skipped for room (cash / caps), [6] worst market loss $,
[7] worst market loss / equity before it, [8] markets with a fill, [9] markets with fills on
both sides, [10] of those, pairs that lock a profit (avg Up + avg Down price + fees < $1),
[11 + d] equity at the end of day d. cfg[11] floor: no order for the rest of the path once
E < floor x the all-time peak equity (a halt a human must lift).

Side policy (cfg[5]): 0 none; 1 one direction per market (no order opposite a known fill);
2 per-side fill cap (max_fills counts fills per side, the opposite side is free); 3 hedge only:
an order opposite the market's net position is capped at the net share imbalance (known fills
plus orders in flight on its side), so it can only lower the market's worst-case loss."""
from __future__ import annotations

import numpy as np
from numba import njit

ACK = 0.014
MEM = 3.0
FEE = 0.07
MAXP = 256
MKT = 300.0
DAY0 = 11


@njit(cache=True)
def _acks(T, st, pend, npend, mk_open, mk_pay, mk_nf, mk_side, mk_sh, mk_c):
    """Apply acks due by T. st = [cash, open]."""
    i = 0
    while i < npend:
        if pend[i, 0] <= T:      # ack t, worst, cost + fee, shares, slot, side, won
            s = int(pend[i, 4])
            st[0] -= pend[i, 2]
            st[1] += pend[i, 2]
            mk_open[s] += pend[i, 2]
            mk_pay[s] += pend[i, 3] * pend[i, 6]
            if pend[i, 3] > 0:
                k = 0 if pend[i, 5] > 0 else 1
                mk_nf[s, k] += 1
                mk_sh[s, k] += pend[i, 3]
                mk_c[s, k] += pend[i, 2]
                if mk_side[s] == 0:
                    mk_side[s] = pend[i, 5]
            pend[i, :] = pend[npend - 1, :]
            npend -= 1
        else:
            i += 1
    return npend


@njit(cache=True)
def _mark(st, E):
    """st = [cash, open, eq_min, peak, maxdd, day_peak]."""
    if E < st[2]:
        st[2] = E
    if E > st[3]:
        st[3] = E
    if E > st[5]:
        st[5] = E
    if st[3] > 0 and 1 - E / st[3] > st[4]:
        st[4] = 1 - E / st[3]


@njit(cache=True)
def _pay(s, st, mk_open, mk_pay, worst, mk_sh, mk_c):
    if mk_sh[s, 0] > 0 or mk_sh[s, 1] > 0:
        worst[2] += 1
    if mk_sh[s, 0] > 0 and mk_sh[s, 1] > 0:
        worst[3] += 1
        if mk_c[s, 0] / mk_sh[s, 0] + mk_c[s, 1] / mk_sh[s, 1] < 1.0:
            worst[4] += 1
    E0 = st[0] + st[1]
    loss = mk_open[s] - mk_pay[s]
    if loss > worst[0]:
        worst[0] = loss
    if E0 > 0 and loss / E0 > worst[1]:
        worst[1] = loss / E0
    st[0] += mk_pay[s]
    st[1] -= mk_open[s]
    _mark(st, st[0] + st[1])


@njit(cache=True)
def path(seq, seed, cfg, start, day_len, m_lo, m_hi, tr, side, lim, won, score, tau, v1val,
         h, off, nlev, lcol, ltick, lsh, out):
    np.random.seed(seed)
    mode, size, max_sh = int(cfg[0]), cfg[1], cfg[2]
    fm, fe, pol, max_fills, dd = cfg[3], cfg[4], int(cfg[5]), cfg[6], cfg[7]
    min_edge, fit, redeem, floor = cfg[8], cfg[9] > 0.5, cfg[10], cfg[11]
    L, K = seq.shape[0], h.shape[1]
    st = np.array([start, 0.0, start, start, 0.0, start])
    worst = np.zeros(5)
    pend = np.zeros((MAXP, 8))
    npend = 0
    mk_open, mk_pay = np.zeros(L), np.zeros(L)
    mk_nf, mk_side = np.zeros((L, 2)), np.zeros(L)
    mk_sh, mk_c = np.zeros((L, 2)), np.zeros((L, 2))
    mem = np.zeros((MAXP, 3))
    sent, fills, rej, paid, paused, halted = 0, 0, 0, 0, False, False
    for j in range(L):
        u = seq[j]
        t0 = j * MKT
        if j % day_len == 0 and j > 0:
            out[DAY0 + j // day_len - 1] = st[0] + st[1]
            st[5], paused = st[0] + st[1], False
        nmem = 0
        for o in range(m_lo[u], m_hi[u]):
            T = t0 + tr[o]
            npend = _acks(T, st, pend, npend, mk_open, mk_pay, mk_nf, mk_side, mk_sh, mk_c)
            while paid < j and (paid + 1) * MKT + redeem <= T:
                _pay(paid, st, mk_open, mk_pay, worst, mk_sh, mk_c)
                paid += 1
            E = st[0] + st[1]
            _mark(st, E)
            if dd < 1e17 and E < (1 - dd) * st[5]:
                paused = True
            if floor < 1e17 and E < floor * st[3]:
                halted = True
            if paused or halted or score[o] < tau[o] + min_edge:
                continue
            ks = 0 if side[o] > 0 else 1
            nfk = mk_nf[j, ks] if pol == 2 else mk_nf[j, 0] + mk_nf[j, 1]
            if nfk >= max_fills:
                continue
            if pol == 1 and mk_side[j] != 0 and side[o] != mk_side[j]:
                continue
            p = lim[o]
            w = p + FEE * p * (1 - p)
            if mode == 0:
                q = size
            elif mode == 1:
                q = np.floor(size * E / p)
            else:
                q = np.floor(size * max(v1val[o], 0.0) / (1 - p) * E / p)
            q = min(max(q, 5.0), max_sh)                 # venue floor 5 sh
            if q * p < 1.0:
                q = max(q, np.ceil(1.05 / p - 1e-9))     # venue $1 floor, as the bot
            res, m_inf, inf_sh = 0.0, 0.0, np.zeros(2)
            for i in range(npend):
                res += pend[i, 1]
                if int(pend[i, 4]) == j:
                    m_inf += pend[i, 1]
                    inf_sh[0 if pend[i, 5] > 0 else 1] += pend[i, 7]
            if pol == 3:
                mine = mk_sh[j, ks] + inf_sh[ks]
                other = mk_sh[j, 1 - ks] + inf_sh[1 - ks]
                if other > 0 or mine > 0:
                    if mine >= other and mk_side[j] != 0 and side[o] != mk_side[j]:
                        continue
                    if mine < other:
                        q = min(q, np.floor(other - mine))
            room = st[0] - res
            if fm < 1e17:
                room = min(room, fm * E - mk_open[j] - m_inf)
            if fe < 1e17:
                room = min(room, fe * E - st[1] - res)
            if q * w > room + 1e-9:
                if not fit:
                    rej += 1
                    continue
                q = np.floor(max(room, 0.0) / w + 1e-9)
            if q < 5.0 or q * p < 1.0 - 1e-9:
                rej += 1
                continue
            k = np.random.randint(K)
            left, cost, sh = q, 0.0, 0.0
            for lv in range(off[o, k], off[o, k] + nlev[o, k]):
                if left <= 1e-9:
                    break
                a = lsh[lv]
                for i in range(nmem):
                    if mem[i, 1] == lcol[lv] and mem[i, 0] > tr[o] - MEM:
                        a -= mem[i, 2]
                if a <= 0:
                    continue
                x = min(a, left)
                px = ltick[lv] / 100.0
                cost += x * (px + FEE * px * (1 - px))
                sh += x
                left -= x
                if nmem < MAXP:
                    mem[nmem, 0], mem[nmem, 1], mem[nmem, 2] = tr[o], lcol[lv], x
                    nmem += 1
            sent += 1
            if sh > 0:
                fills += 1
            if npend < MAXP:
                pend[npend, 0], pend[npend, 1], pend[npend, 2] = T + h[o, k] + ACK, q * w, cost
                pend[npend, 3], pend[npend, 4], pend[npend, 5], pend[npend, 6] = sh, j, side[o], won[o]
                pend[npend, 7] = q
                npend += 1
    npend = _acks(1e18, st, pend, npend, mk_open, mk_pay, mk_nf, mk_side, mk_sh, mk_c)
    while paid < L:
        _pay(paid, st, mk_open, mk_pay, worst, mk_sh, mk_c)
        paid += 1
    nd = out.shape[0] - DAY0
    out[DAY0 + nd - 1] = st[0] + st[1]
    out[0], out[1], out[2], out[3] = st[0] + st[1], st[2], st[4], sent
    out[4], out[5], out[6], out[7] = fills, rej, worst[0], worst[1]
    out[8], out[9], out[10] = worst[2], worst[3], worst[4]
