//! Model parity: the Rust evaluator vs sklearn `predict` on recorded decision rows.
//!
//! Fixture: `python3 -m btclat.paper.replay.decisions ...` writes model_rows.bin/json (the
//! Python bot's model inputs on recorded tape plus sklearn's predictions). The directory is
//! BTL_PARITY_DIR or the newest data/cache/rust/dec-*; the test is skipped (with a message)
//! when none exists, and fails when BTL_REQUIRE_PARITY=1.
use std::path::{Path, PathBuf};

use btl_model::{load, ModelSpec};

fn repo() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../../..").canonicalize().unwrap()
}

fn fixture() -> Option<PathBuf> {
    if let Ok(d) = std::env::var("BTL_PARITY_DIR") {
        return Some(PathBuf::from(d));
    }
    let mut v: Vec<PathBuf> = std::fs::read_dir(repo().join("data/cache/rust")).ok()?
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| p.join("model_rows.bin").exists())
        .collect();
    v.sort();
    v.pop()
}

#[test]
fn sklearn_parity_on_recorded_rows() {
    let Some(dir) = fixture() else {
        assert!(std::env::var("BTL_REQUIRE_PARITY").is_err(), "no parity fixture");
        eprintln!("SKIP: no data/cache/rust/dec-* fixture (run python3 -m btclat.paper.replay.decisions)");
        return;
    };
    let info: serde_json::Value = serde_json::from_slice(&std::fs::read(dir.join("model_rows.json")).unwrap()).unwrap();
    let name = info["model"].as_str().unwrap();
    let path = repo().join(format!("data/out/predict/models/{name}.trees.json"));
    let sha = std::fs::read_to_string(path.with_extension("json.sha256")).unwrap().trim().to_string();
    let (doc, forest, _) = load(&ModelSpec { path, sha256: sha }).unwrap();
    let nf = info["n_features"].as_u64().unwrap() as usize;
    assert_eq!(nf, doc.vf.len());
    let vf: Vec<String> = serde_json::from_value(info["vf"].clone()).unwrap();
    assert_eq!(vf, doc.vf, "fixture and model feature lists differ");
    let raw = std::fs::read(dir.join("model_rows.bin")).unwrap();
    let vals: Vec<f64> = raw.chunks_exact(8).map(|c| f64::from_le_bytes(c.try_into().unwrap())).collect();
    let w = 2 * nf + 2;
    assert_eq!(vals.len() % w, 0);
    let n = vals.len() / w;
    let (mut max_rel, mut n_exact) = (0.0f64, 0usize);
    for r in vals.chunks_exact(w) {
        for (x, want) in [(&r[..nf], r[2 * nf]), (&r[nf..2 * nf], r[2 * nf + 1])] {
            let got = forest.predict(x);
            let rel = (got - want).abs() / want.abs().max(1e-300);
            max_rel = max_rel.max(rel);
            n_exact += (got == want) as usize;
        }
    }
    eprintln!("model parity {}: {} rows x 2 sides, {} bit-identical, max rel diff {:e}", dir.display(), n, n_exact, max_rel);
    assert!(n >= 10_000 || std::env::var("BTL_REQUIRE_PARITY").is_err(), "need >= 10k rows, have {n}");
    assert!(max_rel <= 1e-9, "max rel diff {max_rel:e} > 1e-9");
}
