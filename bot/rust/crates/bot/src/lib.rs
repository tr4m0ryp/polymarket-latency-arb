//! btclat-bot library: the live taker + model veto bot and its replay (binary in main.rs).
pub mod cli;
pub mod live;
pub mod replay;
pub mod setup;

#[derive(clap::Args, Clone, Debug)]
pub struct ModelArgs {
    /// model name under data/out/predict/models (<name>.trees.json) or a path to the JSON
    #[arg(long, default_value = "v1_L0")]
    pub model: String,
    /// sha256 the model JSON must have (required for live; default: the exporter's sidecar)
    #[arg(long)]
    pub model_sha256: Option<String>,
    #[arg(long, default_value = "data/out/strategy/fair-pzm.json")]
    pub fair: String,
}
