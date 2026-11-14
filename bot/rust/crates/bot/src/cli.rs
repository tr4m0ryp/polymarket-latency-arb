//! `btclat-bot run` arguments. Every money limit can only be LOWERED from the hard values in
//! btl_risk (the risk crate refuses a looser one); the limit offset i is 0 unless a flag says
//! otherwise, and the randomized-i experiment has its own flag.
use clap::{Args, ValueEnum};
use std::path::PathBuf;

use btl_risk::bankroll as bk;
use btl_risk::{Bankroll, SidePolicy, Sizing};

use crate::ModelArgs;

#[derive(Copy, Clone, Debug, PartialEq, Eq, ValueEnum, serde::Serialize)]
pub enum IMode {
    /// limit = seen ask + --i (default 0)
    Fixed,
    /// limit = seen ask + i, i drawn uniformly per order from --i-set (experiment)
    Random,
    /// i from a plugged-in predictor (hook; none is built yet, refused at start)
    Predicted,
}

#[derive(Copy, Clone, Debug, PartialEq, Eq, ValueEnum, serde::Serialize)]
pub enum OType {
    Fak,
    Fok,
    Gtc,
}

#[derive(Copy, Clone, Debug, PartialEq, Eq, ValueEnum, serde::Serialize)]
pub enum LogFeeds {
    All,
    None,
}

/// Order sizing (reports/bankroll-caps.md): fixed shares, or a stake scaled by the live equity.
#[derive(Copy, Clone, Debug, PartialEq, Eq, ValueEnum, serde::Serialize)]
pub enum SizeMode {
    /// --size shares per order
    Fixed,
    /// stake = --frac x equity per order
    Frac,
    /// stake = --kelly x model edge / (1 - p) x equity
    Kelly,
}

#[derive(Copy, Clone, Debug, PartialEq, Eq, ValueEnum, serde::Serialize)]
pub enum SideArg {
    /// no side rule
    Any,
    /// one direction per market (no order opposite a known fill)
    One,
    /// --max-fills counts per side, the opposite side is free
    PerSide,
    /// opposite orders only up to the net share imbalance (never raise the worst-case loss)
    Hedge,
}

#[derive(Args, Clone, Debug, serde::Serialize)]
pub struct RunArgs {
    /// no keys, no orders: logs what it would send
    #[arg(long, conflicts_with = "i_approve")]
    pub dry: bool,
    /// REAL orders (the user approved this run)
    #[arg(long)]
    pub i_approve: bool,
    /// run name (default <utc yyyymmdd-hhmm>-<mode>-<host>); logs go to <root>/<run>/
    #[arg(long)]
    pub run: Option<String>,
    #[arg(long, default_value = "data/trade")]
    pub root: PathBuf,
    /// stop after this many hours
    #[arg(long)]
    pub hours: Option<f64>,
    /// config dir with polymarket.env, KILL and state/ (default $BTCLAT_CONFIG or ~/.config/btclat)
    #[arg(long)]
    pub config: Option<PathBuf>,
    /// limit offset i ($ above the seen ask); binding default 0
    #[arg(long, default_value_t = 0.0)]
    pub i: f64,
    /// required for any i > 0 (logged loudly)
    #[arg(long)]
    pub allow_i_positive: bool,
    #[arg(long, value_enum, default_value_t = IMode::Fixed)]
    pub i_mode: IMode,
    /// i values for --i-mode random, e.g. 0,0.01
    #[arg(long, value_delimiter = ',')]
    pub i_set: Vec<f64>,
    /// required for --i-mode random (randomized-i experiment)
    #[arg(long)]
    pub i_random_experiment: bool,
    #[arg(long, value_enum, default_value_t = OType::Fak)]
    pub order_type: OType,
    /// GTC only: cancel the rest of an unfilled GTC this long after its ack
    #[arg(long, default_value_t = 1000)]
    pub gtc_cancel_ms: u64,
    /// identical copies per order / cancel on separate connections (1..3)
    #[arg(long, default_value_t = 3)]
    pub k: usize,
    /// order sizing; the default scales with the live balance (reports/bankroll-caps.md)
    #[arg(long, value_enum, default_value_t = default_sizing())]
    pub sizing: SizeMode,
    /// --sizing fixed: shares per order (venue minimum 5)
    #[arg(long, default_value_t = 60.0)]
    pub size: f64,
    /// --sizing frac: fraction of equity staked per order
    #[arg(long, default_value_t = bk::DEFAULT_FRAC)]
    pub frac: f64,
    /// --sizing kelly: Kelly multiplier on the model's predicted edge
    #[arg(long, default_value_t = bk::DEFAULT_KELLY)]
    pub kelly: f64,
    /// shares per order, ceiling
    #[arg(long, default_value_t = bk::DEFAULT_MAX_SH)]
    pub max_sh: f64,
    /// one market's cost + fee (fills + in flight) <= x equity; 1 = off
    #[arg(long, default_value_t = bk::DEFAULT_MARKET_FRAC)]
    pub market_frac: f64,
    /// all open positions + in flight <= x equity; 1 = off
    #[arg(long, default_value_t = bk::DEFAULT_OPEN_FRAC)]
    pub open_frac: f64,
    #[arg(long, value_enum, default_value_t = default_side())]
    pub side_policy: SideArg,
    /// fills per market (per side under --side-policy per-side); 0 = off
    #[arg(long, default_value_t = bk::DEFAULT_MAX_FILLS)]
    pub max_fills: u32,
    /// pause the UTC day below (1 - y) x the day's peak equity; 1 = off
    #[arg(long, default_value_t = bk::DEFAULT_DD_STOP)]
    pub dd_stop: f64,
    /// halt for good below x the all-time peak equity (<state>/halt; a human removes it); 1 = off
    #[arg(long, default_value_t = bk::DEFAULT_FLOOR)]
    pub floor: f64,
    /// $ of the venue balance the bot never touches: sizing, caps, drawdown and affordability
    /// all use balance - reserve; nothing is sent when that is <= 0 (deploy: RESERVE in bot.env)
    #[arg(long, default_value_t = 0.0)]
    pub reserve: f64,
    /// --dry only: the working bankroll the dry run sizes from (the reserve comes on top)
    #[arg(long, default_value_t = 100.0)]
    pub dry_balance: f64,
    /// Binance connections per stream (first arrival wins)
    #[arg(long, default_value_t = 4)]
    pub conns: usize,
    #[arg(long, value_enum, default_value_t = LogFeeds::All)]
    pub log_feeds: LogFeeds,
    /// dry only: simulated ack delay (keeps the in-flight / refractory pacing realistic)
    #[arg(long, default_value_t = 250)]
    pub dry_ack_ms: u64,
    /// CLOB REST host (tests point it at a local mock)
    #[arg(long, default_value = "https://clob.polymarket.com")]
    pub clob_host: String,
    #[arg(long)]
    pub max_orders_hour: Option<u32>,
    #[arg(long)]
    pub loss_cap: Option<f64>,
    #[arg(long)]
    pub max_exposure: Option<f64>,
    #[arg(long)]
    pub max_notional: Option<f64>,
    /// per-market seconds between sent orders (can only be raised above 0.2)
    #[arg(long)]
    pub refractory: Option<f64>,
    #[command(flatten)]
    #[serde(skip)]
    pub model: ModelArgs,
}

fn default_sizing() -> SizeMode {
    SizeMode::from_str(bk::DEFAULT_SIZING, true).expect("DEFAULT_SIZING")
}

fn default_side() -> SideArg {
    SideArg::from_str(bk::DEFAULT_SIDE, true).expect("DEFAULT_SIDE")
}

impl RunArgs {
    /// The bankroll caps of this run (fractions >= 1 and max_fills 0 switch a cap off).
    pub fn bankroll(&self) -> Result<Bankroll, btl_risk::LimitError> {
        let off = |v: f64| if v >= 1.0 { None } else { Some(v) };
        Bankroll {
            sizing: match self.sizing {
                SizeMode::Fixed => Sizing::Fixed(self.size),
                SizeMode::Frac => Sizing::Frac(self.frac),
                SizeMode::Kelly => Sizing::Kelly(self.kelly),
            },
            max_sh: self.max_sh,
            market_frac: off(self.market_frac),
            open_frac: off(self.open_frac),
            side: match self.side_policy {
                SideArg::Any => SidePolicy::Any,
                SideArg::One => SidePolicy::OneDirection,
                SideArg::PerSide => SidePolicy::PerSide,
                SideArg::Hedge => SidePolicy::HedgeOnly,
            },
            max_fills: if self.max_fills == 0 { u32::MAX } else { self.max_fills },
            dd_stop: off(self.dd_stop),
            reserve: self.reserve,
            floor: off(self.floor),
        }
        .checked()
    }
}
