#!/usr/bin/env bash
# Pull a feed-race run back: recorder/feedrace/fetch.sh <host> <key> <label>
set -euo pipefail
HOST=$1; KEY=$2; LABEL=$3
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p "$ROOT/data/cache/feedrace/$LABEL"
rsync -a -e "ssh -i $KEY" "$HOST:feedrace/data/$LABEL/" "$ROOT/data/cache/feedrace/$LABEL/"
du -sh "$ROOT/data/cache/feedrace/$LABEL"
