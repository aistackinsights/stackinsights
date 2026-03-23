# query_local_llm.py — Query Qwen3.5-397B via OpenAI-compatible API
# Article: https://aistackinsights.ai/blog/flash-moe-run-400b-llm-consumer-hardware
#
# Usage:
#   pip install httpx
#   python query_local_llm.py
#
# Requires: llama-server running locally (see run_server.sh)

import httpx
import json
import sys
from typing import Optional

BASE_URL = "http://127.0.0.1:8080/v1"


def chat(
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
    system: Optional[str] = None,
) -> str:
    """Send a chat message to the local Qwen3.5-397B server."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "qwen35-397b",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }

    try:
        r = httpx.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except httpx.ConnectError:
        print(
            "ERROR: Cannot connect to llama-server at http://127.0.0.1:8080\n"
            "Make sure run_server.sh is running first.",
            file=sys.stderr,
        )
        sys.exit(1)


def stream_chat(prompt: str, max_tokens: int = 512) -> None:
    """Stream tokens from the local server, printing as they arrive."""
    payload = {
        "model": "qwen35-397b",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": True,
    }

    with httpx.stream(
        "POST",
        f"{BASE_URL}/chat/completions",
        json=payload,
        timeout=120,
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                chunk = json.loads(line[6:])
                delta = chunk["choices"][0]["delta"].get("content", "")
                print(delta, end="", flush=True)
    print()  # newline after stream ends


if __name__ == "__main__":
    print("=== Qwen3.5-397B Local Inference Demo ===\n")

    # Test 1: Hard reasoning
    print("Test 1: Graduate-level reasoning (GPQA-style)")
    print("-" * 50)
    response = chat(
        "Explain the Gated Delta Network architecture used in Qwen3.5 "
        "and why it reduces KV cache memory compared to standard attention. "
        "Be technically precise.",
        max_tokens=600,
    )
    print(response)

    print("\nTest 2: Streaming response")
    print("-" * 50)
    stream_chat(
        "Write a Python function that implements a simple LRU cache using an OrderedDict. "
        "Include type hints and a docstring.",
        max_tokens=400,
    )
