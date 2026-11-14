//! The taker executor on the decision thread: one FAK (or FOK / GTC) BUY per veto order, limit
//! = seen ask + i, every risk cap checked first, signed on the spot (~70 us) and posted as k
//! identical copies on k warm HTTP/2 connections; the venue dedupes them. Each copy's answer
//! comes back as a message; the first OK answer settles the order (fill from the response,
//! GET /data/order for a delayed one), else the order is a miss once all k have answered.
pub mod book;
pub mod fills;
pub mod ipolicy;
mod ack;
pub mod order;
mod timers;

use std::collections::{BinaryHeap, HashMap, HashSet};
use std::cmp::Reverse;
use std::sync::atomic::AtomicU64;
use std::sync::Arc;

use btl_log::Logger;
use btl_risk::{Intent, RiskBook};
use btl_venue::{ApiCreds, Clob, Signer};
use crossbeam_channel::Sender;

use crate::cli::{OType, RunArgs};
use crate::live::msg::Msg;
use ipolicy::IPolicy;

/// Live venue access (None in --dry).
#[derive(Clone)]
pub struct Venue {
    pub clob: Clob,
    pub api: ApiCreds,
    pub addr: String,
    pub sig_type: u8,
}

pub struct Pending {
    pub intent: Intent,
    pub mkt: i64,
    pub limit: f64,
    pub k: usize,
    pub n_ack: usize,
    pub resolved: bool,
    pub first_ack: bool,
    pub filled_sh: f64,
    pub order_id: Option<String>,
    /// copies that came back as transport errors (code 0)
    pub n_transport: usize,
    pub t_dec_mono: u64,
    pub t_recv_mono: u64,
}

#[derive(Debug, Clone)]
pub enum Timer {
    Book { cid: String, at: &'static str },
    GtcCancel { cid: String },
    DryAck { cid: String },
}

pub struct Exec {
    pub run: String,
    pub log: Logger,
    pub risk: RiskBook,
    pub venue: Option<Venue>,
    pub signer: Signer,
    pub owner: String,
    pub ipol: Box<dyn IPolicy>,
    pub tx: Sender<Msg>,
    pub order_type: OType,
    pub k: usize,
    pub gtc_cancel_ms: u64,
    pub dry_ack_ms: u64,
    pub orders: HashMap<String, Pending>,
    pub by_oid: HashMap<String, String>,
    pub timers: BinaryHeap<Reverse<(u64, u64, usize)>>,
    pub timer_jobs: HashMap<usize, Timer>,
    pub seq: u64,
    pub trade_ids: HashSet<String>,
    /// wall s of the last order sent (read by the trade poll)
    pub last_send: Arc<AtomicU64>,
    pub stop_reason: Option<String>,
    /// decision -> first copy on the wire (ns), receipt -> first copy (ns), sign (ns)
    pub lat_dec_send: Vec<u64>,
    pub lat_recv_send: Vec<u64>,
    pub lat_sign: Vec<u64>,
    pub n: HashMap<&'static str, u64>,
}

pub const FATAL: [&str; 5] = ["geoblock", "closed_only", "banned", "auth", "forbidden"];

impl Exec {
    #[allow(clippy::too_many_arguments)]
    pub fn new(run: String, log: Logger, risk: RiskBook, venue: Option<Venue>, signer: Signer, owner: String,
               ipol: Box<dyn IPolicy>, tx: Sender<Msg>, a: &RunArgs) -> Exec {
        let mut risk = risk;
        risk.set_bankroll(a.bankroll().expect("bankroll caps (validated by live::run)"));
        Exec { run, log, risk, venue, signer, owner, ipol, tx, order_type: a.order_type, k: a.k,
            gtc_cancel_ms: a.gtc_cancel_ms, dry_ack_ms: a.dry_ack_ms, orders: HashMap::new(), by_oid: HashMap::new(),
            timers: BinaryHeap::new(), timer_jobs: HashMap::new(), seq: 0, trade_ids: HashSet::new(),
            last_send: Arc::new(AtomicU64::new(0)), stop_reason: None, lat_dec_send: vec![], lat_recv_send: vec![], lat_sign: vec![],
            n: HashMap::new() }
    }

    pub fn bump(&mut self, k: &'static str) {
        *self.n.entry(k).or_default() += 1;
    }

    pub fn at(&mut self, due_mono: u64, t: Timer) {
        self.seq += 1;
        let id = self.seq as usize;
        self.timer_jobs.insert(id, t);
        self.timers.push(Reverse((due_mono, self.seq, id)));
    }

    pub fn dry(&self) -> bool {
        self.venue.is_none()
    }
}
