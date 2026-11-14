//! Sign time per order (amounts + EIP-712 + secp256k1 + JSON), test key only.
//!     cargo run --release -p btl_venue --example sign_bench

use btl_venue::{Creds, OrderSpec, OrderType, Side, Signer};

fn main() -> anyhow::Result<()> {
    let pk = "0x4c0883a69102937d6231471b5dbb6204fe5129617082792ae468d01a3f362318";
    let token = "71321045679252212594626385532706912750332728571942532289631379312455583992563";
    for st in [0u8, 3] {
        let s = Signer::new(&Creds::new(pk, "0x6E0C80c90ea6C15917308F820Eac91Ce2724B5b5", st, None)?)?;
        let n = 20_000u64;
        let (mut sign, mut build, mut all) = (Vec::new(), Vec::new(), 0u64);
        for i in 0..n {
            let spec = OrderSpec { token_id: token.into(), price: 0.01 + (i % 99) as f64 / 100.0, size: 5.0 + (i % 7) as f64,
                                   side: if i % 2 == 0 { Side::Buy } else { Side::Sell }, order_type: OrderType::Fak,
                                   post_only: false, expiration: 0 };
            let t = btl_venue::mono_ns();
            let o = s.sign(&spec, "owner", btl_venue::new_salt(), 1_760_000_000_000 + i)?;
            all += btl_venue::mono_ns() - t;
            sign.push(o.sign_ns);
            build.push(o.build_ns);
        }
        sign.sort_unstable();
        build.sort_unstable();
        let q = |v: &Vec<u64>, p: f64| v[((v.len() - 1) as f64 * p) as usize] as f64 / 1e3;
        println!("sig_type {st}: sign_ns p50 {:.1} us p99 {:.1} us | build_ns p50 {:.1} us p99 {:.1} us | mean call {:.1} us",
                 q(&sign, 0.5), q(&sign, 0.99), q(&build, 0.5), q(&build, 0.99), all as f64 / n as f64 / 1e3);
    }
    Ok(())
}
