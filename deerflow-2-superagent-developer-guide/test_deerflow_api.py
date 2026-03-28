"""
test_deerflow_api.py
─────────────────────
Fire a task at a running DeerFlow 2.0 instance and stream the response.
Validates your setup and shows the agent's reasoning + tool calls in real time.

Article: https://aistackinsights.ai/blog/deerflow-2-superagent-developer-guide
Repo:    https://github.com/aistackinsights/stackinsights/tree/main/deerflow-2-superagent-developer-guide

Requirements:
    pip install httpx rich

Usage:
    python test_deerflow_api.py
    python test_deerflow_api.py --task "Research the top AI agent frameworks of 2026 and write a comparison table"
    python test_deerflow_api.py --host http://localhost:8000 --task "Summarize today's AI news"
    python test_deerflow_api.py --list-skills   # list available skills
"""

import argparse
import json
import sys
import time
from datetime import datetime

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.text import Text
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

DEFAULT_HOST = "http://localhost:8000"
DEFAULT_TASK = (
    "Research the top 3 open-source AI agent frameworks released in 2026. "
    "For each one, summarize: what it does, its key technical differentiators, "
    "GitHub stars, and who should use it. Format the output as a markdown comparison table."
)


# ─── Health check ─────────────────────────────────────────────────────────────

def check_health(host: str) -> bool:
    try:
        r = httpx.get(f"{host}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


# ─── List skills ──────────────────────────────────────────────────────────────

def list_skills(host: str) -> None:
    try:
        r = httpx.get(f"{host}/api/skills", timeout=10)
        r.raise_for_status()
        skills = r.json()
        if HAS_RICH:
            from rich.table import Table
            t = Table(title="Available DeerFlow Skills")
            t.add_column("Name", style="cyan")
            t.add_column("Description")
            for s in skills:
                t.add_row(s.get("name", "?"), s.get("description", "")[:80])
            console.print(t)
        else:
            print("\nAvailable skills:")
            for s in skills:
                print(f"  {s.get('name')}: {s.get('description', '')[:60]}")
    except Exception as e:
        print(f"Could not fetch skills: {e}")


# ─── Task submission (streaming) ──────────────────────────────────────────────

def run_task_streaming(host: str, task: str) -> None:
    """Submit a task and stream the response using SSE."""
    url = f"{host}/api/chat/stream"
    payload = {
        "messages": [{"role": "user", "content": task}],
        "stream": True,
    }

    if HAS_RICH:
        console.print(Panel(
            f"[bold cyan]Task:[/bold cyan] {task}\n\n"
            f"[dim]Host: {host} | Started: {datetime.now().strftime('%H:%M:%S')}[/dim]",
            title="🦌 DeerFlow 2.0 — Task Submitted",
            border_style="cyan",
        ))
    else:
        print(f"\nTask: {task}")
        print(f"Host: {host}")
        print("─" * 60)

    full_response = []
    tool_calls_seen = []
    start_time = time.time()

    try:
        with httpx.stream("POST", url, json=payload, timeout=300) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw == "[DONE]":
                    break
                try:
                    chunk = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                tool_call = delta.get("tool_calls")

                if content:
                    full_response.append(content)
                    if HAS_RICH:
                        console.print(content, end="", highlight=False)
                    else:
                        print(content, end="", flush=True)

                if tool_call:
                    fn = tool_call[0].get("function", {})
                    name = fn.get("name", "")
                    if name and name not in tool_calls_seen:
                        tool_calls_seen.append(name)
                        if HAS_RICH:
                            console.print(f"\n  [dim cyan]⚡ Tool call: {name}[/dim cyan]")
                        else:
                            print(f"\n  [tool: {name}]", flush=True)

    except httpx.ConnectError:
        print(f"\n\nERROR: Cannot connect to DeerFlow at {host}")
        print("Make sure DeerFlow is running: docker compose up -d")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[Interrupted]")

    elapsed = round(time.time() - start_time, 1)
    full_text = "".join(full_response)

    if HAS_RICH:
        console.print(f"\n\n[dim]─── Completed in {elapsed}s | {len(full_text)} chars | "
                      f"Tools used: {', '.join(tool_calls_seen) or 'none'} ───[/dim]")
    else:
        print(f"\n\n─── Done in {elapsed}s | Tools: {', '.join(tool_calls_seen) or 'none'} ───")


# ─── Task submission (non-streaming) ─────────────────────────────────────────

def run_task_sync(host: str, task: str) -> None:
    """Submit a task and wait for the full response."""
    url = f"{host}/api/chat/completions"
    payload = {"messages": [{"role": "user", "content": task}]}

    if HAS_RICH:
        console.print(f"[dim]Submitting task (non-streaming)...[/dim]")
    else:
        print("Submitting task...")

    try:
        r = httpx.post(url, json=payload, timeout=300)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        if HAS_RICH:
            console.print(Markdown(content))
        else:
            print(content)
    except httpx.ConnectError:
        print(f"ERROR: Cannot connect to {host}. Is DeerFlow running?")
        sys.exit(1)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Test a running DeerFlow 2.0 instance — AIStackInsights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_deerflow_api.py                                    # default research task
  python test_deerflow_api.py --task "Write a Python web scraper for HN"
  python test_deerflow_api.py --task "Analyze NVDA stock technicals" --no-stream
  python test_deerflow_api.py --list-skills
  python test_deerflow_api.py --host http://my-server:8000 --task "..."
        """,
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="DeerFlow API host")
    parser.add_argument("--task", default=DEFAULT_TASK, help="Task to run")
    parser.add_argument("--no-stream", action="store_true", help="Use non-streaming API")
    parser.add_argument("--list-skills", action="store_true", help="List available skills and exit")
    args = parser.parse_args()

    # Health check
    if not check_health(args.host):
        print(f"ERROR: DeerFlow not reachable at {args.host}")
        print("Start it with: docker compose up -d  (from deer-flow directory)")
        print("Or run the setup script: ./setup_deerflow.sh")
        sys.exit(1)

    if HAS_RICH:
        console.print(f"[green]✓ DeerFlow is healthy at {args.host}[/green]")
    else:
        print(f"✓ DeerFlow is healthy at {args.host}")

    if args.list_skills:
        list_skills(args.host)
        return

    if args.no_stream:
        run_task_sync(args.host, args.task)
    else:
        run_task_streaming(args.host, args.task)


if __name__ == "__main__":
    main()
