#!/bin/bash
# convert_to_ane.sh
# Convert a HuggingFace model to CoreML format for Apple Neural Engine (ANE) inference.
# Uses the ANEMLL open-source conversion pipeline (https://github.com/Anemll/Anemll).
#
# Requirements: macOS 14+, Python 3.11+, Homebrew

set -e

# Clone ANEMLL if not already present
if [ ! -d "./Anemll" ]; then
    git clone https://github.com/Anemll/Anemll && cd Anemll
else
    cd Anemll
fi

# Set up the Python environment using uv (fast installs)
brew install uv
./create_uv_env.sh
source env-anemll/bin/activate
./install_dependencies.sh

# Convert Qwen3 0.6B — small model, good for testing the pipeline end-to-end
# Replace with any supported architecture: LLaMA, Qwen, Gemma 3
./anemll/utils/convert_model.sh \
    --model Qwen/Qwen3-0.6B-Instruct \
    --output ./output/qwen3-0.6b-ane \
    --context 512

# Optionally run weight deduplication to cut file size by ~50%
# python anemll/utils/anemll_dedup.py --model ./output/qwen3-0.6b-ane

# Run the interactive chat CLI against the converted CoreML model
python anemll/utils/chat.py --model ./output/qwen3-0.6b-ane
