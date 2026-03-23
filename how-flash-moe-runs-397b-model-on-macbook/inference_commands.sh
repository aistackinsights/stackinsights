#!/bin/bash
# inference-commands.sh
# Example commands for running Flash-MoE inference
# Must be run from the flash-moe/metal_infer directory after building

# Standard 4-bit inference — production quality, 4.4+ tok/s
./infer --prompt "Explain quantum computing in simple terms" --tokens 200

# Interactive chat mode with full tool calling support
./chat

# Per-layer timing breakdown — useful for profiling and optimization
./infer --prompt "Hello" --tokens 20 --timing

# 2-bit mode — faster (~5.7 tok/s) but breaks JSON/tool calling
# Only use for non-structured text generation
./infer --prompt "Tell me a short story" --tokens 200 --2bit
