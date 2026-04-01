#!/usr/bin/env bash
# =============================================================================
# edge_deploy_rpi.sh — Deploy Bonsai 1-bit LLM on Raspberry Pi 5
# Companion script for: https://aistackinsights.ai/blog/1-bit-llms-bonsai-bitnet-on-device-ai-guide
#
# Tested on: Raspberry Pi 5 (8 GB), Raspberry Pi OS Bookworm (64-bit)
# Expected runtime: ~15–25 minutes on a fresh Pi (build takes the longest)
#
# What this script does:
#   1. Installs system build dependencies
#   2. Clones and builds BitNet.cpp from source
#   3. Downloads the Bonsai 1.7B model from Hugging Face
#   4. Starts a lightweight HTTP inference server
#   5. Registers a systemd service for auto-start on boot
# =============================================================================

set -euo pipefail   # Exit on error, undefined vars, or pipe failures

# ─── Configuration ────────────────────────────────────────────────────────────
INSTALL_DIR="${HOME}/bitnet"                          # Where BitNet.cpp lives
MODEL_DIR="${HOME}/models"                            # Where GGUF models live
MODEL_REPO="microsoft/Bonsai-1.7B-GGUF"              # HuggingFace repo ID
MODEL_FILE="Bonsai-1.7B-Q8_0.gguf"                   # Specific GGUF file
SERVER_PORT=8080                                       # HTTP server port
THREADS=4                                             # CPU threads (Pi 5 has 4 cores)
MAX_TOKENS=256                                        # Default generation length
SERVICE_NAME="bonsai-inference"                       # systemd service name

# Colors for readable output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*" >&2; exit 1; }

# ─── Step 1: System dependencies ─────────────────────────────────────────────
log "Step 1/5 — Installing system dependencies..."
# cmake is required to build BitNet.cpp
# python3-pip and python3-venv for the inference server
# git to clone repos
# libopenblas for optimized matrix ops on ARM
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
    cmake \
    git \
    python3 \
    python3-pip \
    python3-venv \
    libopenblas-dev \
    build-essential \
    curl

log "Dependencies installed."

# ─── Step 2: Clone and build BitNet.cpp ───────────────────────────────────────
log "Step 2/5 — Cloning BitNet.cpp..."

if [ -d "${INSTALL_DIR}" ]; then
    warn "BitNet.cpp directory already exists at ${INSTALL_DIR}. Pulling latest..."
    cd "${INSTALL_DIR}" && git pull
else
    git clone --depth 1 https://github.com/microsoft/BitNet.git "${INSTALL_DIR}"
fi

log "Building BitNet.cpp (this takes 10–20 minutes on Pi 5)..."
cd "${INSTALL_DIR}"

# Create a build directory and configure with cmake
mkdir -p build && cd build

cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLAMA_BLAS=ON \
    -DLLAMA_BLAS_VENDOR=OpenBLAS \
    -DLLAMA_NATIVE=ON        # Enables ARM NEON optimizations on Pi 5

# Build using all available cores (-j $(nproc))
make -j "$(nproc)"
log "BitNet.cpp build complete. Binary: ${INSTALL_DIR}/build/bin/llama-cli"

# ─── Step 3: Download Bonsai 1.7B model from Hugging Face ────────────────────
log "Step 3/5 — Downloading Bonsai 1.7B from Hugging Face..."

mkdir -p "${MODEL_DIR}"

# Install huggingface_hub CLI if not present
if ! command -v huggingface-cli &>/dev/null; then
    pip3 install --quiet huggingface_hub[cli]
fi

# huggingface-cli download pulls only the requested file, not the full repo
huggingface-cli download \
    "${MODEL_REPO}" \
    "${MODEL_FILE}" \
    --local-dir "${MODEL_DIR}" \
    --local-dir-use-symlinks False

MODEL_PATH="${MODEL_DIR}/${MODEL_FILE}"
log "Model downloaded to: ${MODEL_PATH}"

# Quick sanity check — model file should be > 1 GB
MODEL_SIZE=$(du -m "${MODEL_PATH}" | cut -f1)
if [ "${MODEL_SIZE}" -lt 500 ]; then
    err "Model file looks too small (${MODEL_SIZE} MB). Download may have failed."
fi
log "Model size: ${MODEL_SIZE} MB — looks good."

# ─── Step 4: Create HTTP inference server ────────────────────────────────────
log "Step 4/5 — Creating inference server..."

SERVER_SCRIPT="${INSTALL_DIR}/inference_server.py"

cat > "${SERVER_SCRIPT}" << 'PYEOF'
#!/usr/bin/env python3
"""
Minimal HTTP inference server for Bonsai on Raspberry Pi.
Wraps llama-cli via subprocess and exposes two endpoints:

  POST /generate   {"prompt": "...", "max_tokens": 128}
  GET  /health     Returns {"status": "ok", "model": "..."}
"""

import http.server
import json
import os
import subprocess
import sys
from urllib.parse import urlparse

# ── Config from environment (set by systemd service) ──────────────────────────
BINARY     = os.environ.get("BITNET_BINARY",     "/home/pi/bitnet/build/bin/llama-cli")
MODEL_PATH = os.environ.get("BITNET_MODEL",      "/home/pi/models/Bonsai-1.7B-Q8_0.gguf")
THREADS    = int(os.environ.get("BITNET_THREADS", "4"))
MAX_TOKENS = int(os.environ.get("BITNET_MAX_TOKENS", "256"))
PORT       = int(os.environ.get("BITNET_PORT",   "8080"))


def run_inference(prompt: str, max_tokens: int) -> dict:
    """Call llama-cli and return generated text + timing info."""
    import time
    cmd = [
        BINARY,
        "-m", MODEL_PATH,
        "-p", prompt,
        "-n", str(max_tokens),
        "--temp", "0.7",
        "-t", str(THREADS),
        "--no-display-prompt",
        "-e",
    ]
    start = time.perf_counter()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        return {"error": result.stderr[:300], "latency_sec": elapsed}

    text = result.stdout.strip()
    tokens = len(text.split())
    return {
        "text": text,
        "tokens": tokens,
        "latency_sec": round(elapsed, 3),
        "tokens_per_sec": round(tokens / elapsed, 1) if elapsed > 0 else 0,
    }


class InferenceHandler(http.server.BaseHTTPRequestHandler):
    """Simple request handler — no dependencies beyond stdlib."""

    def log_message(self, fmt, *args):
        # Suppress default access log noise; change to `pass` to silence entirely
        print(f"[{self.address_string()}] {fmt % args}")

    def _send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json(200, {
                "status": "ok",
                "model": os.path.basename(MODEL_PATH),
                "binary": BINARY,
                "threads": THREADS,
            })
        else:
            self._send_json(404, {"error": "Not found. Try POST /generate or GET /health"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/generate":
            self._send_json(404, {"error": "Not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            req = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        prompt = req.get("prompt", "").strip()
        if not prompt:
            self._send_json(400, {"error": "'prompt' is required"})
            return

        max_tokens = int(req.get("max_tokens", MAX_TOKENS))
        result = run_inference(prompt, max_tokens)
        self._send_json(200 if "error" not in result else 500, result)


if __name__ == "__main__":
    print(f"Starting Bonsai inference server on port {PORT}...")
    print(f"  Model:  {MODEL_PATH}")
    print(f"  Binary: {BINARY}")
    print(f"  Threads:{THREADS}")
    print(f"\nEndpoints:")
    print(f"  POST http://localhost:{PORT}/generate")
    print(f"  GET  http://localhost:{PORT}/health\n")
    server = http.server.HTTPServer(("0.0.0.0", PORT), InferenceHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
PYEOF

chmod +x "${SERVER_SCRIPT}"
log "Inference server script created: ${SERVER_SCRIPT}"

# ─── Step 5: Create and enable systemd service ────────────────────────────────
log "Step 5/5 — Creating systemd service for auto-start..."

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Determine the actual username (works whether run as root or via sudo)
ACTUAL_USER="${SUDO_USER:-$(whoami)}"

sudo tee "${SERVICE_FILE}" > /dev/null << SVCEOF
[Unit]
Description=Bonsai 1-bit LLM Inference Server
After=network.target
Documentation=https://aistackinsights.ai/blog/1-bit-llms-bonsai-bitnet-on-device-ai-guide

[Service]
Type=simple
User=${ACTUAL_USER}
WorkingDirectory=${INSTALL_DIR}

# Environment variables — edit these to change model or port
Environment=BITNET_BINARY=${INSTALL_DIR}/build/bin/llama-cli
Environment=BITNET_MODEL=${MODEL_PATH}
Environment=BITNET_THREADS=${THREADS}
Environment=BITNET_MAX_TOKENS=${MAX_TOKENS}
Environment=BITNET_PORT=${SERVER_PORT}

ExecStart=/usr/bin/python3 ${SERVER_SCRIPT}
Restart=on-failure
RestartSec=5s

# Resource limits — prevents the process from starving the OS
MemoryMax=4G
CPUQuota=90%

[Install]
WantedBy=multi-user.target
SVCEOF

# Reload systemd daemon, enable, and start the service
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl start  "${SERVICE_NAME}"

log "systemd service '${SERVICE_NAME}' enabled and started."

# ─── Health check ─────────────────────────────────────────────────────────────
log "Running health check (waiting 5 s for server to start)..."
sleep 5

HEALTH=$(curl -sf "http://localhost:${SERVER_PORT}/health" 2>/dev/null || echo "FAIL")
if echo "${HEALTH}" | grep -q '"status":"ok"'; then
    log "Health check passed! Server is running."
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Bonsai deployment complete!                  ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo ""
    echo "  Generate text:"
    echo "    curl -s -X POST http://localhost:${SERVER_PORT}/generate \\"
    echo "         -H 'Content-Type: application/json' \\"
    echo "         -d '{\"prompt\": \"What is 1-bit quantization?\", \"max_tokens\": 100}'"
    echo ""
    echo "  Check health:"
    echo "    curl http://localhost:${SERVER_PORT}/health"
    echo ""
    echo "  View logs:"
    echo "    sudo journalctl -u ${SERVICE_NAME} -f"
    echo ""
    echo "  Stop/start service:"
    echo "    sudo systemctl stop  ${SERVICE_NAME}"
    echo "    sudo systemctl start ${SERVICE_NAME}"
else
    warn "Health check failed. Server may still be loading the model (can take 30–60 s)."
    warn "Check logs: sudo journalctl -u ${SERVICE_NAME} -n 50"
fi
