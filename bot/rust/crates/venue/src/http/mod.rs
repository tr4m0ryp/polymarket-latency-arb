//! The CLOB over k warm HTTP/2 connections: timed requests, hedged (identical-copy) sends,
//! keep-warm, server clock offset, and the REST endpoints of btclat/trade/venue/client.py.

pub mod conn;
pub mod endpoints;
pub mod hedge;
pub mod pool;
pub mod resp;
pub mod warm;

pub use pool::{Clob, GEOBLOCK, HOST, MAX_CONNS};
pub use resp::Resp;
