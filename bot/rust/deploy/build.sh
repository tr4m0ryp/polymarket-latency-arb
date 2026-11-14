#!/usr/bin/env bash
# Build btclat-bot for the Dublin box (c7g.large Graviton3, aarch64, Ubuntu 24.04, glibc 2.39).
#   bash rust/deploy/build.sh            # on the box (native) or cross from x86_64 via cargo-zigbuild
# Output: dist/btclat-bot-aarch64 (+ .sha256). Cross needs: rustup target add aarch64-unknown-linux-gnu,
# cargo install cargo-zigbuild, pip install ziglang (zig provides the aarch64 C toolchain ring needs).
set -euo pipefail
cd "$(dirname "$0")/.."
export RUSTFLAGS="${RUSTFLAGS:--C target-cpu=neoverse-v1}"   # Graviton3; unset for a generic build
out=../dist
mkdir -p "$out"
if [ "$(uname -m)" = "aarch64" ]; then
  cargo build --release -p btl_bot
  bin=target/release/btclat-bot
else
  command -v cargo-zigbuild >/dev/null || { echo "need cargo-zigbuild (cargo install cargo-zigbuild) + zig"; exit 1; }
  cargo zigbuild --release -p btl_bot --target aarch64-unknown-linux-gnu.2.35
  bin=target/aarch64-unknown-linux-gnu/release/btclat-bot
fi
cp "$bin" "$out/btclat-bot-aarch64"
(cd "$out" && sha256sum btclat-bot-aarch64 > btclat-bot-aarch64.sha256 && cat btclat-bot-aarch64.sha256)
file "$out/btclat-bot-aarch64" 2>/dev/null || true
