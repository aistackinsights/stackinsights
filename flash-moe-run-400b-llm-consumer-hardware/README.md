# Flash-MoE: Run a 397B LLM on Consumer Hardware

Code samples from the article: https://aistackinsights.ai/blog/flash-moe-run-400b-llm-consumer-hardware

## What This Does

Demonstrates the Flash-MoE technique — streaming inactive Mixture-of-Experts weights from SSD storage — to run Alibaba's **Qwen3.5-397B-A17B** model (397 billion parameters) on Apple Silicon Macs and even an iPhone 17 Pro.

## Requirements

- macOS with Apple Silicon (M1/M2/M3/M4 — 128 GB unified memory recommended)
- Homebrew + CMake
- ~200 GB free disk space (for IQ4_KSS quantized model)
- Python 3.10+ with `httpx` (`pip install httpx`)

## Files

- `install.sh` — Clone and build llama.cpp with Metal GPU support
- `run_server.sh` — Launch the local inference server with SSD offload enabled
- `query_local_llm.py` — Query the running server via OpenAI-compatible API (supports both blocking and streaming modes)

## Quick Start

```bash
# 1. Build llama.cpp
chmod +x install.sh && ./install.sh

# 2. Download the model (194 GiB IQ4_KSS quant)
pip install huggingface_hub
huggingface-cli download ubergarm/Qwen3.5-397B-A17B-GGUF \
  --include "Qwen3.5-397B-A17B-IQ4_KSS*.gguf" \
  --local-dir ~/models/qwen35-397b

# 3. Start the server (Flash-MoE SSD offloading is automatic)
chmod +x run_server.sh && ./run_server.sh

# 4. Query it
python query_local_llm.py
```

## Expected Performance (M4 Max, 128 GB)

| Quant | Size | GPQA Diamond | Generation Speed |
|-------|------|-------------|-----------------|
| Q8_0 | 392 GiB | ~88% | ~20 t/s |
| IQ4_KSS | 194 GiB | ~87% | ~18 t/s |
| smol-IQ2_XS | 138 GiB | 82% | ~15 t/s |

## Key References

- [Qwen3.5-397B-A17B (Hugging Face)](https://huggingface.co/Qwen/Qwen3.5-397B-A17B)
- [ubergarm GGUF quants](https://huggingface.co/ubergarm/Qwen3.5-397B-A17B-GGUF)
- [llama.cpp Metal GDN kernel (PR #20361)](https://github.com/ggml-org/llama.cpp/pull/20361)
- [HN discussion: iPhone 17 Pro 400B demo](https://news.ycombinator.com/item?id=47490070)
- [HN discussion: MacBook Flash-MoE experiment](https://news.ycombinator.com/item?id=47476422)
