#!/usr/bin/env bash
# llama_cpp_alternative.sh — Run Qwen3.5-397B-A17B via llama.cpp (GGUF)
# Source: https://aistackinsights.ai/blog/flash-moe-397b-model-on-laptop
#
# Alternative to Flash-MoE using the llama.cpp ecosystem.
# Requires the full Q8_0 model to fit in RAM (~113GB needed).
# Includes the GDN Metal kernel from PR #20361 (merged Mar 11 2026)
# for +25% throughput on Apple Silicon.
#
# Requirements:
#   - llama.cpp built from source (post Mar 11 2026 for GDN kernel)
#   - ~113GB GGUF file (Q8_0) or ~100GB (IQ2_XS ~2.46 BPW)

set -euo pipefail

LLAMA_CLI="${LLAMA_CLI:-llama-cli}"
MODEL="${MODEL:-./Qwen3.5-397B-A17B-Q8_0.gguf}"
PROMPT="${1:-Explain quantum entanglement in one paragraph}"
TOKENS="${2:-200}"

echo "==> Downloading Q8_0 GGUF (113GB) via Hugging Face CLI"
echo "    (skip if already downloaded)"
# huggingface-cli download ubergarm/Qwen3.5-397B-A17B-GGUF \
#     --include "*.gguf" --local-dir ./

echo ""
echo "==> Running llama.cpp inference"
echo "    Model:  ${MODEL}"
echo "    Prompt: ${PROMPT}"
echo "    Tokens: ${TOKENS}"
echo ""

# -fa 1       = enable flash attention
# -ngl 99     = offload all layers to Metal GPU
# -b 2048     = batch size
# -ub 2048    = micro-batch size
"${LLAMA_CLI}" \
    -m "${MODEL}" \
    -fa 1 \
    -ngl 99 \
    -b 2048 -ub 2048 \
    -p "${PROMPT}" \
    -n "${TOKENS}"

echo ""
echo "Benchmark with llama-bench:"
echo "  llama-bench -m ${MODEL} -fa 1 -t 1 -ngl 99 -b 2048 -ub 2048"
echo ""
echo "Expected performance (M3 Max, Q8_0, empty context):"
echo "  pp512 (prompt processing): ~190 tok/s"
echo "  tg128 (text generation):   ~20 tok/s"
echo "  (degrades to ~40 pp / ~8 tg at 250k context)"
