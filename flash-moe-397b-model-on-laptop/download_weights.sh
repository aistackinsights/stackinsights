#!/usr/bin/env bash
# download_weights.sh — Download and prepare Qwen3.5-397B-A17B for Flash-MoE
# Source: https://aistackinsights.ai/blog/flash-moe-397b-model-on-laptop
#
# WARNING: This downloads ~220GB of model data. Ensure you have enough disk space.
# The download requires a Hugging Face account (free). Log in with:
#   huggingface-cli login

set -euo pipefail

MODEL_ID="Qwen/Qwen3.5-397B-A17B"
LOCAL_DIR="./qwen35-weights"

echo "==> Installing Hugging Face CLI..."
pip install --quiet huggingface_hub

echo ""
echo "==> Downloading ${MODEL_ID} (~220GB) to ${LOCAL_DIR}/"
echo "    This will take a while on most connections..."
echo ""
huggingface-cli download "${MODEL_ID}" --local-dir "${LOCAL_DIR}"

echo ""
echo "==> Extracting non-expert weights → model_weights.bin (~5.5GB)..."
# Must be run from inside flash-moe/metal_infer/
python extract_weights.py

echo ""
echo "==> Packing 4-bit expert weights → packed_experts/ (~209GB)..."
echo "    This step takes ~20 minutes on a fast machine..."
python repack_experts.py

echo ""
echo "Done! You can now run inference:"
echo "  ./infer --prompt 'Your prompt here' --tokens 200"
echo "  ./chat   (interactive mode with tool calling)"
