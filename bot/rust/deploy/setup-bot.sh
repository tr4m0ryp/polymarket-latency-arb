#!/usr/bin/env bash
# Run ON the Dublin box as root from an unpacked kit (after btclat/paper/deploy/setup.sh and
# btclat/trade/deploy/setup-trade.sh):  sudo bash rust/deploy/setup-bot.sh
# Installs the btclat-bot binary (dist/btclat-bot-aarch64, sha256-checked), the exported model
# JSONs and the fair-value weights, bot.env and the two systemd units. Starts NOTHING, reads no key.
set -euo pipefail
KIT="$(cd "$(dirname "$0")/../.." && pwd)"
APP=/opt/btclat
CFG=$APP/.config/btclat
BIN="$KIT/dist/btclat-bot-aarch64"
[ -f "$BIN" ] || { echo "no $BIN (build with rust/deploy/build.sh)"; exit 1; }
(cd "$KIT/dist" && sha256sum -c btclat-bot-aarch64.sha256)
mkdir -p "$APP/bin" "$APP/data/out/predict/models" "$APP/data/out/strategy" "$APP/data/trade" "$CFG/state"
install -m 755 "$BIN" "$APP/bin/btclat-bot"
cp "$KIT"/data/out/predict/models/*.trees.json "$KIT"/data/out/predict/models/*.trees.json.sha256 "$APP/data/out/predict/models/"
cp "$KIT/data/out/strategy/fair-pzm.json" "$APP/data/out/strategy/"
if [ ! -f "$CFG/bot.env" ]; then
  # default model: the hold-aware gate v1h_G_h250x_L0 (reports/veto-hold.md); caps: the CLI defaults
  # (reports/bankroll-caps.md); RESERVE: the untouchable part of the wallet (user rule 2026-10-14)
  sha=$(cat "$APP/data/out/predict/models/v1h_G_h250x_L0.trees.json.sha256")
  printf 'HOURS=1\nTAG=%s\nMODEL=v1h_G_h250x_L0\nMODEL_SHA256=%s\nRESERVE=43.04\nEXTRA=\n' "$(date -u +%Y%m%d)" "$sha" > "$CFG/bot.env"
fi
# untouchable wallet reserve (user rule 2026-10-14): the bot works with balance - RESERVE only
grep -q '^RESERVE=' "$CFG/bot.env" || echo 'RESERVE=43.04' >> "$CFG/bot.env"
grep -q '^MODEL=v1h_G_h250x_L0$' "$CFG/bot.env" || echo "note: $CFG/bot.env keeps MODEL=$(grep '^MODEL=' "$CFG/bot.env" | cut -d= -f2); the default is v1h_G_h250x_L0 (MODEL_SHA256=$(cat "$APP/data/out/predict/models/v1h_G_h250x_L0.trees.json.sha256"))"
chown -R btclat:btclat "$APP/bin" "$APP/data" "$APP/.config"
chmod 700 "$APP/.config" "$CFG" "$CFG/state"
sudo -u btclat "$APP/bin/btclat-bot" --version
chronyc tracking | grep -E "System time|Reference" || true
install -m 644 "$KIT/rust/deploy/btclat-bot-dry.service" /etc/systemd/system/
install -m 644 "$KIT/rust/deploy/btclat-bot-live.service" /etc/systemd/system/
systemctl daemon-reload
cat <<TXT
Installed, NOT started. Edit $CFG/bot.env (HOURS, TAG, MODEL, MODEL_SHA256, RESERVE, EXTRA), then:
  dry  : sudo systemctl start btclat-bot-dry
  live : (user approval) sudo systemctl start btclat-bot-live
Kill: sudo -u btclat touch $CFG/KILL
TXT
