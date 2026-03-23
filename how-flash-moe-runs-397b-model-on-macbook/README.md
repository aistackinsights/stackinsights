# How Flash-MoE Runs a 397B Parameter Model on a MacBook Pro

Code samples from the article: https://aistackinsights.ai/blog/how-flash-moe-runs-397b-model-on-macbook

## Overview

Flash-MoE is a pure C/Metal inference engine that runs Qwen3.5-397B-A17B (a 397 billion parameter Mixture-of-Experts model) on a MacBook Pro with 48GB RAM at 4.4+ tokens/second — streaming the full 209GB model from SSD on demand.

## Files

- `clone_and_build.sh` — Clone the Flash-MoE repo and build the Metal inference engine from source
- `inference_commands.sh` — Example commands for 4-bit, 2-bit, chat, and timing modes
- `fma_dequant_kernel.metal` — Annotated Metal compute shader illustrating the FMA-optimized 4-bit dequantization trick (the algebraic rearrangement that delivers a 12% GPU speedup)

## Requirements

- macOS 26+ (Darwin 25.2.0)
- Apple M3 Max with 48GB unified memory (M4 Max also works)
- ~210GB free SSD space (4-bit) or ~120GB (2-bit, but breaks tool calling)
- Xcode command-line tools

## Source Repository

All production code lives at: https://github.com/danveloper/flash-moe

## Key Benchmarks

| Configuration | tok/s | Notes |
|---|---|---|
| 4-bit + FMA kernel | 4.36 | Full tool calling, production quality |
| 4-bit baseline | 3.90 | Before FMA optimization |
| 2-bit OS cache | 5.74 | Breaks JSON output |
| 2-bit warm cache burst | 7.05 | Not sustained |

## Related Papers

- [Apple "LLM in a Flash" (arXiv:2312.11514)](https://arxiv.org/abs/2312.11514) — the foundational paper this work builds on
- [Flash-MoE Technical Paper](https://github.com/danveloper/flash-moe/blob/main/paper/flash_moe.pdf) — 90+ experiments documented
