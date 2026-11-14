#!/usr/bin/env bash
# Kit for the Dublin box: the aarch64 binary (+ sha256), these deploy files, the exported model
# JSONs (+ sha256) and the fair-value weights.   bash rust/deploy/package.sh  ->  dist/btclat-bot-kit.tgz
set -euo pipefail
cd "$(dirname "$0")/../.."
[ -f dist/btclat-bot-aarch64 ] || bash rust/deploy/build.sh
tar czf dist/btclat-bot-kit.tgz dist/btclat-bot-aarch64 dist/btclat-bot-aarch64.sha256 rust/deploy \
  data/out/predict/models/*.trees.json data/out/predict/models/*.trees.json.sha256 data/out/strategy/fair-pzm.json
ls -la dist/btclat-bot-kit.tgz
