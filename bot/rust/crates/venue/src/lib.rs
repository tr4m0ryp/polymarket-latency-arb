//! btl_venue: the Polymarket CLOB venue layer of the latency bot. Credentials, CTF Exchange V2
//! order signing (byte-identical to py_clob_client_v2), L1/L2 auth headers, a pool of k warm
//! HTTP/2 connections with hedged (identical-copy) sends, response parsing and the user
//! channel websocket. Ports btclat/trade/venue/* and btclat/trade/maker/fills/userws.py.

pub mod auth;
pub mod clock;
pub mod creds;
pub mod http;
pub mod parse;
pub mod sign;
pub mod types;
pub mod userws;

pub use auth::l2::l2_headers;
pub use clock::{mono_ns, wall_ms, wall_ns};
pub use creds::{load_creds, ApiCreds, Creds};
pub use http::{Clob, Resp, HOST, MAX_CONNS};
pub use parse::OrderResult;
pub use sign::{new_salt, Signer};
pub use types::{OrderSpec, OrderType, Side, SignedOrder};
pub use userws::{UserMsg, WsState};
