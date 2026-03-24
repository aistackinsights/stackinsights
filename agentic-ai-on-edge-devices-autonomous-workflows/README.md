# Agentic AI on Edge Devices

Code samples from the article: https://aistackinsights.ai/blog/agentic-ai-on-edge-devices-autonomous-workflows

## Files
- `edge_agent.py` -- full ReAct agentic loop running on ollama (phi4-mini / qwen2.5:3b)
- `agent_state.py` -- durable SQLite state management that survives device reboots

## Quick Start
`bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull phi4-mini
python edge_agent.py
`
