#!/usr/bin/env bash
# install.sh — Build llama.cpp with Metal backend for Qwen3.5-397B Flash-MoE
# Requires: macOS with Apple Silicon (M1/M2/M3/M4), Homebrew, CMake
# Article: https://aistackinsights.ai/blog/flash-moe-run-400b-llm-consumer-hardware

set -euo pipefail

echo "Installing dependencies..."
brew install cmake

echo "Cloning llama.cpp..."
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp

echo "Building with Metal support..."
cmake -B build -DGGML_METAL=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j "$(sysctl -n hw.logicalcpu)"

echo "Build complete. Binaries in: $(pwd)/build/bin/"
echo ""
echo "Next: download a GGUF quant and run run_server.sh"
