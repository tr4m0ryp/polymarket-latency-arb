//! The decision engine shared by the live bot and the replay: world state per event, the
//! value-candidate schedule and the veto arm (btclat/paper/engine + arms/decide.py, veto only).
pub mod core;
pub mod gate;
pub mod market;
pub mod signal;
pub mod veto;
pub mod world;

pub use self::core::Engine;
pub use gate::Gate;
pub use signal::{Signal, Stats};
pub use market::{Ctx, MarketCtx, MarketMeta};
pub use veto::{Decision, VetoParams};
pub use world::World;
