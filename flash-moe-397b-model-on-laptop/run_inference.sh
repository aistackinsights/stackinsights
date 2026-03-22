#!/usr/bin/env bash
# run_inference.sh — Flash-MoE inference examples
# Source: https://aistackinsights.ai/blog/flash-moe-397b-model-on-laptop
#
# Run from inside: flash-moe/metal_infer/
# Ensure model weights are extracted (see download_weights.sh)

set -euo pipefail

PROMPT="${1:-Explain the Mixture-of-Experts architecture in plain English}"
TOKENS="${2:-200}"

echo "===== Flash-MoE Inference Examples ====="
echo ""

# -------------------------------------------------
# 1. Standard 4-bit inference (recommended)
#    4.36 tok/s, full tool calling, production quality
# -------------------------------------------------
echo "[1] 4-bit inference (production quality, full tool calling)"
echo "    Usage: ./infer --prompt \"...\" --tokens N"
echo ""
./infer --prompt "${PROMPT}" --tokens "${TOKENS}"

echo ""
echo "---"
echo ""

# -------------------------------------------------
# 2. Per-layer timing breakdown
#    Use this to understand where time is spent
# -------------------------------------------------
echo "[2] Per-layer timing (diagnostic)"
./infer --prompt "Hello" --tokens 20 --timing

echo ""
echo "---"
echo ""

# -------------------------------------------------
# 3. Interactive chat with tool calling
#    Supports JSON function calling natively
# -------------------------------------------------
echo "[3] Interactive chat (Ctrl+C to exit)"
echo "    ./chat"
echo "    (skipping in script mode — run manually)"

echo ""
echo "---"
echo ""

# -------------------------------------------------
# 4. 2-bit inference (faster but BREAKS tool calling)
#    5.74 tok/s, 120GB disk, JSON quoting corrupted
# -------------------------------------------------
echo "[4] 2-bit inference (faster; do NOT use for tool calling)"
echo "    ./infer --prompt \"...\" --tokens N --2bit"
echo "    WARNING: produces \\name\\ instead of \"name\" in JSON output"
