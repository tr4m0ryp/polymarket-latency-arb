use btl_bot::live::exec::order::min_notional_size;

#[test]
fn five_shares_when_notional_reaches_one_dollar() {
    assert_eq!(min_notional_size(5.0, 0.20), 5.0);
    assert_eq!(min_notional_size(5.0, 0.55), 5.0);
}

#[test]
fn cheap_asks_get_just_enough_shares_for_one_dollar() {
    assert_eq!(min_notional_size(5.0, 0.05), 21.0); // 21 x 0.05 = $1.05
    assert_eq!(min_notional_size(5.0, 0.15), 7.0);  // 7 x 0.15 = $1.05
    assert!(min_notional_size(5.0, 0.11) * 0.11 >= 1.0);
}

#[test]
fn reserve_flag_reaches_the_bankroll() {
    use clap::Parser;
    #[derive(Parser)]
    struct T {
        #[command(flatten)]
        a: btl_bot::cli::RunArgs,
    }
    let b = T::parse_from(["t", "--dry", "--reserve", "43.04"]).a.bankroll().unwrap();
    assert_eq!(b.reserve, 43.04);
    assert_eq!(T::parse_from(["t", "--dry"]).a.bankroll().unwrap().reserve, 0.0);
    assert!(T::parse_from(["t", "--dry", "--reserve=-1"]).a.bankroll().is_err());
}
