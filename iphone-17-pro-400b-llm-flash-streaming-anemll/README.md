# The iPhone 17 Pro Is Running a 400B LLM

Code samples from the article: https://aistackinsights.ai/blog/iphone-17-pro-400b-llm-flash-streaming-anemll

## Overview

This folder contains the runnable code from our deep-dive on flash weight streaming —
the technique that lets an iPhone 17 Pro (12GB RAM) run a 400-billion-parameter
Mixture-of-Experts LLM by streaming expert weights on-demand from flash storage.

## Files

- `install.sh` — Install MLX and mlx-lm for Apple Silicon inference
- `flash_inference.py` — Stream token generation using MLX's lazy evaluation on large models
- `convert_to_ane.sh` — Convert a HuggingFace model to CoreML for Apple Neural Engine via ANEMLL

## Requirements

- Apple Silicon Mac (M1 or later; M3/M4/M5 recommended for larger models)
- macOS 14+, Python 3.11+, Homebrew

## Quick Start

```bash
# 1. Install dependencies
bash install.sh

# 2. Run streaming inference on a 72B model (needs ~40GB unified memory for 4-bit)
python flash_inference.py

# 3. Convert a small model to ANE CoreML format (macOS only)
bash convert_to_ane.sh
```

## Key Resources

- [ANEMLL GitHub](https://github.com/Anemll/Anemll) — ANE inference library
- [Apple Flash Inference Paper (ACL 2024)](https://arxiv.org/abs/2312.11514)
- [MLX Framework](https://github.com/ml-explore/mlx)
- [Hacker News Discussion](https://news.ycombinator.com/item?id=47490070) — technical breakdown
