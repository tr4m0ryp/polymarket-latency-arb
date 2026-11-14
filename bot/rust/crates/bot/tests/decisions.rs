//! Decision parity: the Rust replay vs the Python paper bot's decisions on the same recorded tape.
//!
//! Fixtures: every data/cache/rust/*/ with run.json + decisions.jsonl whose raw tape is present:
//! dec-* (v1 veto, `python3 -m btclat.paper.replay.decisions`, limit = seen + 0.02) and v1h-*
//! (the hold-aware gate `v1h_G_h250x_L0`, `python3 -m btclat.paper.replay.gated`, limit = seen,
//! plus gate_rows.jsonl: the 7 book extras and the gate prediction of every v1-pass row, which
//! must be bit-identical). Runs in release builds (a debug replay of hours of tape is slow) or
//! with BTL_REQUIRE_PARITY=1, which also fails the test when no fixture exists. Every order must
//! match (time to 1 us, market, side, limit).
use std::path::PathBuf;

use btl_bot::{replay, setup};

fn repo() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../..").canonicalize().unwrap()
}

#[test]
fn rust_replay_matches_python_decisions() {
    let require = std::env::var("BTL_REQUIRE_PARITY").is_ok();
    if cfg!(debug_assertions) && !require {
        eprintln!("SKIP: decision parity runs in --release (or with BTL_REQUIRE_PARITY=1)");
        return;
    }
    let home = repo();
    let mut dirs: Vec<PathBuf> = std::fs::read_dir(home.join("data/cache/rust")).map(|r| r.filter_map(|e| e.ok())
        .map(|e| e.path()).filter(|p| p.join("run.json").exists() && p.join("decisions.jsonl").exists()).collect())
        .unwrap_or_default();
    dirs.sort();
    let mut checked = 0;
    for d in dirs {
        let run: serde_json::Value = serde_json::from_slice(&std::fs::read(d.join("run.json")).unwrap()).unwrap();
        let root = home.join(run["root"].as_str().unwrap());
        if !root.exists() {
            continue;
        }
        let hours: Vec<i64> = run["hours"].as_array().unwrap().iter().map(|h| h.as_i64().unwrap()).collect();
        let (spec, pinned) = setup::model_spec(&home, run["model"].as_str().unwrap(), None).unwrap();
        let l = setup::build(&home, &spec, pinned, "data/out/strategy/fair-pzm.json", Default::default()).unwrap();
        let out = std::env::temp_dir().join(format!("btl-parity-{}-{}", std::process::id(), checked));
        let i = run["i"].as_f64().unwrap_or(0.02);
        let st = replay::run(l.engine, l.model, replay::Opts { root: &root, hours: hours.clone(), out: &out, i,
            expect: Some(&d.join("decisions.jsonl")), dump_rows: false }).unwrap();
        let p = &st["parity"];
        eprintln!("decision parity {} hours {:?}: python {} rust {} matched {} (rate {})", d.display(), hours,
            p["python"], p["rust"], p["matched"], p["match_rate"]);
        assert_eq!(p["python"], p["rust"]);
        assert_eq!(p["matched"], p["python"], "unmatched: {}", serde_json::to_string(&p["only_python"]).unwrap());
        assert_eq!(p["max_pred_abs_diff_aligned"].as_f64(), Some(0.0));
        if let Some(g) = st.get("gate_parity") {
            eprintln!("gate parity: python {} rust {} matched {} x_mismatch {} gate_mismatch {}", g["python"], g["rust"],
                g["matched"], g["x_mismatch"], g["gate_mismatch"]);
            assert_eq!(g["python"], g["rust"]);
            assert_eq!(g["matched"], g["python"]);
            assert_eq!(g["x_mismatch"], serde_json::json!([0, 0, 0, 0, 0, 0, 0]), "{}", g["examples"]);
            assert_eq!(g["gate_mismatch"], 0, "{}", g["examples"]);
        }
        let _ = std::fs::remove_dir_all(&out);
        checked += 1;
    }
    assert!(checked > 0 || !require, "no decision fixture with its tape");
    if checked == 0 {
        eprintln!("SKIP: no data/cache/rust/dec-* fixture (run python3 -m btclat.paper.replay.decisions)");
    }
}
