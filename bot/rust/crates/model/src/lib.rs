//! Frozen value model of the live bot: a sklearn HistGradientBoostingRegressor exported to JSON
//! by `research/predict/infer/export.py`, loaded with a sha256 check and evaluated exactly as
//! sklearn's `predict` does on float64 inputs (baseline + per-tree leaf values, summed in tree
//! order; `x <= threshold` goes left; NaN follows `missing_go_to_left`).
mod forest;
mod load;

pub use forest::Forest;
pub use load::{load, sha256_file, ModelDoc, ModelSpec};
