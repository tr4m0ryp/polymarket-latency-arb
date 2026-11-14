//! btclat-bot: the live taker + model veto bot (`vt_v1_m0.02_trigger`) and its replay.
//!
//!   btclat-bot replay --root data/paper/dublin-20261012/raw --hours 497750,497751 [--expect py/decisions.jsonl]
//!   btclat-bot run --dry  [--hours H] [--run NAME]                       (no keys, no orders)
//!   btclat-bot run --i-approve --model-sha256 <hex> [--hours H] ...      (REAL orders)

use anyhow::Result;
use clap::{Parser, Subcommand};
use std::path::PathBuf;

use btl_bot::{cli, live, replay, setup, ModelArgs};

#[derive(Parser)]
#[command(name = "btclat-bot", version)]
struct Cli {
    /// repo root on this host (paths below are relative to it)
    #[arg(long, env = "BTCLAT_HOME", default_value = ".")]
    home: PathBuf,
    #[command(subcommand)]
    cmd: Cmd,
}


#[derive(Subcommand)]
enum Cmd {
    /// The bot on live feeds: --dry (no keys, no orders) or --i-approve (REAL orders).
    Run(Box<cli::RunArgs>),
    /// Run the decision engine over recorded raw tape (no network, no orders).
    Replay {
        #[arg(long)]
        root: PathBuf,
        /// comma list of epoch hours; the first is warm-up
        #[arg(long, value_delimiter = ',')]
        hours: Vec<i64>,
        #[arg(long)]
        out: Option<PathBuf>,
        /// limit offset for the decisions file (the Python arm's slip is 0.02)
        #[arg(long, default_value_t = 0.0)]
        i: f64,
        #[arg(long)]
        expect: Option<PathBuf>,
        /// also write every trigger row's features into signals.jsonl
        #[arg(long)]
        dump_rows: bool,
        #[command(flatten)]
        model: ModelArgs,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.cmd {
        Cmd::Run(a) => std::process::exit(live::run(&cli.home, *a)?),
        Cmd::Replay { root, hours, out, i, expect, dump_rows, model } => {
            let (spec, pinned) = setup::model_spec(&cli.home, &model.model, model.model_sha256.as_deref())?;
            let l = setup::build(&cli.home, &spec, pinned, &model.fair, Default::default())?;
            let out = out.unwrap_or_else(|| cli.home.join(format!("data/cache/rust/replay-{}-{}", hours[0], hours[hours.len() - 1])));
            let root = if root.is_absolute() { root } else { cli.home.join(root) };
            let st = replay::run(l.engine, l.model, replay::Opts { root: &root, hours, out: &out, i, expect: expect.as_deref(), dump_rows })?;
            let mut brief = st.clone();
            brief["model"] = serde_json::json!(st["model"]["name"]);
            if let Some(p) = brief.get_mut("parity") {
                p["only_python"] = serde_json::json!(p["only_python"].as_array().map(|v| v.len()));
                p["only_rust"] = serde_json::json!(p["only_rust"].as_array().map(|v| v.len()));
            }
            if let Some(g) = brief.get_mut("gate_parity") {
                g["examples"] = serde_json::json!(g["examples"].as_array().map(|v| v.len()));
            }
            println!("{}", serde_json::to_string_pretty(&brief)?);
        }
    }
    Ok(())
}
