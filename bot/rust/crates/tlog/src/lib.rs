//! btl_log: append-only structured JSONL event logger for the latency-critical bot.
//!
//! The hot path ([`Logger::log`], [`Logger::log_at`], [`Logger::log_raw`]) never blocks on I/O:
//! it stamps a sequence number and pushes onto a bounded channel; one writer thread assembles
//! the line, writes it through a `BufWriter` (flushed at least every 200 ms), rotates hourly by the
//! record's `wall_ns` and gzips finished hours in the background. A full channel drops the record
//! and counts it ([`Logger::dropped`]; reported in the periodic and final `log_stats` line).
//!
//! # Files
//!
//! `<dir>/<prefix>-<HOUR>.jsonl` while open, `<prefix>-<HOUR>.jsonl.gz` once finished. A process
//! never reopens an existing file: if `<prefix>-<HOUR>.jsonl` or `.jsonl.gz` already exists (an
//! earlier process in the same hour) the next free suffix is used, `<prefix>-<HOUR>.<n>.jsonl`
//! (n = 1, 2, ...). Plain files left behind by a crash are gzipped in the background at open.
//! Rotation only moves forward: a record whose `wall_ns` is in an earlier hour than the open file
//! (late, caller-supplied timestamp) is written to the open file. `seq` is assigned at call time, so
//! lines from several threads may be slightly out of `seq` order and a dropped record leaves a
//! gap; readers sort by `seq`. Use a distinct `run` per process (seq restarts at 0).
//!
//! Internal record: `log_stats` with `written`, `dropped`, `queued`, `io_errors` every 10 s and at close.
//!
//! # Event schema (the contract with the Python reader, btclat/trade/report/rust/)
//!
//! ```text
//! # btclat-bot event log contract (Rust writer <-> Python reader)
//!
//! Files: <run_dir>/bot-<HOUR>.jsonl while the hour is open; gzip'd to bot-<HOUR>.jsonl.gz on rotate/close
//! (HOUR = wall_ns // 3_600_000_000_000, epoch hour as in btclat/live/sink.py). run_dir = data/trade/<run>/.
//! A reader must accept both .jsonl and .jsonl.gz, and tolerate a truncated last line / gzip without trailer.
//!
//! Every line is one JSON object with the common fields
//!   run (str), seq (u64, strictly increasing per run), mono_ns (u64, CLOCK_MONOTONIC ns), wall_ns (u64, unix ns),
//!   kind (str)
//! plus the kind's fields. Prices are in the BOUGHT token's terms (0..1 floats) unless the name says _up.
//! "t" fields are wall seconds (float). cid = client order id string "<run>:<n>" (same as the signal id sig).
//!
//! kinds (writer may add fields; reader must ignore unknown fields/kinds):
//! - start    mode ("dry"|"live"|"replay"), args (obj), model {name, sha256, sha16, n_trees}, limits (obj),
//!            i_mode ("fixed"|"random"|"predicted"), i (float, fixed), i_set ([float]), host, version
//! - market   slug, start, end, up, down, condition_id, tick
//! - conn     feed, conn (int), state ("connect"|"error"|"close"), err?
//! - feed     src ("sb" spot book | "pb" perp book | "st" spot trade | "pt" perp trade | "pm" clob book), conn, t,
//!            vts (venue/exchange stamp, s, may be null); sb/pb: b,a,bq,aq,u; st/pt: px,q,m,id; pm: slug,snap,n,bb,ba,top
//!            (bb/ba = Up-token best bid/ask ticks 0..100 after applying; top = top changed)
//! - signal   sig, slug, t, src, trig_side (+1/-1/0), p_dmic, s_dmic, pu, pdn, edge, side, seen, bb, ba, secs_left,
//!            decision ("order"|"veto"|"skip"), reason (null for order; veto: "margin"|"side"|"gate_band"|"gate_tleft"|
//!            "gate_fav"|"gate_book"|"refractory"; skip: risk reason), feat_ns, model_ns, features (obj name->float|null)
//! - order    sig, cid, slug, token, up (bool), side (+1/-1), seen, i, i_mode, limit, size, order_type ("FAK"|"FOK"|"GTC"),
//!            k (copies), dry (bool), t (wall s of decision), t_dec_mono_ns, build_ns, sign_ns, maker_amount, taker_amount,
//!            salt, ts_ms
//! - send     cid, copy, conn, t_send_mono_ns, t_send_wall_ns
//! - ack      cid, copy, conn, code (http, 0 = transport error), ok (bool), status, order_id, latency_ns,
//!            t_ack_mono_ns, t_ack_wall_ns, cf_ray, pop, http, err_kind, err, fill_sh, fill_cost, px, trade_ids, body
//!            (copies after the first usually come back as duplicate rejects: err_kind "duplicate")
//! - book     cid, at ("signal"|"send"|"ack"|"ack+3s"|"ack+10s"), slug, t, up (bool, side bought), bids [[px,sz]x<=5],
//!            asks [[px,sz]x<=5] (bought token terms, best first), bb, ba (bought token best bid/ask, float),
//!            mid (bought token mid or null), depth_le_limit (shares offered at <= the order limit)
//! - fill     cid, order_id, src ("post"|"lookup"|"trade_poll"|"user_ws"), sh, px, cost, fee, trade_id, match_t, status
//! - cancel   what ("all"|order id), reason, code, ok, latency_ns, body
//! - skip     sig, cid, reason
//! - error    where, err
//! - stats    free-form counters (feeds per src, dups, latencies p50/p90/p99 in us, rss_mb, ...)
//! - settle   slug, outcome (1.0 Up won, 0.0 Down won)
//! - stop     reason, cancel_all_ok
//! ```
//!
//! Extension to the schema above: the logger itself writes `kind = "log_stats"` lines
//! (`written`, `dropped`, `queued`, `io_errors`).

mod clock;
mod logger;
mod record;
mod writer;

pub use clock::{mono_ns, now, wall_ns, HOUR_NS};
pub use logger::{Config, Logger};
