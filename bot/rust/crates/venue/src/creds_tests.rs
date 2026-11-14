use std::os::unix::fs::PermissionsExt;
use std::path::PathBuf;

use super::*;

const PK: &str = "4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f362318";
const FUNDER: &str = "0x6E0C80c90ea6C15917308F820Eac91Ce2724B5b5";

fn tmp_dir(tag: &str) -> PathBuf {
    let d = std::env::temp_dir().join(format!("btl_venue_creds_{tag}_{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&d);
    std::fs::create_dir_all(&d).unwrap();
    std::fs::set_permissions(&d, std::fs::Permissions::from_mode(0o700)).unwrap();
    d
}

fn write(dir: &Path, text: &str, mode: u32) -> PathBuf {
    let p = dir.join("polymarket.env");
    let _ = std::fs::remove_file(&p);
    std::fs::write(&p, text).unwrap();
    std::fs::set_permissions(&p, std::fs::Permissions::from_mode(mode)).unwrap();
    p
}

#[test]
fn loads_and_redacts() {
    let d = tmp_dir("ok");
    let text = format!("# test\nPOLY_PRIVATE_KEY={PK}\nPOLY_FUNDER=\"{FUNDER}\"\nPOLY_SIGNATURE_TYPE=3\n\
                        POLY_API_KEY=k-123456\nPOLY_API_SECRET=c2VjcmV0\nPOLY_API_PASSPHRASE=pp\n");
    let c = load_creds(&write(&d, &text, 0o600)).unwrap();
    assert_eq!((c.sig_type(), c.funder(), c.has_l2()), (3, FUNDER, true));
    assert_eq!(c.private_key, format!("0x{PK}"));
    let dbg = format!("{c:?} {} {:?}", c, c.api().unwrap());
    assert!(!dbg.contains(PK) && !dbg.contains("c2VjcmV0") && !dbg.contains("pp)"), "{dbg}");
    assert!(dbg.contains("l2=set"));
}

#[test]
fn rejects_bad_perms_and_values() {
    let d = tmp_dir("bad");
    let good = format!("POLY_PRIVATE_KEY=0x{PK}\nPOLY_FUNDER={FUNDER}\nPOLY_SIGNATURE_TYPE=1\n");
    let e = load_creds(&write(&d, &good, 0o640)).unwrap_err().to_string();
    assert!(e.contains("chmod 600"), "{e}");
    let c = load_creds(&write(&d, &good, 0o400)).unwrap();
    assert!(!c.has_l2());
    std::fs::set_permissions(&d, std::fs::Permissions::from_mode(0o777)).unwrap();
    let e = load_creds(&write(&d, &good, 0o600)).unwrap_err().to_string();
    assert!(e.contains("chmod 700"), "{e}");
    std::fs::set_permissions(&d, std::fs::Permissions::from_mode(0o700)).unwrap();
    let cases = [
        (good.replace("POLY_SIGNATURE_TYPE=1", "POLY_SIGNATURE_TYPE=4"), "0, 1, 2 or 3"),
        (good.replace(FUNDER, "0x1234"), "POLY_FUNDER"),
        (good.replace(PK, "abcd"), "32 bytes"),
        (format!("{good}POLY_API_KEY=x\n"), "all of"),
        (format!("{good}garbage\n"), "line 4"),
    ];
    for (text, needle) in cases {
        let e = load_creds(&write(&d, &text, 0o600)).unwrap_err().to_string();
        assert!(e.contains(needle), "{e} lacks {needle}");
    }
    let e = load_creds(&d.join("missing.env")).unwrap_err().to_string();
    assert!(e.contains("no credentials file"), "{e}");
    let e = load_creds(&d).unwrap_err().to_string();
    assert!(e.contains("not a regular file") || e.contains("mode"), "{e}");
    std::fs::remove_dir_all(&d).unwrap();
}
