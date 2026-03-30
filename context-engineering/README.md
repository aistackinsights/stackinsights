# Context Engineering — Companion Scripts

Companion code for the article **[Context Engineering: A Developer's Guide (2026)](https://aistackinsights.ai/blog/context-engineering-developer-guide-2026)** on [aistackinsights.ai](https://aistackinsights.ai).

These scripts demonstrate three practical patterns for giving LLMs the right context at the right time: structured tool access via MCP, hybrid retrieval-augmented generation, and persistent agent memory.

---

## Quick Install

```bash
pip install mcp llama_index anthropic letta llama-index-retrievers-bm25
```

> **Note:** Each script can be used independently — install only what you need.

---

## Scripts

### 1. `mcp_server_template.py` — MCP Server with Codebase Tools

A production-ready [Model Context Protocol](https://modelcontextprotocol.io) server that exposes your codebase as structured tools any MCP-compatible client (Claude Desktop, Cursor, etc.) can call.

**Tools exposed:**

| Tool | Description |
|------|-------------|
| `get_schema` | Extract a specific model definition from a Prisma schema file |
| `get_recent_logs` | Tail the last N lines from any log file |
| `search_codebase` | Regex/grep search across `.ts`, `.tsx`, and `.py` files |

**Run:**

```bash
python mcp_server_template.py
```

Wire it into Claude Desktop by adding to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "codebase": {
      "command": "python",
      "args": ["/path/to/mcp_server_template.py"]
    }
  }
}
```

---

### 2. `hybrid_rag_pipeline.py` — Hybrid RAG (Semantic + BM25)

Indexes your source directory and answers questions using a fusion of vector (semantic) and BM25 (keyword) retrieval. Retrieved context is injected into a Claude `claude-sonnet-4-6` prompt for grounded, accurate answers.

**Why hybrid?** Vector search finds conceptually similar passages; BM25 finds exact identifier matches. Fusing both with Reciprocal Rank Fusion gives you the best of both worlds.

**Run:**

```bash
python hybrid_rag_pipeline.py "How does authentication work in this codebase?"

# Point at a different source directory
python hybrid_rag_pipeline.py "What does UserService do?" --src ./packages/api/src
```

**Use as a library:**

```python
from hybrid_rag_pipeline import build_index, ask

index = build_index("./src")
answer = ask("Where are database migrations defined?", index=index)
print(answer)
```

> Set your `ANTHROPIC_API_KEY` environment variable before running.

---

### 3. `letta_memory_agent.py` — Persistent Memory Agent (Letta)

A [Letta](https://github.com/letta-ai/letta) (formerly MemGPT) agent that persists facts across sessions using two memory tiers:

- **Core memory** — always in-context; stores persona, user profile, and key decisions
- **Archival memory** — unlimited vector-backed long-term storage; retrieved on demand

**Setup:**

```bash
pip install letta
letta server &    # starts the Letta REST server on http://localhost:8283
python letta_memory_agent.py
```

Re-run the script multiple times to see the agent recall facts from prior sessions without being re-told.

---

## Environment Variables

| Variable | Required by | Description |
|----------|-------------|-------------|
| `ANTHROPIC_API_KEY` | `hybrid_rag_pipeline.py` | Your Anthropic API key |

---

## Related Article

📖 **[Context Engineering: A Developer's Guide (2026)](https://aistackinsights.ai/blog/context-engineering-developer-guide-2026)**

Covers the full context engineering stack: MCP servers, hybrid RAG, prompt caching, structured outputs, and persistent memory — with code examples and production tips.

---

## License

MIT
