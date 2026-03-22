#!/usr/bin/env bash
# build.sh — Build the Flash-MoE inference engine
# Source: https://aistackinsights.ai/blog/flash-moe-397b-model-on-laptop
#
# Requirements:
#   - macOS 15+ (Sequoia/Tahoe) with Apple Silicon (M3 Max / M4 Max/Ultra)
#   - 48GB+ unified memory
#   - ~220GB free SSD space
#   - Xcode Command Line Tools: xcode-select --install

set -euo pipefail

echo "==> Cloning Flash-MoE..."
git clone https://github.com/danveloper/flash-moe
cd flash-moe/metal_infer

echo "==> Building inference engine..."
make

echo ""
echo "Build complete. Binaries:"
echo "  ./infer  — scripted inference + benchmarks"
echo "  ./chat   — interactive TUI with tool calling"
echo ""
echo "Next step: download model weights (see download_weights.sh)"
