# TurboQuant KV Cache Compression — Zero Accuracy Loss

Code from the article: https://aistackinsights.ai/blog/turboquant-kv-cache-compression-zero-accuracy-loss

## What this is
A working implementation of TurboQuant's three-layer KV cache compression:
1. **KVCacheRotator** — random orthogonal rotation for uniform distribution
2. **PolarQuant** — polar coordinate quantization, zero normalization overhead
3. **QJLErrorCorrector** — 1-bit Johnson-Lindenstrauss bias correction

## Files
- `turboquant_kv_cache.py` — complete implementation + demo

## Papers
- TurboQuant: https://arxiv.org/abs/2504.19874 (ICLR 2026)
- PolarQuant: https://arxiv.org/abs/2502.02617 (AISTATS 2026)
- QJL: https://dl.acm.org/doi/10.1609/aaai.v39i24.34773 (AAAI 2025)

## Usage
```bash
pip install torch
python turboquant_kv_cache.py
```
