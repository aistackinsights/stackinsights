"""
Multi-Agent Orchestration Demo — Gemma 4 via Ollama
=====================================================
Spins up 3 parallel agents using Python threading, each with a distinct role:

  • Agent 1 — Code Reviewer  : Spots bugs in a sample function
  • Agent 2 — Test Writer    : Writes pytest tests for the same function
  • Agent 3 — Doc Writer     : Writes a docstring + README section

All 3 hit local Ollama (Gemma 4 27B) concurrently.
Demonstrates the "fan-out" pattern that underpins Cursor 3's parallel agent model.

Usage:
    # Make sure Ollama is running with gemma3:27b
    python multi_agent_demo.py

Requirements:
    pip install requests   # or just use stdlib urllib (see below)
    ollama pull gemma3:27b
"""

import json
import sys
import threading
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any

# ── Config ────────────────────────────────────────────────────────────────────

OLLAMA_BASE = "http://localhost:11434"
MODEL = "gemma3:27b"

# ── Sample code that all agents will analyse ──────────────────────────────────

SAMPLE_CODE = '''
def calculate_discount(price, discount_pct, user_type="regular"):
    """Apply a discount to a price."""
    if user_type == "vip":
        discount_pct = discount_pct * 1.5

    discount = price * discount_pct  # bug: should be discount_pct / 100
    final_price = price - discount

    if final_price < 0:
        final_price = 0  # floor at zero

    return final_price
'''

# ── Agent definitions ─────────────────────────────────────────────────────────

@dataclass
class Agent:
    name: str
    role: str
    system_prompt: str
    user_prompt: str
    result: str = ""
    error: str = ""
    elapsed_sec: float = 0.0


AGENTS = [
    Agent(
        name="Agent 1 — Code Reviewer",
        role="code_reviewer",
        system_prompt=(
            "You are a senior Python engineer doing a code review. "
            "Be precise and concise. List bugs with line references and fixes."
        ),
        user_prompt=(
            f"Review the following Python function for bugs, edge cases, "
            f"and correctness issues. Be concise.\n\n```python{SAMPLE_CODE}```"
        ),
    ),
    Agent(
        name="Agent 2 — Test Writer",
        role="test_writer",
        system_prompt=(
            "You are a Python testing expert. Write clean, idiomatic pytest tests. "
            "Include edge cases. No explanations — just the test code."
        ),
        user_prompt=(
            f"Write pytest unit tests for this function. "
            f"Cover: normal cases, VIP discount, zero/negative prices, boundary values."
            f"\n\n```python{SAMPLE_CODE}```"
        ),
    ),
    Agent(
        name="Agent 3 — Doc Writer",
        role="doc_writer",
        system_prompt=(
            "You are a technical writer. Write clear, developer-friendly documentation. "
            "Use Google-style docstrings and Markdown for README sections."
        ),
        user_prompt=(
            f"Write: (1) a Google-style docstring for this function, "
            f"and (2) a brief README section explaining its usage with an example."
            f"\n\n```python{SAMPLE_CODE}```"
        ),
    ),
]


# ── Ollama API call ───────────────────────────────────────────────────────────

def call_ollama(system: str, user: str, model: str = MODEL) -> str:
    """Send a chat request to local Ollama and return the assistant message."""
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "num_predict": 1024,
                "temperature": 0.3,
            },
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_BASE}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["message"]["content"].strip()
    except urllib.error.URLError as exc:
        raise ConnectionError(
            f"Cannot reach Ollama at {OLLAMA_BASE}. "
            f"Is it running? (`ollama serve`)\nDetails: {exc}"
        ) from exc


# ── Worker (runs in a thread) ─────────────────────────────────────────────────

def run_agent(agent: Agent, results_lock: threading.Lock) -> None:
    """Thread target: runs one agent and stores the result in `agent`."""
    start = time.perf_counter()
    try:
        agent.result = call_ollama(agent.system_prompt, agent.user_prompt)
    except Exception as exc:  # noqa: BLE001
        agent.error = str(exc)
    finally:
        agent.elapsed_sec = time.perf_counter() - start

    with results_lock:
        status = "✓" if not agent.error else "✗"
        print(f"  [{status}] {agent.name} finished in {agent.elapsed_sec:.1f}s")


# ── Pretty printer ────────────────────────────────────────────────────────────

def print_results(agents: list[Agent]) -> None:
    """Print all agent results in a readable format."""
    total = sum(a.elapsed_sec for a in agents)
    max_single = max(a.elapsed_sec for a in agents)

    print("\n" + "═" * 65)
    print("  RESULTS")
    print("═" * 65)

    for agent in agents:
        print(f"\n{'─' * 65}")
        print(f"  {agent.name}")
        print(f"{'─' * 65}")
        if agent.error:
            print(f"  ERROR: {agent.error}")
        else:
            # Indent result lines
            for line in agent.result.splitlines():
                print(f"  {line}")

    print("\n" + "═" * 65)
    print(f"  Timing Summary")
    print("═" * 65)
    for agent in agents:
        bar_len = int((agent.elapsed_sec / max_single) * 30) if max_single > 0 else 0
        bar = "█" * bar_len + "░" * (30 - bar_len)
        print(f"  {agent.name[:30]:30s} {bar} {agent.elapsed_sec:5.1f}s")
    print(f"\n  Sequential equivalent: ~{total:.1f}s")
    print(f"  Parallel wall-clock:   ~{max_single:.1f}s")
    speedup = total / max_single if max_single > 0 else 1.0
    print(f"  Speedup factor:        ~{speedup:.1f}x")
    print("═" * 65 + "\n")


# ── Health check ──────────────────────────────────────────────────────────────

def check_ollama_health() -> bool:
    """Return True if Ollama is reachable and the model is available."""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            return any(MODEL.split(":")[0] in m for m in models)
    except Exception:  # noqa: BLE001
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n" + "═" * 65)
    print("  Multi-Agent Demo — Gemma 4 (Ollama) Fan-Out Pattern")
    print("═" * 65)
    print(f"\n  Model : {MODEL}")
    print(f"  Agents: {len(AGENTS)} (running concurrently)")
    print(f"\n  Sample code under analysis:")
    for line in SAMPLE_CODE.strip().splitlines():
        print(f"    {line}")
    print()

    # Health check
    print("  Checking Ollama connection...")
    if not check_ollama_health():
        print(
            f"\n  ERROR: Cannot reach Ollama at {OLLAMA_BASE} or model '{MODEL}' not found.\n"
            f"  Run: ollama serve  (in another terminal)\n"
            f"  Then: ollama pull {MODEL}\n"
        )
        sys.exit(1)
    print(f"  Ollama OK — model {MODEL} ready.\n")

    # Launch all agents in parallel
    print("  Launching agents...")
    results_lock = threading.Lock()
    threads = [
        threading.Thread(target=run_agent, args=(agent, results_lock), daemon=True)
        for agent in AGENTS
    ]

    wall_start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    wall_elapsed = time.perf_counter() - wall_start

    print(f"\n  All agents done in {wall_elapsed:.1f}s wall-clock time.")
    print_results(AGENTS)


if __name__ == "__main__":
    main()
