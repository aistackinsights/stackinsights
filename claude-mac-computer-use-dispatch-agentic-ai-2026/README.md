# Claude Mac Computer Use + Dispatch — Companion Scripts

Code and scripts for the AIStackInsights article:
**"Claude Can Now Control Your Mac. Here's What That Actually Means."**

📖 [Read the full article](https://aistackinsights.ai/blog/claude-mac-computer-use-dispatch-agentic-ai-2026)

---

## Scripts

| File | Description |
|---|---|
| `setup_dispatch.sh` | Automates macOS setup for Claude computer use + Dispatch pairing |
| `claude_computer_use_api.py` | Python demo using Claude's computer use API (Anthropic SDK) |
| `dispatch_task_monitor.py` | Poll and display active Dispatch task status via Claude API |

---

## Requirements

- macOS (Sonoma or later recommended)
- Claude Pro or Max subscription ($17+/mo)
- Python 3.11+ for Python scripts
- `anthropic` SDK: `pip install anthropic`

```bash
pip install anthropic python-dotenv rich
```

---

## Setup

```bash
# Clone the companion repo
git clone https://github.com/aistackinsights/stackinsights.git
cd stackinsights/claude-mac-computer-use-dispatch-agentic-ai-2026

# Add your API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=your_key_here

# Run the setup helper
chmod +x setup_dispatch.sh
./setup_dispatch.sh
```

---

## Usage

### 1. macOS Setup Helper

```bash
./setup_dispatch.sh
```

Checks for Claude desktop app, macOS Accessibility permissions, and walks you through enabling computer use in Cowork settings.

### 2. Computer Use API Demo

```bash
python claude_computer_use_api.py --task "Open TextEdit and write a short poem about AI agents"
```

### 3. Dispatch Task Monitor

```bash
python dispatch_task_monitor.py --poll 5
```

Polls the Claude API every 5 seconds and prints active Dispatch task status to the terminal.

---

## Notes

- Computer use is a **research preview** — reliability varies by application and task complexity
- Always review what Claude intends to do before running tasks against sensitive applications
- Dispatch requires the Claude iOS app paired to your Mac via QR code in Cowork settings

---

*Part of [AIStackInsights Stackinsights](https://github.com/aistackinsights/stackinsights) — companion code for every article.*
