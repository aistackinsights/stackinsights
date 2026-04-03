# Cursor 3 + Gemma 4 — Companion Scripts

Companion code for the article:  
**[Cursor 3 + Gemma 4: The New AI Developer Stack for 2026](https://aistackinsights.ai/blog/cursor-3-gemma-4-new-ai-developer-stack-2026)**

These scripts let you run Gemma 4 locally, wire it into Cursor 3, and experiment with function calling and multi-agent patterns — all on your own hardware.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| **Ollama** | Installed by `setup_local_gemma4_cursor.sh` if missing |
| **Python 3.10+** | For type hints (`list[str] \| None`) |
| **pip install openai** | Only needed for `gemma4_function_calling.py` |
| **~16 GB RAM** | For the 27B model; use 4B on lighter hardware |
| **Google AI Studio key** | Only needed for the function-calling script |

---

## Quick Setup

```bash
# 1. Clone and enter the folder
git clone https://github.com/aistackinsights/stackinsights
cd stackinsights/cursor3-gemma4

# 2. Run the setup script (installs Ollama, pulls model, prints Cursor config)
chmod +x setup_local_gemma4_cursor.sh
./setup_local_gemma4_cursor.sh
```

The script will print a JSON snippet. Paste it into **Cursor 3 → Settings → Models**.

---

## Scripts

### `setup_local_gemma4_cursor.sh`

One-shot setup for the full local stack:

- Installs Ollama if not present
- Pulls `gemma3:27b`
- Starts the Ollama server as a background process
- Prints the exact JSON config to add Gemma 4 as a Cursor 3 model
- Tests the connection and writes `~/.ollama_cursor_status`

```bash
./setup_local_gemma4_cursor.sh
```

---

### `gemma4_function_calling.py`

Demonstrates Gemma 4's tool/function-calling capability via Google AI's OpenAI-compatible endpoint.

Includes three example tools:
- `get_weather(location)` — current weather data
- `search_codebase(query, path)` — codebase symbol search
- `create_github_issue(title, body, labels)` — opens a GitHub issue

Runs three demo conversations showing single-tool calls and multi-tool chains.

```bash
# Get a free key at https://aistudio.google.com/
GOOGLE_API_KEY=your_key_here python gemma4_function_calling.py
```

---

### `multi_agent_demo.py`

Fans out work to 3 parallel agents using Python threading — no frameworks needed.

Each agent receives the same sample function and produces a different artifact:

| Agent | Task |
|---|---|
| Code Reviewer | Spots bugs and suggests fixes |
| Test Writer | Generates pytest unit tests |
| Doc Writer | Writes a docstring + README section |

All 3 run concurrently against local Ollama. The timing summary shows the speedup over sequential execution.

```bash
# Requires Ollama running with gemma3:27b
python multi_agent_demo.py
```

---

## Gemma 4 Model Size Guide

| Model | VRAM / RAM | Best For |
|---|---|---|
| `gemma3:2b` | ~3 GB | Fast autocomplete, simple Q&A, low-end devices |
| `gemma3:4b` | ~5 GB | Lightweight coding assist, Raspberry Pi / small VPS |
| `gemma3:27b` | ~16 GB | Full coding agent, code review, test generation |
| `gemma-3-27b-it` (API) | — | Cloud inference via Google AI Studio (free tier) |

> **Rule of thumb:** Start with 27B locally if you have ≥16 GB RAM. Drop to 4B on laptops with <8 GB, or use the API for zero local overhead.

---

## Directory Structure

```
cursor3-gemma4/
├── README.md                     # This file
├── setup_local_gemma4_cursor.sh  # One-shot local stack setup
├── gemma4_function_calling.py    # Tool/function-calling agent (Google AI API)
└── multi_agent_demo.py           # Parallel multi-agent demo (local Ollama)
```

---

## Links

- 📖 Article: [Cursor 3 + Gemma 4: The New AI Developer Stack for 2026](https://aistackinsights.ai/blog/cursor-3-gemma-4-new-ai-developer-stack-2026)
- 🦙 Ollama: [https://ollama.com](https://ollama.com)
- 🔑 Google AI Studio: [https://aistudio.google.com](https://aistudio.google.com)
- 📦 Gemma on Ollama: `ollama pull gemma3:27b`
