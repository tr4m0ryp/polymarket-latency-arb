//! The decision row's columns (btclat/paper/features/raw.py `row`), by index. A row is a fixed
//! array; NaN stands for a column the Python dict lacks (`f.get(c, nan)`).
pub const BOOK: [&str; 29] = ["imb", "spr", "lq", "dmic0.025", "dmic0.05", "dmic0.1", "dmic0.25", "dmic1",
    "dmid0.1", "dmid1", "dmid5", "micoff", "ofi0.025", "ofi0.1", "ofi0.4", "ofi1.6", "depb", "depa", "lam",
    "up0.4", "dn0.4", "up2", "dn2", "ttdb", "ttda", "ttd_rel", "ttd_min", "tsm", "lastdir"];
pub const T: usize = 0;
pub const PERP: usize = 1; // p_<BOOK[k]> at PERP + k
pub const SPOT: usize = PERP + 29; // s_<BOOK[k]>
pub const ST_SV005: usize = SPOT + 29;
pub const ST_SV02: usize = ST_SV005 + 1;
pub const ST_SV1: usize = ST_SV005 + 2;
pub const ST_TN: usize = ST_SV005 + 3;
pub const ST_BIG: usize = ST_SV005 + 4;
pub const BASIS_DEV: usize = ST_SV005 + 5;
pub const MIC_DEV: usize = BASIS_DEV + 1;
pub const PM_BB: usize = MIC_DEV + 1;
pub const PM_BA: usize = PM_BB + 1;
pub const PM_MID: usize = PM_BB + 2;
pub const PM_SPR: usize = PM_BB + 3;
pub const SECS_LEFT: usize = PM_BB + 4;
pub const LZS: usize = PM_BB + 5;
pub const SIGMA: usize = PM_BB + 6;
pub const PM_TSC: usize = PM_BB + 7;
pub const PM_STALE: usize = PM_BB + 8;
pub const BK0: usize = PM_BB + 9;
pub const BK1: usize = PM_BB + 10;
pub const BK2: usize = PM_BB + 11;
pub const GAP: usize = PM_BB + 12;
pub const ZS: usize = PM_BB + 13;
pub const FAIR_DZ: usize = ZS + 1;
pub const FAIR_P: usize = ZS + 2;
pub const N: usize = FAIR_P + 1;

pub const P_DMIC01: usize = PERP + 5;
pub const S_DMIC01: usize = SPOT + 5;

/// Column names in index order (p_/s_ prefixes, st_ flow, the rest as in raw.py).
pub fn all() -> Vec<String> {
    let mut v = vec!["t".to_string()];
    for p in ["p", "s"] {
        v.extend(BOOK.iter().map(|b| format!("{p}_{b}")));
    }
    v.extend(["st_sv0.05", "st_sv0.2", "st_sv1", "st_tn", "st_big", "basis_dev", "mic_dev", "pm_bb", "pm_ba",
        "pm_mid", "pm_spr", "secs_left", "lzs", "sigma", "pm_tsc", "pm_stale", "bk0", "bk1", "bk2", "gap", "zs",
        "fair_dz", "fair_p"].map(String::from));
    debug_assert_eq!(v.len(), N);
    v
}

pub fn index(name: &str) -> Option<usize> {
    all().iter().position(|c| c == name)
}

pub type Row = [f64; N];
