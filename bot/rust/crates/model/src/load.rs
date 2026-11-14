//! Model JSON (format `btclat-hgb-v1`) and the sha256 gate: the bot refuses a model file whose
//! hash differs from the one it was configured with, so swapping models is a config change.
use anyhow::{bail, Context, Result};
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};

use crate::forest::Forest;

pub const FORMAT: &str = "btclat-hgb-v1";

#[derive(Debug, Deserialize)]
pub struct TreeDoc {
    pub feature: Vec<i64>,
    pub threshold: Vec<f64>,
    pub left: Vec<u32>,
    pub right: Vec<u32>,
    pub is_leaf: Vec<u8>,
    pub value: Vec<f64>,
    pub missing_left: Vec<u8>,
}

#[derive(Debug, Deserialize)]
pub struct ModelDoc {
    pub format: String,
    pub name: String,
    pub source: String,
    pub source_sha256: String,
    pub vf: Vec<String>,
    #[serde(default)]
    pub meta: serde_json::Value,
    pub baseline: f64,
    pub n_features: usize,
    pub trees: Vec<TreeDoc>,
}

/// Where the model lives and the hash it must have (both config inputs).
#[derive(Debug, Clone)]
pub struct ModelSpec {
    pub path: PathBuf,
    pub sha256: String,
}

pub fn sha256_file(path: &Path) -> Result<String> {
    let b = std::fs::read(path).with_context(|| format!("read {}", path.display()))?;
    Ok(hex::encode(Sha256::digest(&b)))
}

/// Load and check: file sha256 == spec.sha256 (lowercase hex), format, tree shapes.
pub fn load(spec: &ModelSpec) -> Result<(ModelDoc, Forest, String)> {
    let bytes = std::fs::read(&spec.path).with_context(|| format!("read model {}", spec.path.display()))?;
    let got = hex::encode(Sha256::digest(&bytes));
    if got != spec.sha256.to_lowercase() {
        bail!("refusing: model {} sha256 {} != configured {}", spec.path.display(), got, spec.sha256);
    }
    let doc: ModelDoc = serde_json::from_slice(&bytes).context("parse model json")?;
    if doc.format != FORMAT {
        bail!("refusing: model format {:?}, expected {FORMAT}", doc.format);
    }
    if doc.n_features != doc.vf.len() {
        bail!("refusing: model has {} inputs but vf lists {}", doc.n_features, doc.vf.len());
    }
    let forest = Forest::build(&doc)?;
    Ok((doc, forest, got))
}
