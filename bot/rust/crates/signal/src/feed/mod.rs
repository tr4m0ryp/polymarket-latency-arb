//! Raw websocket message -> normalized events (btclat/paper/feeds/parse.py), shared by the live
//! feeds and the replay.
pub mod binance;
pub mod clob;
pub mod event;

pub use event::{Book, Ev, Kind, Pm, Trade};
