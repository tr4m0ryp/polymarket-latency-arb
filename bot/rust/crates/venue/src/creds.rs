//! Credentials file (`~/.config/btclat/polymarket.env` by convention): KEY=VALUE lines, `#`
//! comments, same format and permission checks as btclat/trade/gate/creds.py.
//!
//! ```text
//! POLY_PRIVATE_KEY=0x<64 hex>   signer key (EOA controlling the Polymarket wallet)
//! POLY_FUNDER=0x<40 hex>        wallet holding the pUSD (signer's own address for EOA)
//! POLY_SIGNATURE_TYPE=3         0 EOA, 1 POLY_PROXY, 2 GNOSIS_SAFE, 3 POLY_1271
//! POLY_API_KEY / POLY_API_SECRET / POLY_API_PASSPHRASE   optional L2, all or none
//! ```
//!
//! Debug never prints a secret.

use std::collections::HashMap;
use std::fmt;
use std::os::unix::fs::MetadataExt;
use std::path::Path;

use anyhow::{bail, Result};

const API: [&str; 3] = ["POLY_API_KEY", "POLY_API_SECRET", "POLY_API_PASSPHRASE"];

/// L2 API credentials (HMAC secret is urlsafe base64). Debug shows only the key's first chars.
#[derive(Clone, PartialEq, Eq)]
pub struct ApiCreds {
    pub key: String,
    pub secret: String,
    pub passphrase: String,
}

impl fmt::Debug for ApiCreds {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let head: String = self.key.chars().take(4).collect();
        write!(f, "ApiCreds(key={head}..., secret=<redacted>, passphrase=<redacted>)")
    }
}

/// Parsed credentials. The private key is reachable only inside the crate (for the signer).
#[derive(Clone)]
pub struct Creds {
    pub(crate) private_key: String,
    funder: String,
    sig_type: u8,
    api: Option<ApiCreds>,
}

impl fmt::Debug for Creds {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let l2 = if self.api.is_some() { "set" } else { "derive" };
        write!(f, "Creds(funder={}, sig_type={}, l2={l2})", self.funder, self.sig_type)
    }
}

impl fmt::Display for Creds {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Debug::fmt(self, f)
    }
}

impl Creds {
    /// Build from values (tests, or keys held elsewhere); validated like the file.
    pub fn new(private_key: &str, funder: &str, sig_type: u8, api: Option<ApiCreds>) -> Result<Creds> {
        let pk = if private_key.starts_with("0x") { private_key.to_string() } else { format!("0x{private_key}") };
        if !is_hex(&pk, 64) {
            bail!("POLY_PRIVATE_KEY must be 32 bytes hex");
        }
        if !is_hex(funder, 40) {
            bail!("POLY_FUNDER must be a 0x address (40 hex)");
        }
        if sig_type > 3 {
            bail!("POLY_SIGNATURE_TYPE must be 0, 1, 2 or 3");
        }
        Ok(Creds { private_key: pk, funder: funder.to_string(), sig_type, api })
    }

    pub fn sig_type(&self) -> u8 {
        self.sig_type
    }

    /// The funder exactly as written in the file (it goes verbatim into the order's `maker`).
    pub fn funder(&self) -> &str {
        &self.funder
    }

    pub fn has_l2(&self) -> bool {
        self.api.is_some()
    }

    pub fn api(&self) -> Option<&ApiCreds> {
        self.api.as_ref()
    }
}

fn is_hex(s: &str, n: usize) -> bool {
    s.len() == n + 2 && s.starts_with("0x") && s[2..].bytes().all(|b| b.is_ascii_hexdigit())
}

/// Refuse a file anyone else could read or swap: regular, ours, mode & 077 == 0, and a parent
/// directory not writable by group/others.
pub fn check_perms(path: &Path) -> Result<()> {
    let md = match std::fs::metadata(path) {
        Ok(m) => m,
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
            bail!("no credentials file {}; see btclat/trade/gate/creds.py for the format", path.display())
        }
        Err(e) => bail!("cannot stat {}: {e}", path.display()),
    };
    if !md.file_type().is_file() {
        bail!("{} is not a regular file", path.display());
    }
    // SAFETY: getuid has no preconditions and cannot fail.
    let uid = unsafe { libc::getuid() };
    if md.uid() != uid {
        bail!("{} is owned by uid {}, not by this user ({uid})", path.display(), md.uid());
    }
    if md.mode() & 0o077 != 0 {
        bail!("{} has mode {:#o}; run: chmod 600 {}", path.display(), md.mode() & 0o777, path.display());
    }
    let parent = match path.parent() {
        Some(p) if !p.as_os_str().is_empty() => p,
        _ => Path::new("."),
    };
    if std::fs::metadata(parent)?.mode() & 0o022 != 0 {
        bail!("{} is writable by group/others; run: chmod 700 {}", parent.display(), parent.display());
    }
    Ok(())
}

/// KEY=VALUE lines; blank lines and `#` comments skipped; values trimmed of quotes.
pub fn parse_env(text: &str) -> Result<HashMap<String, String>> {
    let mut out = HashMap::new();
    for (n, raw) in text.lines().enumerate() {
        let line = raw.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let Some((k, v)) = line.split_once('=') else {
            bail!("credentials line {}: expected KEY=VALUE", n + 1);
        };
        let v = v.trim().trim_matches('"').trim_matches('\'');
        out.insert(k.trim().to_string(), v.to_string());
    }
    Ok(out)
}

/// Load and validate the credentials file (permissions first, then values).
pub fn load_creds(path: &Path) -> Result<Creds> {
    check_perms(path)?;
    let d = parse_env(&std::fs::read_to_string(path)?)?;
    let get = |k: &str| d.get(k).cloned().unwrap_or_default();
    let st = match get("POLY_SIGNATURE_TYPE").as_str() {
        "0" => 0,
        "1" => 1,
        "2" => 2,
        "3" => 3,
        _ => bail!("POLY_SIGNATURE_TYPE must be 0, 1, 2 or 3"),
    };
    let api: Vec<String> = API.iter().map(|k| get(k)).collect();
    let set = api.iter().filter(|v| !v.is_empty()).count();
    if set != 0 && set != 3 {
        bail!("set all of {API:?} or none (then they are derived)");
    }
    let api = (set == 3).then(|| ApiCreds { key: api[0].clone(), secret: api[1].clone(), passphrase: api[2].clone() });
    Creds::new(&get("POLY_PRIVATE_KEY"), &get("POLY_FUNDER"), st, api)
}

#[cfg(test)]
#[path = "creds_tests.rs"]
mod tests;
