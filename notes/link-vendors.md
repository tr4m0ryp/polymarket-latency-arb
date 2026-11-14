# Low-latency Tokyo to Europe link vendors (parked)

Status 2026-10-11: **active** (user: fix the Tokyo-London link asap). CryptoStruct request sent
2026-10-11 22:09 UTC via cryptostruct.com/contact (covers the BSO + CryptoStruct microwave; reply to
<EMAIL>). Raft and McKay forms need a human captcha; BSO's form needs a phone number.
Earlier status 2026-10-10: parked. We build on AWS's own network first (cheap Dublin build, ~113 ms
arrival, reports/infra-plan.md). Come back here only once live fills show a positive edge that a
faster link would protect.

## Options

| vendor | medium | Tokyo to London, one way | note |
|---|---|---|---|
| AWS backbone | fiber | ~100-107 ms | what we use now |
| McKay Brothers | private route | ~66 ms (132 ms RTT London, 136 ms Dublin, incl. on-ramp) | handoff in AWS cloud (or CC2/LD4); quoted 2026-10-12: GBP 20K/month minimum (5M package) |
| BSO + CryptoStruct | microwave | < 66 ms | Binance market data delivered in London; may remove the need for a Tokyo box; price on request |
| **Misaka KHV01 relay (self-serve)** | VPS in Khabarovsk, public internet via Russia | ~87 (London), ~90 (Dublin) [M: 25.6 + 149.1 / 154.6 ms RTT] | $12/month by card at misaka.io; only self-serve option that beats AWS; test from apne1-az4 first (other AWS Tokyo hosts measured 32-75 ms on the first leg); sanctions check first; race it beside the AWS path (reports/fast-link.md) |
| Megaport MCR + VXC (self-serve) | fiber via US | ~109-114 (218 / 228 ms RTT) | slower than AWS; not worth it |
| Avelacom | fiber via Russia | ~70 (139.6 ms RTT) | AWS Direct Connect handoff; Tokyo-Stockholm PoP ~118 ms RTT; sales |
| Raft | HF shortwave radio | ~35-40 ms (estimate; air floor ~32 ms) | Chicago-London < 25 ms audited; Asia links exist, no public Tokyo-London figure |

## Endpoints we need

- **Tokyo:** Equinix TY2 or AT Tokyo Chuo (AWS Direct Connect into ap-northeast-1, where Binance runs).
- **London:** Equinix LD4/LD5 Slough (into eu-west-2, Polymarket's matching engine). Orders from a UK
  IP only via Polymarket's co-location (KYC/KYB) form.
- **Dublin (fallback, orders allowed):** Equinix DB1 or Interxion DUB2 (into eu-west-1), ~5 ms from London.

Data-centre names are the usual AWS handoff sites; not yet checked against AWS's current list.

## Messages (ready to send)

### Raft

```
Subject: Student research question: Tokyo to Europe HF latency

Hello Raft team,

I'm a student at the University of Amsterdam (UvA), researching how speed and
location affect trading between Tokyo and Europe.

My question: what one-way latency does HF radio achieve between these points,
compared with fiber and microwave (around 66 ms today)?
- Tokyo: Equinix TY2 or AT Tokyo Chuo (near AWS ap-northeast-1)
- London: Equinix LD4/LD5 (near AWS eu-west-2), or Dublin: Equinix DB1 / Interxion
  DUB2 (near AWS eu-west-1)

Could you share any figures, or point me to someone I could talk to briefly?

Many thanks,
[Name]
University of Amsterdam
[Email]
```

### McKay Brothers

Reply 2026-10-12 07:14 (Clement Pelletier): 132.x ms RTT instance to instance AWS Tokyo to AWS London, 136 ms to AWS Dublin, on-ramp included; handoff directly in AWS. Smallest package GBP 20K per month (5M). Out of budget at our scale.

```
Subject: Student research question: Tokyo to Europe latency

Hello McKay Brothers team,

I'm a student at the University of Amsterdam (UvA), researching how speed and
location affect crypto trading between Tokyo and Europe.

I read about your Tokyo to Europe route (under 132 ms round trip). My questions:
- What is the one-way latency from AWS Tokyo (ap-northeast-1) to Equinix LD4/LD5
  (near AWS eu-west-2) and to AWS Dublin (eu-west-1)?
- Where are the handoff points at each end?
- Is there a small-scale or student option, and what does it cost?

Could you share any figures, or point me to someone I could talk to briefly?

Many thanks,
[Name]
University of Amsterdam
[Email]
```

### BSO / CryptoStruct

```
Subject: Student research question: Binance data in London via microwave

Hello BSO / CryptoStruct team,

I'm a student at the University of Amsterdam (UvA), researching how speed and
location affect crypto trading between Tokyo and Europe.

I read about your Tokyo to London microwave route for Binance data (under 66 ms
one way). My questions:
- Which Binance data does it carry (spot and/or futures, top of book, trades)?
- Where is it delivered: Equinix LD4/LD5, AWS London (eu-west-2), or AWS Dublin
  (eu-west-1)?
- Can it also carry small messages of my own, or is it data-only?
- Is there a small-scale or student option, and what does it cost?

Could you share any figures, or point me to someone I could talk to briefly?

Many thanks,
[Name]
University of Amsterdam
[Email]
```

Ask every vendor whether Binance **futures** data is covered: the perp moved the 5m book ~3x more
than spot in our data.

## Sources

- McKay: https://www.marketsmedia.com/mckay-brothers-launches-fastest-connectivity-between-tokyo-and-europe
- BSO + CryptoStruct: https://cryptostruct.com/news/bso-microwave-2026-08
- Raft HF (STAC audit, Chicago-London): https://stacresearch.com/node/47871
- Misaka KHV01 (plans, card, test IP 185.209.84.131): https://www.misaka.io/locations/khv01
- Megaport RTT matrix: https://www.megaport.com/network-latency/ (extract: data/out/infra/fastlink/megaport_rtt_tokyo_europe.csv)
- Full self-serve survey: reports/fast-link.md
