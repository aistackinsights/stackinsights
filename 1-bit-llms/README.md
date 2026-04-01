# 1-Bit LLMs — Companion Scripts

Companion scripts for the article **[Running 1-Bit LLMs: Bonsai & BitNet On-Device AI Guide](https://aistackinsights.ai/blog/1-bit-llms-bonsai-bitnet-on-device-ai-guide)** on AI Stack Insights.

These tools let you run Microsoft's Bonsai 1-bit quantized models locally — from a Raspberry Pi to a gaming laptop — and benchmark them against cloud APIs.

---

## What's in This Folder

| File | What it does |
|------|-------------|
| `bonsai_inference.py` | Python wrapper for BitNet.cpp/llama.cpp — generation, classification, JSON extraction, benchmarking |
| `benchmark_vs_cloud.py` | Latency + cost comparison: local Bonsai vs. Anthropic claude-haiku-3 |
| `edge_deploy_rpi.sh` | Full Raspberry Pi 5 deployment: build, download, HTTP server, systemd service |
| `README.md` | This file |

---

## Hardware Requirements

| Model | Size (Q8) | Min RAM | Recommended Hardware |
|-------|-----------|---------|----------------------|
| Bonsai 400M | ~450 MB | 512 MB | Raspberry Pi 4, old phones, microcontrollers |
| Bonsai 1.7B | ~1.8 GB | 2 GB | Raspberry Pi 5, Jetson Nano, low-power NUC |
| Bonsai 3B | ~3.2 GB | 4 GB | Laptop, Jetson Orin, Mac mini |
| Bonsai 7B | ~7.5 GB | 8 GB | Desktop CPU, high-end laptop, gaming PC |

> **RAM rule of thumb:** You need ~1.2× the model size in free RAM for smooth inference. Swap works but is very slow on SD cards.

---

## Quick Install

### Python dependencies
```bash
pip install anthropic huggingface_hub psutil
```

### BitNet.cpp (for `bonsai_inference.py` and `benchmark_vs_cloud.py`)
```bash
# On Linux / macOS / WSL
git clone --depth 1 https://github.com/microsoft/BitNet.git
cd BitNet
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS
make -j$(nproc)
# Binary: BitNet/build/bin/llama-cli
```

### Download a model
```bash
huggingface-cli download microsoft/Bonsai-1.7B-GGUF Bonsai-1.7B-Q8_0.gguf \
    --local-dir ~/models --local-dir-use-symlinks False
```

---

## Usage

### `bonsai_inference.py` — Inference wrapper + benchmark

```bash
# Basic demo (generation, classification, JSON extraction, benchmark)
python bonsai_inference.py \
    --model ~/models/Bonsai-1.7B-Q8_0.gguf \
    --binary ~/BitNet/build/bin/llama-cli \
    --threads 4

# Verbose output (shows subprocess commands)
python bonsai_inference.py --model ~/models/Bonsai-1.7B-Q8_0.gguf --verbose
```

**Use in your own code:**
```python
from bonsai_inference import BitNetInference

llm = BitNetInference(binary_path="~/BitNet/build/bin/llama-cli")
llm.load_model("~/models/Bonsai-1.7B-Q8_0.gguf")

# Generate text
reply = llm.generate("Explain 1-bit quantization in one sentence.", max_tokens=80)

# Zero-shot classification
result = llm.classify("Server is down again", labels=["bug", "feature", "docs"])
print(result["label"])   # → "bug"

# Structured extraction
data = llm.extract_json(
    "Contact Alice at alice@corp.com",
    schema={"name": "full name", "email": "email address"}
)
print(data)  # → {"name": "Alice", "email": "alice@corp.com"}
```

---

### `benchmark_vs_cloud.py` — Local vs. cloud cost comparison

```bash
# Full benchmark (set ANTHROPIC_API_KEY first)
export ANTHROPIC_API_KEY=sk-ant-...
python benchmark_vs_cloud.py --model ~/models/Bonsai-1.7B-Q8_0.gguf

# Local only — no API key needed
python benchmark_vs_cloud.py --model ~/models/Bonsai-1.7B-Q8_0.gguf --local-only

# Custom thread count (RPi 5 = 4 cores)
python benchmark_vs_cloud.py --model ~/models/Bonsai-1.7B-Q8_0.gguf \
    --threads 4 --max-tokens 64 --local-only
```

**Example output:**
```
══════════════════════════════════════════════════════════════════════════
  SUMMARY — Local Bonsai  vs.  Cloud (claude-haiku-3)
══════════════════════════════════════════════════════════════════════════
  Metric                          Local Bonsai          Cloud API
  ──────────────────────────────────────────────────────────────────
  Avg latency / request              2.3400s             0.8200s
  Avg tokens / second              38.5 tok/s          62.1 tok/s
  Total cost (10 prompts)          $0.000001           $0.000847
  Effective $/1M output tokens       $0.0005            $1.2500
  Requires internet                       No                 Yes
  Data leaves device                      No                 Yes
══════════════════════════════════════════════════════════════════════════
```

---

### `edge_deploy_rpi.sh` — Full Raspberry Pi 5 setup

```bash
# Run on your Raspberry Pi 5 (Raspberry Pi OS Bookworm 64-bit recommended)
chmod +x edge_deploy_rpi.sh
./edge_deploy_rpi.sh
```

After the script completes, your inference server is running at `http://localhost:8080`:

```bash
# Generate text
curl -s -X POST http://localhost:8080/generate \
     -H 'Content-Type: application/json' \
     -d '{"prompt": "What is edge AI?", "max_tokens": 100}' | python3 -m json.tool

# Health check
curl http://localhost:8080/health
```

**Service management:**
```bash
sudo systemctl status  bonsai-inference
sudo systemctl restart bonsai-inference
sudo journalctl -u bonsai-inference -f   # live logs
```

---

## Model Selection Guide

Choose the right Bonsai model for your task and hardware:

| Task Type | Recommended Model | Why |
|-----------|------------------|-----|
| Binary classification, keyword tagging | Bonsai 400M | Blazing fast, tiny RAM, handles simple labels |
| Multi-class classification (< 10 classes) | Bonsai 1.7B | Good accuracy, fits on RPi 5 |
| Structured JSON extraction (flat) | Bonsai 1.7B | Reliable field extraction from simple text |
| Summarization (short docs) | Bonsai 3B | Better coherence for longer outputs |
| Q&A, light reasoning | Bonsai 3B | Strong instruction-following |
| Code generation, complex reasoning | Bonsai 7B | Full reasoning capacity |
| Production edge service (low latency) | Bonsai 1.7B | Best speed/accuracy tradeoff |
| Batch offline processing | Bonsai 3B–7B | Accuracy matters more than speed |

**General rules:**
- If it fits in RAM → use the biggest model you can
- For RPi 5 (4–8 GB): Bonsai 1.7B is the sweet spot
- For latency-critical paths: Bonsai 400M or 1.7B
- For accuracy-critical tasks: Bonsai 3B or 7B

---

## Links

- 📖 **Article:** [Running 1-Bit LLMs: Bonsai & BitNet On-Device AI Guide](https://aistackinsights.ai/blog/1-bit-llms-bonsai-bitnet-on-device-ai-guide)
- 🤗 **Models:** [microsoft/Bonsai on Hugging Face](https://huggingface.co/microsoft/Bonsai-1.7B-GGUF)
- 🔧 **BitNet.cpp:** [github.com/microsoft/BitNet](https://github.com/microsoft/BitNet)
- 🦙 **llama.cpp:** [github.com/ggerganov/llama.cpp](https://github.com/ggerganov/llama.cpp)

---

## License

Scripts are MIT licensed. Model weights are subject to Microsoft's model license — check the Hugging Face repo for details.
