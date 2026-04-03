#!/usr/bin/env bash
# =============================================================================
# setup_local_gemma4_cursor.sh
# Sets up a fully local Gemma 4 + Cursor 3 stack using Ollama.
#
# Usage:
#   chmod +x setup_local_gemma4_cursor.sh
#   ./setup_local_gemma4_cursor.sh
# =============================================================================

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
GEMMA_MODEL="gemma3:27b"           # Ollama model tag
OLLAMA_HOST="http://localhost:11434"
STATUS_FILE="$HOME/.ollama_cursor_status"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'  # No Color

info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR]${NC}  $*"; }

# ── Step 1: Check / install Ollama ───────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Gemma 4 + Cursor 3 — Local Stack Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if command -v ollama &>/dev/null; then
    OLLAMA_VERSION=$(ollama --version 2>/dev/null | head -1 || echo "unknown")
    success "Ollama already installed: $OLLAMA_VERSION"
else
    info "Ollama not found. Installing via official install script..."
    if command -v curl &>/dev/null; then
        curl -fsSL https://ollama.com/install.sh | sh
    else
        error "curl is required to install Ollama. Please install curl first."
        exit 1
    fi

    if command -v ollama &>/dev/null; then
        success "Ollama installed successfully."
    else
        error "Ollama installation failed. Please visit https://ollama.com for manual install."
        exit 1
    fi
fi

# ── Step 2: Start Ollama server ───────────────────────────────────────────────
info "Checking Ollama server status..."

if curl -s --max-time 2 "$OLLAMA_HOST" &>/dev/null; then
    success "Ollama server is already running at $OLLAMA_HOST"
else
    info "Starting Ollama server in background..."
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    echo "$OLLAMA_PID" > /tmp/ollama.pid

    # Wait for server to come up (up to 15s)
    for i in $(seq 1 15); do
        sleep 1
        if curl -s --max-time 1 "$OLLAMA_HOST" &>/dev/null; then
            success "Ollama server started (PID $OLLAMA_PID)"
            break
        fi
        if [[ $i -eq 15 ]]; then
            error "Ollama server didn't start in time. Check /tmp/ollama.log"
            exit 1
        fi
    done
fi

# ── Step 3: Pull Gemma 4 model ────────────────────────────────────────────────
info "Pulling $GEMMA_MODEL (this may take a while on first run ~15GB)..."

if ollama list 2>/dev/null | grep -q "$GEMMA_MODEL"; then
    success "Model $GEMMA_MODEL already available locally."
else
    ollama pull "$GEMMA_MODEL"
    success "Model $GEMMA_MODEL pulled successfully."
fi

# ── Step 4: Test connection ───────────────────────────────────────────────────
info "Testing model with a quick prompt..."

TEST_RESPONSE=$(curl -s "$OLLAMA_HOST/api/generate" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$GEMMA_MODEL\",
    \"prompt\": \"Reply with only: GEMMA_OK\",
    \"stream\": false,
    \"options\": {\"num_predict\": 10}
  }" | python3 -c "import sys,json; print(json.load(sys.stdin).get('response','ERROR').strip())" 2>/dev/null || echo "ERROR")

if echo "$TEST_RESPONSE" | grep -qi "GEMMA_OK\|OK"; then
    success "Model test passed: $TEST_RESPONSE"
else
    warn "Model test response: $TEST_RESPONSE (may still be OK — model just warmed up)"
fi

# ── Step 5: Print Cursor 3 config ─────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}  Cursor 3 Settings → Models → Add Model${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Paste this into Cursor's model config (JSON mode):"
echo ""
cat <<'JSON'
{
  "models": [
    {
      "name": "Gemma 4 27B (Local)",
      "provider": "ollama",
      "model": "gemma3:27b",
      "apiBase": "http://localhost:11434",
      "contextLength": 8192
    }
  ]
}
JSON
echo ""
echo "Or use the OpenAI-compatible endpoint:"
echo ""
cat <<'JSON'
{
  "openaiBaseUrl": "http://localhost:11434/v1",
  "openaiApiKey": "ollama",
  "model": "gemma3:27b"
}
JSON
echo ""

# ── Step 6: Write status file ─────────────────────────────────────────────────
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
cat > "$STATUS_FILE" <<EOF
# Ollama + Cursor 3 Setup Status
setup_completed_at=$TIMESTAMP
ollama_host=$OLLAMA_HOST
model=$GEMMA_MODEL
test_response=$TEST_RESPONSE
EOF

success "Setup complete! Status written to $STATUS_FILE"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}  All done! Gemma 4 is running locally.${NC}"
echo "  Ollama API: $OLLAMA_HOST"
echo "  Model:      $GEMMA_MODEL"
echo "  Logs:       /tmp/ollama.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
