import json
from datetime import datetime


def run_tool(tool: str, input_params: dict) -> dict:
    """
    Execute a tool and return a structured observation.
    Never raises — errors become observations with success=False.
    """
    try:
        if tool == "web_search":
            return _web_search(input_params)
        elif tool == "read_file":
            return _read_file(input_params)
        elif tool == "write_file":
            return _write_file(input_params)
        elif tool == "summarize":
            return _summarize(input_params)
        else:
            return {"success": False, "error": f"Unknown tool: {tool}"}
    except Exception as e:
        return {"success": False, "error": str(e), "tool": tool}


def _web_search(params: dict) -> dict:
    """Stub: replace with real search API (Brave, Tavily, etc.)"""
    query = params.get("query", "")
    # In production: call Brave Search API or Tavily
    return {
        "success": True,
        "query": query,
        "results": [
            {"title": f"Result for '{query}'", "url": "https://example.com", "snippet": "Stub result."}
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


def _read_file(params: dict) -> dict:
    path = params.get("path", "")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "path": path, "content": content[:4000]}  # cap at 4k chars
    except FileNotFoundError:
        return {"success": False, "error": f"File not found: {path}"}


def _write_file(params: dict) -> dict:
    path = params.get("path", "")
    content = params.get("content", "")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"success": True, "path": path, "bytes_written": len(content)}


def _summarize(params: dict) -> dict:
    text = params.get("text", "")
    # Stub: in production call LLM with summarization prompt
    truncated = text[:200] + "..." if len(text) > 200 else text
    return {"success": True, "summary": f"[Summary of: {truncated}]", "original_length": len(text)}
