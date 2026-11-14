#!/usr/bin/env bash
# One command per box: copy the recorder to ~/feedrace on HOST, build its own venv, start it
# detached. Touches nothing outside ~/feedrace (never /opt/btclat or the btclat services).
#   recorder/feedrace/deploy.sh ubuntu@<HOST> ~/.config/btclat/btclat-dublin.pem 2 dublin
# Later:  recorder/feedrace/fetch.sh <host> <key> <label>  ->  data/cache/feedrace/<label>/
#         python3 recorder/feedrace/analysis/run.py data/cache/feedrace/<label>
set -euo pipefail
HOST=$1; KEY=$2; HOURS=${3:-2}; LABEL=${4:-run}-$(date -u +%Y%m%dT%H%M)
HERE=$(cd "$(dirname "$0")" && pwd)
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$HOST")
"${SSH[@]}" 'mkdir -p ~/feedrace/code ~/feedrace/data'
scp -q -i "$KEY" "$HERE"/{streams,sink,record,pm}.py "$HOST":feedrace/code/
"${SSH[@]}" bash -s <<REMOTE
set -e
cd ~/feedrace
if [ ! -x venv/bin/python ]; then
  python3 -m venv venv || { sudo apt-get -qq update && sudo apt-get -qq install -y python3-venv && python3 -m venv venv; }
  venv/bin/pip -q install 'websockets>=14,<16'
fi
setsid nohup venv/bin/python code/record.py --hours $HOURS --out data/$LABEL \
  > data/$LABEL.log 2>&1 < /dev/null &
sleep 8; ls -la data/$LABEL; tail -n 30 data/$LABEL/events-*.jsonl
REMOTE
echo "label: $LABEL"
