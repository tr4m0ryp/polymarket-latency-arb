# Co-location and latency to-do (user, 2026-10-15: "every ms counts", beat leaders A and B)

Target: decision-to-match below the leaders' ~180 ms, signal at least level with theirs (today they
send 63-83 ms before our decision). Measure every item on the same box against the current path;
keep a change only if it wins. No real orders without the hold/fill tests already approved.

## Blocked on AWS (watcher probes London every 30 min)
1. Launch c7g.large in eu-west-2a/b/c (euw2-az2/az3/az1); copy /opt/btclat kit + secrets (600).
2. Per AZ: TCP/TLS RTT to clob.polymarket.com, ws-subscriptions, Cloudflare PoP (cf-ray), keep best AZ.
3. London hold test (FAK/FOK/marketable GTC vs resting control) on the whitelisted path: is the
   ~120 ms queue above the 150 ms delay gone? Converts to $/day via table 6 of beat-the-hold.md.
4. London cancel latency (insert -> cancel ack), needed <= 150 ms for the resting leg-1 route.
5. Tokyo relay (ap-northeast-1, nearest AZ to Binance): forward raw Binance frames to London over
   the AWS backbone (TCP and UDP); per-trade-id arrival race vs direct London reception.
6. Decide in Tokyo, send a one-packet trigger to London; London holds pre-signed orders.
7. Third-party Tokyo-London line (the forwarded email): sanctions check by the user if via Russia.
8. Move the live bot to the winning London AZ; Dublin becomes standby.

## Can start now (Dublin as proxy, no orders)
9. Feed race: Binance spot JSON trade/book vs bookTicker vs SBE binary stream vs futures
   (fstream) vs Coinbase/Bybit/OKX; per-move first-arrival and lead in ms.
10. Order path in the Rust bot: pre-signed EIP-712 orders per side and price ladder (sign before the
    signal), warm persistent HTTP/2 or keep-alive connections, TCP_NODELAY, TLS session reuse, DNS
    pinned, no allocation or logging on the hot path (logger off-thread), measure send-to-wire.
11. Box tuning: CPU pinning of feed and order threads, busy-poll sockets, IRQ affinity, ENA Express
    on same-AZ links, larger instance only if it measures faster.
12. Untested venue routes: batch order endpoint, order with many price levels, cancel/insert races.

## Strategy items riding on the above
13. Resting leg-1 mode (post-only one tick inside, 0.5 s, fast cancel): dry run, then ~$10 live.
14. Re-run the pair rule under the corrected fill model at the measured London hold; restart live only
    if the held-out $/day is positive.
15. Housekeeping: deploy the recon fix at restart; verify Builder profile (relayer 10k tx/day);
    delete leftover AWS probes, training box and EBS when done.
