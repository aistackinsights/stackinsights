# Flash-MoE: Running a 397B AI Model on a MacBook Pro

Code samples from the article: https://aistackinsights.ai/blog/flash-moe-397b-model-on-laptop

## Overview

[Flash-MoE](https://github.com/danveloper/flash-moe) is a pure C/Metal inference engine that
runs the Qwen3.5-397B-A17B (397 billion parameter Mixture-of-Experts) model on a MacBook Pro
with 48GB RAM at 4.4+ tokens/second with full tool calling support.

It achieves this by streaming expert weights (209GB at 4-bit) from NVMe SSD on demand,
inspired by Apple's [LLM in a Flash](https://arxiv.org/abs/2312.11514) research paper.

## Requirements

- Apple Silicon Mac: M3 Max or M4 (Max/Ultra)
- 48GB+ unified memory
- ~220GB free SSD space
- macOS 15+ (Sequoia/Tahoe)
- Xcode Command Line Tools

## Files

- `build.sh` — Clone and build the Flash-MoE inference engine from source
- `download_weights.sh` — Download Qwen3.5-397B-A17B weights and convert to Flash-MoE format
- `run_inference.sh` — Inference examples: 4-bit (production), 2-bit (fast), timing breakdown
- `llama_cpp_alternative.sh` — Alternative llama.cpp route using GGUF quantizations

## Quick Start

```bash
# 1. Build
bash build.sh

# 2. Download weights (~220GB — takes time!)
bash download_weights.sh

# 3. Run inference
cd flash-moe/metal_infer
./infer --prompt "Your prompt here" --tokens 200

# Or interactive chat with tool calling:
./chat
```

## Performance

| Config | tok/s | Size | Tool Calling |
|---|---|---|---|
| 4-bit FMA (recommended) | 4.36 | 209GB | ✅ |
| 2-bit (fast) | 5.74 | 120GB | ❌ |
| llama.cpp Q8_0 | ~20 | 113GB (in RAM) | ✅ |

## References

- [Flash-MoE GitHub](https://github.com/danveloper/flash-moe)
- [Qwen3.5-397B-A17B on Hugging Face](https://huggingface.co/Qwen/Qwen3.5-397B-A17B)
- [Apple LLM in a Flash paper](https://arxiv.org/abs/2312.11514)
- [llama.cpp GDN Metal kernel (PR #20361)](https://github.com/ggml-org/llama.cpp/pull/20361)
