//! Messages into the decision thread (the only owner of the engine, the risk book and the
//! order state). Feed tasks timestamp at socket read; send tasks forward each copy's answer.
use btl_signal::feed::Ev;
use btl_signal::MarketMeta;
use btl_venue::{Resp, UserMsg};

/// Receipt of one accepted (deduplicated) feed message.
#[derive(Debug, Clone, Copy)]
pub struct Recv {
    pub conn: u8,
    pub mono: u64,
    pub wall: u64,
}

pub enum Msg {
    Ev(Ev, Recv),
    Market(Box<MarketMeta>),
    Conn { feed: String, conn: usize, state: &'static str, err: Option<String> },
    /// one copy's answer to an order (cid)
    Ack { cid: String, resp: Box<Resp> },
    /// GET /data/order lookup of a delayed order
    Lookup { cid: String, resp: Box<Resp> },
    /// dry: the simulated ack of a would-be order
    DryAck { cid: String },
    Cancel { what: String, reason: String, resps: Vec<Resp> },
    User(UserMsg),
    Trades(Result<Vec<serde_json::Value>, String>),
    Balance(Box<Resp>),
    Settle { slug: String, outcome: f64 },
    Stop(String),
}
