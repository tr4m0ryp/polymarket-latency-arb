# Fast link: a self-serve path from AWS Tokyo to AWS Dublin/London

Date 2026-10-11. Research only: no accounts, no payments, nothing rented, nobody contacted.
Tags: **[M]** measured this session with free Globalping probes (raw lines in
`data/out/infra/fastlink/`, code `research/infra/fastlink_probe.py`), **[S]** sourced (URL + date
in the table or Sources), **[E]** estimated (arithmetic, stated).

## Verdict

**Nothing self-serve reaches ~70 ms one way. One self-serve path beats the AWS backbone: a $12/month
relay VPS in Khabarovsk (Russian Far East), at ~87 ms one way to London and ~90 ms to Dublin.**
Every self-serve network product (Megaport, Equinix, Console Connect, Cloudflare, AWS Global
Accelerator, other clouds) is **as slow or slower** than AWS, because they all leave Tokyo across
the Pacific or through Suez. The only short ground route crosses Russia. Today you can buy that
only from sales-led vendors (McKay, BSO, Avelacom), or as a home-made relay through a Russian
network.

- **Relay path [M]:** AWS Tokyo to Misaka KHV01 **25.6 ms RTT** (best of 3 AWS Tokyo probes, two
  runs), KHV01 to AWS London **149.1 ms**, to AWS Dublin **154.6 ms**. Summed: London **174.7 ms RTT
  (~87 ms one way)**, Dublin **180.2 ms (~90 ms)**. A second Khabarovsk host (EdgeCenter) gives
  27.7 + 143.6 = **171.3 ms** to London.
- **Baseline [M]:** AWS Tokyo to AWS London 209.8 ms RTT, to Dublin 202.4 ms. Our own probe
  measured Binance receive delay at 104 ms (Dublin) and 109 ms (London) one way.
- **Gain:** ~17-20 ms one way at London, **~11-14 ms at Dublin** [E]. It is roughly a third of
  what McKay/BSO would give (~35-40 ms).
- **Big catch:** the Tokyo leg depends on which AWS Tokyo host sends. Of 3 AWS Tokyo probes, one
  measured 25.6, one 32.3 and one **73-75 ms** (150 ms in one run) [M]. Run a ping from our
  apne1-az4 box **before paying for a month**.
- **Other risks:** traffic crosses Russian networks (MTS/EdgeCenter via Moscow [M: traceroute]),
  so it carries sanctions, legal and interception risk. Run it as a **race beside the AWS path,
  never instead of it**. Send each trigger both ways and act on the first copy. That way the worst
  case equals today's baseline.
- **Public RTT claim re-verified [M]:** Azure, GCP, Megaport and the public internet were said to
  be 204-232 ms. This mostly holds. Commercial Tokyo hosts reach AWS London in 203.3-224 ms and
  other clouds' own backbones take 216-226 ms. The one sub-200 reading (CTG Server, 187 ms) was a
  **mislabelled Hong Kong probe**: it is 53 ms from AWS Tokyo, and its traceroute goes through NTT
  Hong Kong to Vienna.

## Table

RTT = round trip; one way taken as RTT/2. Dates are measurement or publication dates.

| provider | product | self-serve? (how) | Tokyo to London / Dublin | connects to AWS | min monthly | setup |
|---|---|---|---|---|---|---|
| **Misaka Network (US co.)** | Cloud VPS **KHV01** Khabarovsk, E2-S1 | **yes**: misaka.io console, Visa/MC/Amex/UnionPay [S] | **174.7 / 180.2 ms RTT, ~87 / ~90 one way** [M, 2026-10-11 23:04 UTC] | public internet both legs (Tokyo via JPIX, ~26 ms) | **$12** (1 vCPU, 1 TB; only plan in stock) [S] | minutes |
| EdgeCenter (RU) | cloud VPS Khabarovsk | no in practice: rouble billing, foreign cards reportedly fail [S: habr] | 171.3 / 185.4 ms RTT [M] | public internet | ~350-2000 RUB [S, forum] | n/a |
| PortTelekom Vladivostok | (probe host) | not checked | 36.1 + 148.1 = 184 ms RTT [M] | public internet | n/a | n/a |
| AWS backbone (baseline) | inter-region / peering | yes | 209.8 / 202.4 ms RTT [M]; cloudping p50 214.7 / 203.7 [S] | native | EC2 only | minutes |
| AWS | Global Accelerator, Cloud WAN | yes | same AWS backbone, no gain [S] | native | n/a | minutes |
| Public internet | best of 50 Tokyo hosts | n/a | 203.3 (HaloCloud via RETN Helsinki) / 212.5 ms RTT [M] | n/a | n/a | n/a |
| Megaport | MCR + VXC to hosted DX | **partly**: portal, company email domain required, card via Stripe ("Register Card") [S] | **218 / 228 ms RTT**, TY2 to LD8 / DB3, Sep 2026 median, Megaport RTT API [S] | hosted DX both ends | MCR minimum 1 Gbps, price behind login; DX ~$43 for two ends [S] | minutes after account |
| Equinix | Fabric / Fabric Cloud Router | billing account first (~24 h); AWS Marketplace FCR US metros only [S] | SLA ceiling APAC-Europe <= 287 ms RTT [S] | hosted DX | FCR $1,200 + VC from $100 [S] | ~1 day |
| Console Connect (PCCW) | port + connection | account + company verification; cloud links through a BDM [S] | none for Tokyo (2019 Singapore-London ~150 "guide only") [S] | partner | not public | days |
| PacketFabric | Cloud Router | portal | no Asia region [S] | n/a | n/a | n/a |
| Colt On Demand, Zayo, Lumen, Epsilon Infiny, InterCloud | NaaS portals | existing/contracted customers only [S] | none published | Fabric / DX | contract | contract |
| NTT GIN | IP transit | sales | "Asia-Europe" 141-153 ms monthly avg, endpoints not stated [S, 2025] | n/a | contract | contract |
| Cloudflare | Argo / Spectrum | Argo yes (~$5 + $0.10/GB, HTTP/WebSocket only); raw TCP/UDP Spectrum is Enterprise [S] | no published figure; same Pacific/Suez cables | internet to EC2 IP | ~$5 | minutes |
| Azure | Japan East to UK South / North Europe | yes | 230 / 227 ms RTT [S, MS Learn 2026-07-30] | n/a | n/a | n/a |
| Oracle, Akamai/Linode, Vultr, Alibaba | own backbone, Tokyo to London | yes | 218.5 / 216.5 / 222.4 / 224.2 ms RTT [M] | n/a | n/a | n/a |
| GCP | asia-northeast1 to europe-west2 | yes | no number found (dashboard did not render) | n/a | n/a | n/a |
| BSO | Crypto Connect Plus | portal with card [S] | no Tokyo-London route in the product | EC2 in-region | consumption, not published | n/a |
| Beeks | Crypto Connect | online store, card unconfirmed | LD4/5 or NY4 hosting, no Tokyo route | n/a | from GBP 258 [S] | n/a |
| CoinAPI, Amberdata, Kaiko, Tardis | market-data APIs | CoinAPI/Amberdata yes | no route; extra hops, only slower than a direct websocket [E] | n/a | $79+ | n/a |

## Recommendation, ranked

1. **Khabarovsk relay racing the AWS path (Misaka KHV01, $12/month).** This is the only
   self-serve option that beats ~100 ms, with ~87 ms one way to London and ~90 ms to Dublin.
2. **Stay on the AWS backbone** (free, ~101-109 ms) if the az4 test or the legal check fails.
3. **Sales-led route** (McKay, BSO/CryptoStruct, Avelacom) for ~66-70 ms. Requests are already
   out (`notes/link-vendors.md`).

**Order steps for option 1** (for the user; nothing here was done):

1. **Check (10 min):** look at EU Regulation 833/2014 and Dutch sanctions guidance for buying a
   VPS from a US company whose server and upstream are in Russia. Do not pay until this is clear.
2. **Free test (5 min):** from the apne1-az4 box, run `ping -c 200 185.209.84.131` (Misaka's KHV01
   test IP). Go ahead only if the median is <= 30 ms. Also run it from the Dublin box (expect
   ~150-155 ms).
3. **Order (10 min):** go to misaka.io, open the Console and sign up. Add a card under billing,
   then order a cloud server in **KHV01**, plan **E2-S1** ($12/month, Linux image). The plan is
   prepaid monthly and auto-charged.
4. **Relay (30 min):** run a UDP forwarder on KHV01 (`socat UDP-LISTEN:9000,fork
   UDP:<dublin-ip>:9000`, or ~30 lines of Rust/Python). Allow only the Tokyo box's IP.
5. **Race:** the Tokyo box sends each ~100-byte trigger twice, once direct to Dublin and once via
   KHV01, both carrying a sequence number. Dublin acts on whichever copy arrives first. Log both
   arrival times for 48 h.
6. **Kill rule:** if the relay copy wins less than 80% of the time, or saves less than 8 ms
   median, cancel before the next renewal.

Only trigger messages cross Russia. Binance is read in Tokyo and orders leave from Dublin, so
neither Binance nor Polymarket ever sees a Russian IP.

## Not self-serve but fastest

- **BSO + CryptoStruct microwave:** under 66 ms one way, Binance data delivered in London
  (TheTrade, 2026-08). Request sent 2026-10-11.
- **McKay Brothers:** under 132 ms RTT, AWS Tokyo to LD4 and AWS Dublin (2025-02).
- **Avelacom:** 139.6 ms RTT via Direct Connect (AWS blog test, 2026-04-28). Tokyo to its AWS
  Stockholm PoP is ~118 ms RTT (2026-04-20).
- **BSO Kraken route:** under 140 ms RTT (2025-11-04).
- **Raft HF radio:** no Tokyo figure.
- **Coming later:** Far North Fiber, Arctic, ~142 ms RTT, not before 2027.

## Caveats

- **Few probes:** each number comes from one to three Globalping probes, one evening (22:58-23:10
  UTC). The KHV01 legs repeated within 1-3 ms over two runs, apart from the per-host Tokyo spread.
- **One way = RTT/2:** routes through Russia may be asymmetric. Only a synced-clock one-way test
  (step 5) settles the real Tokyo-to-Dublin gain.
- **Jitter:** ICMP to the KHV01 host showed spikes of 75-150 ms on some samples. The race design
  limits the damage, but the relay may win less often than its median suggests.
- **Megaport:** its RTT figures are measured between its own data centres, not AWS endpoints.
- **Vendor claims:** Avelacom, NTT, McKay and BSO figures are published by the vendors.
- **Legal and operational:** Russian carriers fall under state interception, and routes can be
  throttled or cut. The Misaka E2-S1 plan was the only one in stock on 2026-10-11.

## Sources

- Globalping API (all [M] rows, measurement ids in `data/out/infra/fastlink/globalping_ping.jsonl`): https://api.globalping.io/v1/measurements
- Misaka KHV01 location, plans, payment, test IP (fetched 2026-10-11): https://www.misaka.io/locations/khv01
- Misaka billing update 2026: https://docs.misaka.io/archives/202512-important-updates-on-billing
- Megaport RTT API (Jul-Sep 2026 extract in `megaport_rtt_tokyo_europe.csv`): https://api.megaport.com/v2/locations/rtt ; https://www.megaport.com/network-latency/
- Megaport card payments: https://docs.megaport.com/finance/credit-card-payments
- Equinix Fabric SLA: https://docs.equinix.com/fabric/fabric-availability ; FCR on AWS Marketplace: https://aws.amazon.com/marketplace/pp/prodview-l3kzqe5fdbqlw
- PacketFabric Cloud Router specs: https://docs.packetfabric.com/cr/specs/
- Console Connect billing thread: https://community.app.consoleconnect.com/social-47/messy-billing-handling-by-concoleconnect-billing-team-306
- NTT GIN SLA stats: https://www.ntt.com/en/services/network/gin/sla/stats.html
- Azure round-trip latency (2026-07-30): https://learn.microsoft.com/en-us/azure/networking/azure-network-latency
- WonderNetwork Tokyo-London and Khabarovsk pings (2026-10-11): https://wondernetwork.com/pings/Tokyo/London ; https://wondernetwork.com/pings/Khabarovsk/London
- AWS Direct Connect pricing: https://aws.amazon.com/directconnect/pricing/
- AWS + Avelacom (139.6 ms): https://aws.amazon.com/blogs/industries/ultra-low-latency-cross-region-crypto-trading-with-avelacom-and-aws/
- Avelacom Stockholm PoP (2026-04-20): https://www.thetradenews.com/avelacom-establishes-low-latency-route-between-tokyo-and-london-cloud-infrastructure/
- BSO + CryptoStruct microwave: https://www.thetradenews.com/thought-leadership/bso-and-cryptostruct-partner-on-ultra-low-latency-tokyo-to-london-microwave-route-for-crypto-data/
- BSO x Kraken (2025-11-04): https://www.bso.co/all-insights/bso-x-kraken-high-speed-tokyo-london-connectivity
- BSO Crypto Connect Plus: https://www.bso.co/bso-ultra/crypto-connect-plus ; Beeks: https://beeksgroup.com/services/trading-infrastructure/cryptocurrency-hosting/ ; CoinAPI: https://www.coinapi.io/market-data-api/pricing
- EdgeCenter billing (forum, undated): https://habr.com/en/articles/657639/comments

## Follow-up check, 2026-10-11 23:25 UTC: our zone to Khabarovsk

`ping -c 200` from a t4g.micro in **apne1-az4** to KHV01 (185.209.84.131): **RTT min / avg / max
149.7 / 150.0 / 152.3 ms**, 0% loss. The route from our Binance zone leaves Tokyo the long way, so
Tokyo -> Khabarovsk -> London would be ~75 + ~75 ms one way, far slower than AWS's ~100 ms.
**Verdict: the Khabarovsk relay is closed for apne1-az4** (premise: AWS egress routing from this
zone on this date; another zone or provider in Tokyo could route differently). No self-serve option
beats AWS for us.
