#!/usr/bin/env bash
# Run ON the instance (Ubuntu 24.04 arm64, t4g.small, eu-west-1) as root, from the unpacked
# kit: sudo bash btclat/paper/deploy/setup.sh [run-tag]. Installs chrony on the Amazon Time
# Sync Service, a venv with the pinned packages, the systemd unit, and starts a 48 h run.
# Touches no AWS API and no credentials; the bot itself sends nothing (btclat/paper/guard.py).
set -euo pipefail
TAG="${1:-$(date -u +%Y%m%d)}"
KIT="$(cd "$(dirname "$0")/../../.." && pwd)"

apt-get update -q
apt-get install -y -q python3-venv python3-dev gcc chrony
install -m 644 "$KIT/btclat/paper/deploy/chrony.conf" /etc/chrony/chrony.conf
systemctl restart chrony
chronyc -a waitsync 30 0.01 || true
chronyc tracking

id btclat >/dev/null 2>&1 || useradd --system --home /opt/btclat --shell /usr/sbin/nologin btclat
mkdir -p /opt/btclat
cp -a "$KIT"/. /opt/btclat/
mkdir -p /opt/btclat/data/paper
python3 -m venv /opt/btclat/.venv
/opt/btclat/.venv/bin/pip install -q --upgrade pip
/opt/btclat/.venv/bin/pip install -q -r /opt/btclat/btclat/paper/deploy/requirements.txt
chown -R btclat:btclat /opt/btclat

# Smoke checks: model hashes, no order path, C scorer compiles.
cd /opt/btclat
sudo -u btclat .venv/bin/python - <<'PY'
from btclat.paper import guard; guard.install()
from btclat.paper.model.load import ValueModel
m = ValueModel("v1_L0"); print("model", m.name, m.sha16, "tree compile s", round(m.compile_s, 2))
PY

install -m 644 btclat/paper/deploy/btclat-paper.service /etc/systemd/system/btclat-paper@.service
systemctl daemon-reload
systemctl enable --now "btclat-paper@${TAG}.service"
systemctl status --no-pager "btclat-paper@${TAG}.service" | head -5
echo "logs: /opt/btclat/data/paper/dublin-${TAG}/  (journalctl -u btclat-paper@${TAG})"
