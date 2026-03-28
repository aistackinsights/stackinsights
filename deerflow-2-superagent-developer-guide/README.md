# DeerFlow 2.0 — Developer Guide Companion Scripts

Companion code for the AIStackInsights article:
**"DeerFlow 2.0: ByteDance Just Open-Sourced a Full-Stack SuperAgent — Here's the Complete Developer Guide"**

📖 [Read the full article](https://aistackinsights.ai/blog/deerflow-2-superagent-developer-guide)

---

## Scripts

| File | Description |
|---|---|
| `setup_deerflow.sh` | One-shot setup script — clones DeerFlow, configures `.env`, starts Docker stack |
| `custom_skill_template.py` | Annotated template for building your own DeerFlow skill |
| `test_deerflow_api.py` | Fire a task at a running DeerFlow instance and stream the output |

---

## Requirements

- Docker Desktop (running)
- Python 3.11+
- Git

```bash
# Clone this companion repo
git clone https://github.com/aistackinsights/stackinsights.git
cd stackinsights/deerflow-2-superagent-developer-guide

# Run DeerFlow setup
chmod +x setup_deerflow.sh
./setup_deerflow.sh
```

---

## DeerFlow Quick Reference

| Feature | Details |
|---|---|
| GitHub | https://github.com/bytedance/deer-flow |
| License | MIT |
| LangGraph version | 1.0 |
| Default models | Doubao-Seed-2.0, DeepSeek v3.2, Kimi 2.5 |
| Also works with | OpenAI, Anthropic Claude, Ollama (local) |
| Sandbox | Docker AIO (browser + shell + filesystem) |
| Messaging | Slack, Telegram, Feishu |

---

*Part of [AIStackInsights Stackinsights](https://github.com/aistackinsights/stackinsights) — companion code for every article.*
