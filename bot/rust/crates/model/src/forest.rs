//! Flat node arrays of all trees (one allocation each), evaluated per row.
use anyhow::{bail, Result};

use crate::load::ModelDoc;

#[derive(Debug, Clone)]
pub struct Forest {
    feat: Vec<u32>,
    thr: Vec<f64>,
    // child indices are global; a leaf has left == u32::MAX
    left: Vec<u32>,
    right: Vec<u32>,
    miss_left: Vec<bool>,
    val: Vec<f64>,
    roots: Vec<u32>,
    pub baseline: f64,
    pub n_features: usize,
}

impl Forest {
    pub fn build(doc: &ModelDoc) -> Result<Forest> {
        let mut f = Forest {
            feat: vec![], thr: vec![], left: vec![], right: vec![], miss_left: vec![], val: vec![],
            roots: vec![], baseline: doc.baseline, n_features: doc.n_features,
        };
        for (ti, t) in doc.trees.iter().enumerate() {
            let n = t.feature.len();
            let lens = [t.threshold.len(), t.left.len(), t.right.len(), t.is_leaf.len(), t.value.len(), t.missing_left.len()];
            if lens.iter().any(|&l| l != n) || n == 0 {
                bail!("tree {ti}: node arrays of unequal length");
            }
            let off = f.feat.len() as u32;
            f.roots.push(off);
            for i in 0..n {
                let leaf = t.is_leaf[i] != 0;
                if !leaf {
                    let (l, r) = (t.left[i] as usize, t.right[i] as usize);
                    let fi = t.feature[i];
                    if l >= n || r >= n || fi < 0 || fi as usize >= doc.n_features {
                        bail!("tree {ti} node {i}: bad child or feature index");
                    }
                }
                f.feat.push(if leaf { 0 } else { t.feature[i] as u32 });
                f.thr.push(t.threshold[i]);
                f.left.push(if leaf { u32::MAX } else { off + t.left[i] });
                f.right.push(if leaf { u32::MAX } else { off + t.right[i] });
                f.miss_left.push(t.missing_left[i] != 0);
                f.val.push(t.value[i]);
            }
        }
        Ok(f)
    }

    pub fn n_trees(&self) -> usize {
        self.roots.len()
    }

    pub fn n_nodes(&self) -> usize {
        self.feat.len()
    }

    /// sklearn `predict` for one row: baseline, then each tree's leaf value added in order.
    #[inline]
    pub fn predict(&self, x: &[f64]) -> f64 {
        debug_assert_eq!(x.len(), self.n_features);
        let mut s = 0.0 + self.baseline;
        for &root in &self.roots {
            let mut i = root as usize;
            while self.left[i] != u32::MAX {
                let v = x[self.feat[i] as usize];
                let go_left = if v.is_nan() { self.miss_left[i] } else { v <= self.thr[i] };
                i = if go_left { self.left[i] } else { self.right[i] } as usize;
            }
            s += self.val[i];
        }
        s
    }
}
