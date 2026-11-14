//! Build the decision engine from config: model JSON (sha256-pinned, feature list from the
//! model itself), the pzm fair weights, and the veto params. A gate model (research variant G,
//! e.g. `v1h_G_h250x_L0`: its inputs end in v1_value + the 7 book extras) runs on top of its
//! base value model, which is pinned by hash in `BASES`; tau comes from the gate's own JSON.
use anyhow::{bail, Context, Result};
use std::path::{Path, PathBuf};

use btl_model::{load, sha256_file, Forest, ModelDoc, ModelSpec};
use btl_signal::engine::{Ctx, Engine, Gate, VetoParams};
use btl_signal::features::{Pzm, Vectorizer};

/// Base value models a gate may stack on, with the sha256 of their trees JSON.
pub const BASES: [(&str, &str); 1] = [("v1_L0", "6ff7973182d747f42d247b5daf33fe012d23935b88e34e5b74adbc87d9b6c142")];

pub struct Loaded {
    pub engine: Engine,
    pub model: serde_json::Value,
}

/// `sha`: the configured hash; None = the exporter's sidecar `<model>.sha256` (dry / replay only).
pub fn model_spec(home: &Path, model: &str, sha: Option<&str>) -> Result<(ModelSpec, bool)> {
    let p = PathBuf::from(model);
    let path = if p.is_absolute() || model.contains('/') { home.join(p) } else {
        home.join(format!("data/out/predict/models/{model}.trees.json"))
    };
    match sha {
        Some(s) => Ok((ModelSpec { path, sha256: s.to_string() }, true)),
        None => {
            let side = path.with_extension("json.sha256");
            let s = std::fs::read_to_string(&side).with_context(|| format!("no --model-sha256 and no {}", side.display()))?;
            Ok((ModelSpec { path, sha256: s.trim().to_string() }, false))
        }
    }
}

fn info(doc: &ModelDoc, forest: &Forest, path: &Path, sha: &str) -> serde_json::Value {
    serde_json::json!({"name": doc.name, "path": path, "sha256": sha, "sha16": &sha[..16], "source": doc.source,
        "source_sha256": doc.source_sha256, "n_trees": forest.n_trees(), "n_nodes": forest.n_nodes(),
        "n_features": doc.vf.len(), "vf": doc.vf, "meta": doc.meta})
}

/// A gate doc -> (gate, base doc, base forest, base info).
fn gate(doc: &ModelDoc, forest: Forest, path: &Path) -> Result<(Gate, ModelDoc, Forest, serde_json::Value)> {
    let label = doc.meta["label"].as_str().unwrap_or("");
    if !label.starts_with('G') {
        bail!("refusing: model {} takes v1_value but is not a G gate (label {label:?})", doc.name);
    }
    let base = doc.meta["base"].as_str().and_then(|b| b.split_whitespace().next()).unwrap_or("");
    let Some(&(_, bsha)) = BASES.iter().find(|b| b.0 == base) else {
        bail!("refusing: gate {} names base {base:?}, not one of the pinned BASES", doc.name);
    };
    let bpath = path.with_file_name(format!("{base}.trees.json"));
    let (bdoc, bforest, bsha) = load(&ModelSpec { path: bpath.clone(), sha256: bsha.into() })?;
    let tau = doc.meta["tau"].as_f64().context("gate meta has no tau")?;
    let g = Gate::new(forest, &doc.vf, &bdoc.vf, tau)?;
    let binfo = info(&bdoc, &bforest, &bpath, &bsha);
    Ok((g, bdoc, bforest, binfo))
}

pub fn build(home: &Path, spec: &ModelSpec, pinned: bool, fair: &str, params: VetoParams) -> Result<Loaded> {
    let (doc, forest, sha): (ModelDoc, _, String) = load(spec)?;
    let mut model = info(&doc, &forest, &spec.path, &sha);
    let (vf, forest, g) = if doc.vf.iter().any(|v| v == "v1_value") {
        let (g, bdoc, bforest, binfo) = gate(&doc, forest, &spec.path)?;
        model["gate"] = serde_json::json!({"tau": g.tau, "base": binfo});
        (bdoc.vf, bforest, Some(g))
    } else {
        (doc.vf, forest, None)
    };
    let vec = Vectorizer::new(&vf)?;
    let fair_path = home.join(fair);
    let pzm = Pzm::load(&fair_path)?;
    model["pinned"] = pinned.into();
    model["fair"] = serde_json::json!(fair_path);
    model["fair_sha256"] = sha256_file(&fair_path)?.into();
    Ok(Loaded { engine: Engine::new(Ctx::new(pzm), forest, vec, params, g), model })
}
