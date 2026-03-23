#!/usr/bin/env bash
# run_server.sh — Launch Qwen3.5-397B with SSD-offload (Flash-MoE) enabled
# Requires: llama.cpp built with Metal, IQ4_KSS GGUF downloaded
# Article: https://aistackinsights.ai/blog/flash-moe-run-400b-llm-consumer-hardware
#
# Download model first:
#   pip install huggingface_hub
#   huggingface-cli download ubergarm/Qwen3.5-397B-A17B-GGUF \
#     --include "Qwen3.5-397B-A17B-IQ4_KSS*.gguf" \
#     --local-dir ~/models/qwen35-397b

set -euo pipefail

MODEL_PATH="${MODEL_PATH:-$HOME/models/qwen35-397b/Qwen3.5-397B-A17B-IQ4_KSS-00001-of-00004.gguf}"
LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$HOME/llama.cpp}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8080}"
CTX_SIZE="${CTX_SIZE:-32768}"

if [[ ! -f "$MODEL_PATH" ]]; then
  echo "ERROR: Model not found at $MODEL_PATH"
  echo "Set MODEL_PATH env var or download the GGUF first."
  exit 1
fi

echo "Starting Qwen3.5-397B server..."
echo "  Model:    $MODEL_PATH"
echo "  Context:  $CTX_SIZE tokens"
echo "  Endpoint: http://$HOST:$PORT/v1"
echo ""
echo "Flash-MoE: inactive experts will be streamed from SSD via OS page cache."
echo "Best performance on Apple Silicon with NVMe storage."
echo ""

"$LLAMA_CPP_DIR/build/bin/llama-server" \
  -m "$MODEL_PATH" \
  --n-gpu-layers 99 \
  --flash-attn \
  --ctx-size "$CTX_SIZE" \
  --threads 1 \
  --batch-size 2048 \
  --ubatch-size 2048 \
  --host "$HOST" \
  --port "$PORT"
