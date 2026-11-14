#!/usr/bin/env bash
# Run ON the Dublin instance (already set up by btclat/paper/deploy/setup.sh) as root, from an
# unpacked kit that contains btclat/trade:  sudo bash btclat/trade/deploy/setup-trade.sh
# Installs the live-test package, its pinned client libs into the existing venv, the config
# directory and the systemd unit template. Starts NOTHING, places no order, reads no key.
# Leaves the running paper bot (btclat-paper@*) alone.
set -euo pipefail
KIT="$(cd "$(dirname "$0")/../../.." && pwd)"
APP=/opt/btclat
CFG=$APP/.config/btclat
[ -x "$APP/.venv/bin/python" ] || { echo "paper kit not installed in $APP (run btclat/paper/deploy/setup.sh first)"; exit 1; }

mkdir -p "$APP/btclat/trade" "$APP/data/trade" "$CFG/state"
cp -a "$KIT/btclat/trade/." "$APP/btclat/trade/"
"$APP/.venv/bin/pip" install -q -r "$APP/btclat/trade/deploy/requirements.txt"
[ -f "$CFG/run.env" ] || printf 'HOURS=1\nTAG=%s\n' "$(date -u +%Y%m%d)" > "$CFG/run.env"
chown -R btclat:btclat "$APP/btclat/trade" "$APP/data/trade" "$APP/.config"
chmod 700 "$APP/.config" "$CFG" "$CFG/state"

# Smoke checks, offline: signing backend and cost with a throwaway in-memory key (never sent),
# no signing library pulled in at import, and what the geoblock endpoint says about this IP.
cd "$APP"
sudo -u btclat .venv/bin/python - <<'PY'
import sys, time
import btclat.trade.__main__  # noqa: F401
assert not [m for m in sys.modules if m.startswith(("py_clob_client", "eth_account"))], "signing lib loaded at import"
from eth_account import Account
from btclat.trade.gate.creds import Creds
from btclat.trade.venue.signer import LibSigner
a = Account.create()
s = LibSigner(Creds("0x" + a.key.hex().removeprefix("0x"), a.address, 0))
x = [s.order("1" * 77, 0.5, 5.0, "BUY", "FAK", False, "k").sign_us for _ in range(50)]
print("sign backend", s.backend, "p50 us", sorted(x)[25])
PY
curl -s -m 10 https://polymarket.com/api/geoblock; echo

install -m 644 "$APP/btclat/trade/deploy/btclat-trade@.service" /etc/systemd/system/btclat-trade@.service
systemctl daemon-reload
cat <<TXT
Installed, NOT started. Before any start (user approval required):
  1. sudo -u btclat install -m 600 /dev/stdin $CFG/polymarket.env   (paste the credentials, Ctrl-D)
  2. edit $CFG/run.env (HOURS, TAG)
  3. sudo systemctl start btclat-trade@probe      ; journalctl -fu btclat-trade@probe
  4. after the probe report: sudo systemctl start btclat-trade@micro
Kill: sudo -u btclat touch $CFG/KILL   (remove it to allow the next start)
TXT
