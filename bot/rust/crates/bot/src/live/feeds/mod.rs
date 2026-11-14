//! Live read-only feeds (btclat/paper/feeds/live.py): Binance spot and USD-M perp on N
//! connections each (first arrival per update / trade id wins), one Polymarket CLOB market
//! connection per 5m market (from discovery until end + 30 s), Gamma discovery and outcomes.
pub mod binance;
pub mod clob;
pub mod gamma;
pub mod ws;
