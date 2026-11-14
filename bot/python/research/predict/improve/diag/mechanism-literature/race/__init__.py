"""Second pass of the phenomenon study: the race on a stale Polymarket quote, split by cause.

- sidecheck: are the feed's trade-direction labels right? (Dubach 2026 finds feed-inferred
  direction agrees with on-chain fills on only ~59% of buckets.) Checked against the venue
  book a grid step before each print;
- deciles: Binance-move -> Polymarket requote lag by activity decile, stratified by the stale
  level's size, split into maker cancels vs trade consumption (competing risks), the rival
  takers' excess hazard over matched quiet instants, and the hold-as-last-look selection."""
