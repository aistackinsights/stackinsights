# ARC-AGI-3: What 1% Score Reveals About Intelligence

Code samples from the article:
https://aistackinsights.ai/blog/arc-agi-3-what-1-percent-score-reveals-about-intelligence

## Files

- `arc_agi3_agent.py` — Minimal agent with WorldModel belief state, integrates with ARC-AGI-3 API
- `meta_agent.py` — MAML-style meta-learning agent skeleton with GRU belief state and inner-loop adaptation

## Setup

```bash
pip install httpx torch
ollama pull phi4-mini   # or use any model_fn
```

## Usage

```python
from arc_agi3_agent import ARCAgent, ollama_model
agent = ARCAgent(api_key="YOUR_KEY", model_fn=ollama_model)
result = agent.run_episode(task_id="arc3-task-001")
```

Get your API key at: https://arcprize.org/arc-agi/3
