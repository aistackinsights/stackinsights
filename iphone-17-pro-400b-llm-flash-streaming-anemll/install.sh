#!/bin/bash
# install.sh
# Install MLX and the mlx-lm convenience layer for Apple Silicon inference

pip install mlx mlx-lm

# Verify your hardware — should print Device(gpu, 0) on Apple Silicon
python -c "import mlx.core as mx; print('Device:', mx.default_device())"
