"""Small-money live test of the paper bot's strategy on the real Polymarket CLOB.

Reuses btclat.paper's feeds, features, frozen model and arms (imported, never copied) and adds
an execution layer: official py-clob-client-v2 signing (venue/signer.py, imported only when a
live session starts), one warm HTTP/2 session (venue/http.py), hard risk caps (risk/), a kill
file and cancel-all on exit (risk/session.py), and two modes:

- probe: post-only BUY 5 sh at 0.01, >= 5 ticks under the best bid, cancelled at once (zero
  fill risk); measures signing, POST ack, cancel, errors, rate limits, warm vs idle session;
- micro: real FAK taker orders of exactly 5 shares on vt_v1_m0.03_any (and optionally the veto
  arm), logged next to the paper engine's prediction for the same signal.

Nothing starts without --i-approve, ~/.config/btclat/polymarket.env (chmod 600), an unlocked
UTC day and a non-geoblocked IP (gate/). The paper bot's guard is untouched: this package
lives outside btclat/paper and the paper process never imports it.

    python3 -m btclat.trade probe --i-approve --n 20
    python3 -m btclat.trade micro --i-approve --hours 4
    python3 -m btclat.trade.report --run <run>"""
from .risk.book import Intent, RiskBook
from .risk.limits import Limits
from .risk.session import Session, Stop

__all__ = ["Intent", "Limits", "RiskBook", "Session", "Stop"]
