#!/bin/bash
# clone-and-build.sh
# Clone Flash-MoE and build the Metal inference engine
# Requires: macOS 26+, Xcode CLI tools, M3 Max with 48GB RAM, ~210GB free SSD

set -e

echo "==> Cloning Flash-MoE repository..."
git clone https://github.com/danveloper/flash-moe.git
cd flash-moe/metal_infer

echo "==> Building with Metal support..."
make

echo "==> Build complete. Binaries:"
ls -lh infer chat

echo ""
echo "==> Next steps:"
echo "  1. Download Qwen3.5-397B-A17B from HuggingFace (~397GB safetensors)"
echo "  2. Run: python extract_weights.py --model-dir /path/to/weights --output-dir /path/to/output"
echo "  3. Run: ./infer --prompt 'Hello, world' --tokens 50"
