#!/usr/bin/env bash
# setup_deerflow.sh
# ─────────────────
# One-shot setup: clones DeerFlow 2.0, creates .env, validates Docker, starts stack.
#
# Article: https://aistackinsights.ai/blog/deerflow-2-superagent-developer-guide
# Repo:    https://github.com/aistackinsights/stackinsights/tree/main/deerflow-2-superagent-developer-guide

set -euo pipefail

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

DEERFLOW_DIR="${DEERFLOW_DIR:-$HOME/deerflow}"
DEERFLOW_REPO="https://github.com/bytedance/deer-flow.git"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     DeerFlow 2.0 — Setup Script (AIStackInsights)    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# ─── 1. Prereqs ───────────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

for cmd in git docker python3; do
  if ! command -v "$cmd" &>/dev/null; then
    echo -e "${RED}✗ '$cmd' not found. Please install it and re-run.${NC}"
    exit 1
  fi
done

# Docker daemon running?
if ! docker info &>/dev/null; then
  echo -e "${RED}✗ Docker daemon is not running. Start Docker Desktop and re-run.${NC}"
  exit 1
fi

PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)"; then
  echo -e "${GREEN}✓ All prerequisites met (Python $PYTHON_VER, Docker running)${NC}"
else
  echo -e "${YELLOW}⚠ Python $PYTHON_VER detected — DeerFlow requires 3.11+. Consider upgrading.${NC}"
fi

# ─── 2. Clone ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/6] Cloning DeerFlow 2.0...${NC}"

if [[ -d "$DEERFLOW_DIR/.git" ]]; then
  echo -e "${GREEN}✓ DeerFlow already cloned at $DEERFLOW_DIR — pulling latest${NC}"
  git -C "$DEERFLOW_DIR" pull --rebase --quiet
else
  git clone --depth=1 "$DEERFLOW_REPO" "$DEERFLOW_DIR"
  echo -e "${GREEN}✓ Cloned to $DEERFLOW_DIR${NC}"
fi

# ─── 3. Environment config ────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[3/6] Configuring .env...${NC}"

ENV_FILE="$DEERFLOW_DIR/.env"

if [[ -f "$ENV_FILE" ]]; then
  echo -e "${GREEN}✓ .env already exists — skipping (edit manually if needed)${NC}"
else
  cp "$DEERFLOW_DIR/.env.example" "$ENV_FILE"
  echo -e "${GREEN}✓ Created .env from .env.example${NC}"
  echo ""
  echo "  Configure your LLM provider in $ENV_FILE"
  echo ""
  echo "  Option A — OpenAI (fastest to get started):"
  echo "    OPENAI_API_KEY=sk-..."
  echo "    BASIC_MODEL=gpt-4o"
  echo "    REASONING_MODEL=o3-mini"
  echo ""
  echo "  Option B — Anthropic Claude:"
  echo "    ANTHROPIC_API_KEY=sk-ant-..."
  echo "    BASIC_MODEL=claude-opus-4-6"
  echo "    REASONING_MODEL=claude-opus-4-6"
  echo ""
  echo "  Option C — Local via Ollama (full privacy, no cloud):"
  echo "    OLLAMA_BASE_URL=http://localhost:11434"
  echo "    BASIC_MODEL=ollama/qwen2.5:32b"
  echo "    REASONING_MODEL=ollama/deepseek-r1:32b"
  echo ""

  read -p "  Press Enter after editing .env to continue..."
fi

# ─── 4. Sandbox mode choice ───────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[4/6] Choosing sandbox mode...${NC}"
echo ""
echo "  DeerFlow can run agent tasks in two modes:"
echo ""
echo "  1. AIO Sandbox (recommended) — Docker container with browser + shell + filesystem"
echo "     Agents run in complete isolation from your host system"
echo ""
echo "  2. No sandbox — Agents run directly on your machine"
echo "     Faster, but agent actions can affect your local filesystem"
echo ""
read -p "  Use sandbox mode? [Y/n] " -n 1 -r SANDBOX_REPLY
echo ""

if [[ "$SANDBOX_REPLY" =~ ^[Nn]$ ]]; then
  # Disable sandbox in .env
  if grep -q "SANDBOX_ENABLED" "$ENV_FILE"; then
    sed -i.bak 's/^SANDBOX_ENABLED=.*/SANDBOX_ENABLED=false/' "$ENV_FILE"
  else
    echo "SANDBOX_ENABLED=false" >> "$ENV_FILE"
  fi
  echo -e "${YELLOW}⚠ Sandbox disabled. Agents will run with access to your local filesystem.${NC}"
else
  if grep -q "SANDBOX_ENABLED" "$ENV_FILE"; then
    sed -i.bak 's/^SANDBOX_ENABLED=.*/SANDBOX_ENABLED=true/' "$ENV_FILE"
  else
    echo "SANDBOX_ENABLED=true" >> "$ENV_FILE"
  fi
  echo -e "${GREEN}✓ Sandbox enabled (recommended)${NC}"
fi

# ─── 5. Docker build + start ──────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[5/6] Building and starting DeerFlow with Docker Compose...${NC}"
echo "  This may take a few minutes on first run."
echo ""

cd "$DEERFLOW_DIR"
docker compose pull --quiet 2>/dev/null || true
docker compose up -d --build

echo -e "${GREEN}✓ DeerFlow stack started${NC}"

# ─── 6. Health check ──────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[6/6] Waiting for API to be ready...${NC}"

MAX_WAIT=60
WAITED=0
while ! curl -sf http://localhost:8000/health &>/dev/null; do
  sleep 2
  WAITED=$((WAITED + 2))
  if [[ $WAITED -ge $MAX_WAIT ]]; then
    echo -e "${YELLOW}⚠ API not responding after ${MAX_WAIT}s — check 'docker compose logs' for errors${NC}"
    break
  fi
done

if curl -sf http://localhost:8000/health &>/dev/null; then
  echo -e "${GREEN}✓ DeerFlow API is healthy${NC}"
fi

# ─── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║             DeerFlow 2.0 is running! 🦌               ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Web UI:  http://localhost:3000"
echo "  API:     http://localhost:8000"
echo "  Docs:    http://localhost:8000/docs"
echo ""
echo "  Test with a task:"
echo "  curl -X POST http://localhost:8000/api/chat/completions \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"messages\":[{\"role\":\"user\",\"content\":\"Research the top 5 open-source LLM inference frameworks and write a comparison report\"}]}'"
echo ""
echo "  Or run the companion test script:"
echo "  python test_deerflow_api.py --task 'Your task here'"
echo ""
echo "  Logs:    docker compose logs -f"
echo "  Stop:    docker compose down"
echo ""
echo "  Article: https://aistackinsights.ai/blog/deerflow-2-superagent-developer-guide"
