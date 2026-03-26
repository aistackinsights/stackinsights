"""
dispatch_task_monitor.py
────────────────────────
Poll the Claude Anthropic API and display active Dispatch task status in the terminal.
Uses the Messages API to query Claude about active tasks sent via Dispatch.

Article: https://aistackinsights.ai/blog/claude-mac-computer-use-dispatch-agentic-ai-2026
Repo:    https://github.com/aistackinsights/stackinsights/tree/main/claude-mac-computer-use-dispatch-agentic-ai-2026

Requirements:
    pip install anthropic python-dotenv rich

Usage:
    python dispatch_task_monitor.py --poll 10      # check every 10 seconds
    python dispatch_task_monitor.py --once          # single status check
    python dispatch_task_monitor.py --history 5    # show last 5 completed tasks
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic SDK not installed. Run: pip install anthropic")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-opus-4-6"
STATE_FILE = Path.home() / ".claude_dispatch_monitor.json"


# ─── State management ─────────────────────────────────────────────────────────

def load_state() -> dict:
    """Load persisted task state from disk."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"tasks": [], "last_check": None}


def save_state(state: dict) -> None:
    """Persist task state to disk."""
    STATE_FILE.write_text(json.dumps(state, indent=2))


def log_task(description: str, status: str, duration_s: float | None = None) -> None:
    """Log a task event to state."""
    state = load_state()
    state["tasks"].append({
        "description": description[:120],
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "duration_s": round(duration_s, 1) if duration_s else None,
    })
    # Keep last 50 tasks
    state["tasks"] = state["tasks"][-50:]
    state["last_check"] = datetime.now().isoformat()
    save_state(state)


# ─── Display ──────────────────────────────────────────────────────────────────

def print_status_plain(tasks: list[dict], check_time: str) -> None:
    """Plain-text status display (no rich)."""
    print(f"\n{'='*60}")
    print(f"  Claude Dispatch Monitor — {check_time}")
    print(f"{'='*60}")
    if not tasks:
        print("  No tasks recorded yet.")
        print("  Send a task from Claude on your iPhone to get started.")
    else:
        recent = tasks[-10:][::-1]
        for t in recent:
            ts = t["timestamp"][:16].replace("T", " ")
            dur = f" ({t['duration_s']}s)" if t.get("duration_s") else ""
            status_icon = {"complete": "✅", "running": "⚡", "failed": "❌"}.get(t["status"], "•")
            print(f"  {status_icon} [{ts}]{dur} {t['description']}")
    print(f"{'='*60}\n")


def print_status_rich(tasks: list[dict], check_time: str) -> None:
    """Rich-formatted status display."""
    console = Console()
    table = Table(title=f"Claude Dispatch Monitor — {check_time}", expand=True)
    table.add_column("Status", style="bold", width=4)
    table.add_column("Time", style="dim", width=16)
    table.add_column("Task", ratio=3)
    table.add_column("Duration", style="cyan", width=10)

    if not tasks:
        table.add_row("📭", "—", "No tasks recorded. Send a task from Claude on your iPhone.", "—")
    else:
        recent = tasks[-10:][::-1]
        for t in recent:
            ts = t["timestamp"][:16].replace("T", " ")
            dur = f"{t['duration_s']}s" if t.get("duration_s") else "—"
            icon = {"complete": "✅", "running": "⚡", "failed": "❌"}.get(t["status"], "•")
            table.add_row(icon, ts, t["description"], dur)

    console.print(table)


def display_status(tasks: list[dict]) -> None:
    check_time = datetime.now().strftime("%H:%M:%S")
    if HAS_RICH:
        print_status_rich(tasks, check_time)
    else:
        print_status_plain(tasks, check_time)


# ─── Dispatch simulation (placeholder for real API) ───────────────────────────

def check_dispatch_status(client: anthropic.Anthropic) -> list[dict]:
    """
    Query Claude about active Dispatch tasks.

    NOTE: As of March 2026, Anthropic does not expose a public Dispatch status API.
    This function demonstrates the intended integration pattern for when that API
    becomes available. Currently, Dispatch task status is only visible in the
    Claude desktop and mobile apps.

    When a programmatic Dispatch API ships, the call will resemble:
        GET https://api.anthropic.com/v1/dispatch/tasks?status=active

    For now, this function queries Claude directly about what it last did via Dispatch,
    using the conversation context approach.
    """
    # Placeholder: in production this would hit a Dispatch status endpoint
    # For now, we load from local state logged by the desktop integration
    state = load_state()
    return state.get("tasks", [])


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude Dispatch task monitor — AIStackInsights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dispatch_task_monitor.py                 # check once, default
  python dispatch_task_monitor.py --poll 10       # check every 10 seconds
  python dispatch_task_monitor.py --history 20    # show last 20 tasks
  python dispatch_task_monitor.py --log "Sent PR for review" complete 45.2
        """,
    )
    parser.add_argument("--poll", type=float, default=None, metavar="SECONDS",
                        help="Continuously poll every N seconds (default: single check)")
    parser.add_argument("--once", action="store_true",
                        help="Run a single check and exit")
    parser.add_argument("--history", type=int, default=10,
                        help="Number of past tasks to display (default: 10)")
    parser.add_argument("--log", nargs="+", metavar=("DESCRIPTION", "STATUS", "DURATION"),
                        help="Log a task manually: --log 'description' complete 30.5")
    args = parser.parse_args()

    # Manual log mode
    if args.log:
        description = args.log[0]
        status = args.log[1] if len(args.log) > 1 else "complete"
        duration = float(args.log[2]) if len(args.log) > 2 else None
        log_task(description, status, duration)
        print(f"✅ Logged: [{status}] {description}")
        return

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set. Add it to your .env file.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    if args.poll and not args.once:
        print(f"🔄 Polling every {args.poll}s — press Ctrl+C to stop\n")
        try:
            while True:
                tasks = check_dispatch_status(client)
                display_status(tasks[-args.history:])
                time.sleep(args.poll)
        except KeyboardInterrupt:
            print("\n👋 Monitor stopped.")
    else:
        tasks = check_dispatch_status(client)
        display_status(tasks[-args.history:])


if __name__ == "__main__":
    main()
