# cq: Stack Overflow for AI Agents — Knowledge Commons

Code samples from the article: https://aistackinsights.ai/blog/cq-stack-overflow-for-ai-agents-knowledge-commons

## Files
- `knowledge_store.py` -- self-hosted knowledge store (SQLite + FastAPI MCP server)
- `agent_knowledge_query.py` -- client library for querying/proposing knowledge
- `confidence.py` -- Bayesian confidence scoring with time decay

## Quick Start
`bash
pip install fastapi uvicorn httpx pydantic
uvicorn knowledge_store:app --port 8080
`

## Original cq by Mozilla AI
https://github.com/mozilla-ai/cq
