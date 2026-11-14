//! Incremental market state, a twin of btclat/paper/state: Binance books, Polymarket book,
//! spot trade flow, the settlement inputs and the book-survival history of the gate.
pub mod book;
mod book_feats;
pub mod flow;
pub mod hist;
pub mod pm;
pub mod series;
pub mod settle;

pub use book::BookState;
pub use flow::TradeFlow;
pub use hist::PmHist;
pub use pm::PmBook;
pub use series::Series;
pub use settle::{p_model, LockedTwap, Settle};
