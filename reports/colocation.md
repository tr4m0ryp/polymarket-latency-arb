# Where to put the bot: venue locations, latency budget, host options

Date 2026-10-09. Measurements from the Scaleway Paris host and live run 1 (`reports/live-lead-run1.md`).

## Verdict

**Tokyo alone does not help; the route between Tokyo and London does.** The strategy reads Binance
(AWS Tokyo) and trades on Polymarket (AWS London). Signal-to-order time is the sum of both legs, so
any host on the Tokyo-London path gives about the same total: what Tokyo saves on the signal leg,
the order leg pays back. The levers that actually move the total, by size:

1. **The intercontinental route: about 40 ms one-way.** The AWS backbone runs about 215 ms round
   trip Tokyo-London; a dedicated crypto link (McKay Brothers, Feb 2025) runs under 132 ms.
2. **Cloudflare in the order path: about 10-15 ms.** Polymarket's API sits behind Cloudflare; direct
   co-location in London (KYC/KYB) is offered and may skip it.
3. **The availability zone (one data-centre group inside a cloud region): under 1 ms.** Picking the
   exact Binance or Polymarket zone is the last step, not the first.

## Where the venues are

- **Binance spot and USD-M futures streams:** every resolved IP maps to AWS `ap-northeast-1` (Tokyo)
  in AWS's published IP ranges. Binance publishes a trade 1 ms after it happens (event time minus
  trade time, median; p99 10 ms spot, 1 ms futures).
- **Polymarket CLOB:** primary servers in AWS `eu-west-2` (London); closest region without geo
  restriction `eu-west-1` (Dublin); direct co-location in eu-west-2 after a KYC/KYB form, for
  traders on their own account (Polymarket docs, Geographic Restrictions page). All API hosts sit
  behind Cloudflare (`cf-ray ...-CDG`, `cf-cache-status DYNAMIC`).
- **Geoblock (same page):** France, Germany, UK and US are close-only on the API, so no new
  orders. Ireland, Japan, Netherlands and South Korea are restricted on the website only; the
  API is not restricted. This host reports `{"blocked": true, "country": "FR"}`.

## Measured latency budget (from Paris)

| leg | measured | note |
|---|---|---|
| Binance trade to publish | 1 ms | event minus trade time, median |
| Tokyo to Paris, one-way | 110-122 ms | spot p50 122, futures p50 111; spot p90 221 vs futures 138 |
| Paris to Tokyo route | 235 ms round trip | NTT via Ashburn and San Jose: westward through the US |
| Paris to Polymarket edge | 2.8 ms round trip | Cloudflare CDG |
| warm API request (`GET /time`) | 22-25 ms round trip | ~8 ms Paris-London network, so ~12 ms Cloudflare + origin |
| Polymarket stamp to our receipt | 13 ms | CLOB websocket |

**Competitors:** the 5m book's first in-direction reprice lands a median **201 ms** after the
Binance trade (p25 128 ms). An AWS-routed bot needs about 107 ms of transit plus processing and
matching, which fits the median. **9% of 5m reprices land within 66 ms**, faster than any known
Tokyo-London route; random times show 0%. These fastest bots must trigger earlier in the move or
on a leading feed. Run 2 records Binance futures to test the second case.

## Host options (one-way signal to order at the matching engine)

| option | Binance to bot | bot to CLOB | total, before processing | API status of host IP | cost / effort |
|---|---|---|---|---|---|
| Paris (now) | 110-122 ms | ~5 ms + Cloudflare | ~120-130 ms | blocked (FR) | have it |
| AWS Dublin, eu-west-1 | ~107 ms (AWS backbone, est.) | ~5 ms + Cloudflare | ~115-125 ms | allowed (IE) | cheap EC2 |
| AWS Tokyo, ap-northeast-1 | ~1 ms | ~107 ms + Cloudflare long-haul (unmeasured) | ~110-125 ms | allowed (JP) | cheap EC2 |
| AWS London co-location | ~107 ms | ~1 ms, maybe no Cloudflare | ~108 ms | via KYC/KYB form | form + approval |
| Tokyo signal box + McKay link + Dublin/LD4 order box | ~1 ms | ~66 ms + ~5 ms | **~72 ms** | allowed (IE) or via KYC (LD4) | vendor contract, price unknown |

**Read:** the four single-host options cluster at 108-125 ms because they all ride roughly the
same intercontinental path. Only the split design with a faster link gets clearly ahead,
~40 ms before an AWS-routed bot. Against a ~100 ms half-life of the stale edge, that is the
difference between taking the stale quote and arriving after it. The AWS backbone figure
(~215 ms round trip) is a third-party estimate, and the Cloudflare long-haul from Tokyo is
unmeasured: both need a probe from inside AWS before anything is rented long term.

## Not a technical question

Host placement changes the IP country, not the trader's jurisdiction. Polymarket's restrictions
and terms apply to the person trading; whether the user may trade from a given country, and
whether a non-French host is acceptable for them, is the user's call (and possibly a legal one).
Nothing here assumes it.

**Update 2026-10-09:** the user trades as a resident of a non-restricted country; that country is not on the restricted
list. The host must still sit in a permitted region, so the candidates are AWS Dublin and AWS
Tokyo, or London through the co-location form. Paris stays a research-only host.

## Next steps

1. **User decisions:** jurisdiction and legality; whether to file the eu-west-2 co-location KYC/KYB
   form; whether to request a McKay Brothers quote (Tokyo AWS to AWS Dublin).
2. **Probe before buying (about 1 day, under $5 of EC2):** small instances in ap-northeast-1 and
   eu-west-1/eu-west-2, read-only: Binance receipt lag per availability zone, AWS Tokyo-to-Dublin
   one-way time, Cloudflare request time from Tokyo vs Dublin. Needs AWS credentials on this machine
   (the AWS MCP server failed to start: `uvx` missing).
3. **Signal side:** finish run 2 (futures vs spot lead) and test triggers earlier in the move.
   The fastest competitors' sub-66 ms reprices point there, not at the network.

## Sources

- Polymarket docs, Geographic Restrictions (server regions, co-location form, jurisdiction tables):
  https://docs.polymarket.com/api-reference/geoblock.md
- AWS IP ranges: https://ip-ranges.amazonaws.com/ip-ranges.json
- Tokyo-London AWS latency, third-party estimate 214.9 ms:
  https://www.economize.cloud/resources/aws/latency/ap-northeast-1-vs-eu-west-2/
- McKay Brothers Tokyo-Europe link, sub-132 ms round trip, AWS Tokyo to LD4 and AWS Dublin (press
  release, 2025-02-28): https://www.marketsmedia.com/mckay-brothers-launches-fastest-connectivity-between-tokyo-and-europe
- Glassnode latency monitor (Binance WS/FIX route to AWS Tokyo; Polymarket origin in eu-west-2
  behind Cloudflare): https://latency.glassnode.com/cex/about, https://latency.glassnode.com/prediction-markets/about
