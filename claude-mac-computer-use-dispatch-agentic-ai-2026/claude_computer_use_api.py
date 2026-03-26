"""
claude_computer_use_api.py
──────────────────────────
Minimal working demo of Claude's computer use API via the Anthropic Python SDK.
Shows how to send a task, receive tool_use blocks, and simulate the screenshot→action loop.

Article: https://aistackinsights.ai/blog/claude-mac-computer-use-dispatch-agentic-ai-2026
Repo:    https://github.com/aistackinsights/stackinsights/tree/main/claude-mac-computer-use-dispatch-agentic-ai-2026

Requirements:
    pip install anthropic python-dotenv Pillow

Usage:
    python claude_computer_use_api.py --task "Open TextEdit and write Hello from Claude"
    python claude_computer_use_api.py --task "Check my top unread emails in Mail" --verbose
    python claude_computer_use_api.py --dry-run   # prints the request without executing
"""

import argparse
import base64
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
    pass  # .env loading is optional

# ─── Config ──────────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-opus-4-6"  # Computer use requires claude-3-5-sonnet or later
MAX_TOKENS = 4096
MAX_ITERATIONS = 20  # Safety cap on the action loop

# Screen dimensions — update to match your display
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900

# ─── Tool definitions ─────────────────────────────────────────────────────────

COMPUTER_USE_TOOLS = [
    {
        "type": "computer_20241022",
        "name": "computer",
        "display_width_px": SCREEN_WIDTH,
        "display_height_px": SCREEN_HEIGHT,
        "display_number": 1,
    },
    {
        "type": "bash_20241022",
        "name": "bash",
    },
    {
        "type": "text_editor_20241022",
        "name": "str_replace_editor",
    },
]

# ─── Screenshot capture ───────────────────────────────────────────────────────

def capture_screenshot() -> str:
    """Capture the current screen and return as base64-encoded PNG."""
    import subprocess
    import tempfile

    if sys.platform != "darwin":
        # On non-macOS, return a placeholder (white image)
        print("  [screenshot] Non-macOS detected — returning placeholder image")
        try:
            from PIL import Image
            import io
            img = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), color=(240, 240, 240))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return base64.standard_b64encode(buf.getvalue()).decode("utf-8")
        except ImportError:
            # Minimal 1x1 white PNG as fallback
            MINIMAL_PNG = (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
                b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
                b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
            )
            return base64.standard_b64encode(MINIMAL_PNG).decode("utf-8")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name

    try:
        subprocess.run(["screencapture", "-x", tmp_path], check=True, capture_output=True)
        with open(tmp_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ─── Action execution ─────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict, verbose: bool = False) -> str:
    """
    Execute a computer_use tool action.
    In a real implementation, this drives the mouse/keyboard via pyautogui or
    Anthropic's reference computer-use Docker environment.
    This demo prints the action and returns a mock result.
    """
    action = tool_input.get("action", "")
    
    if verbose:
        print(f"\n  🔧 Tool: {tool_name}")
        print(f"     Action: {action}")
        if "coordinate" in tool_input:
            print(f"     Coordinate: {tool_input['coordinate']}")
        if "text" in tool_input:
            print(f"     Text: {repr(tool_input['text'])[:80]}")
        if "command" in tool_input:
            print(f"     Command: {tool_input['command'][:80]}")

    # NOTE: In a production implementation, you'd drive actual input here.
    # Reference: https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo
    # 
    # Example with pyautogui:
    #   import pyautogui
    #   if action == "left_click":
    #       pyautogui.click(tool_input["coordinate"][0], tool_input["coordinate"][1])
    #   elif action == "type":
    #       pyautogui.typewrite(tool_input["text"], interval=0.05)
    #   elif action == "screenshot":
    #       return capture_screenshot()  # return new screenshot

    if action == "screenshot":
        # Return an actual screenshot when requested
        return capture_screenshot()

    # For all other actions, return success and a fresh screenshot
    time.sleep(0.5)  # Simulate action time
    return capture_screenshot()


# ─── Main agent loop ──────────────────────────────────────────────────────────

def run_computer_use_task(task: str, verbose: bool = False, dry_run: bool = False) -> None:
    """Run a computer use task through Claude's agent loop."""
    
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set. Add it to .env or your environment.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print(f"\n{'='*60}")
    print(f"  Task: {task}")
    print(f"  Model: {MODEL}")
    print(f"  Started: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")

    if dry_run:
        print("[DRY RUN] Would send to Anthropic API:")
        print(json.dumps({
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "tools": [t["type"] for t in COMPUTER_USE_TOOLS],
            "messages": [{"role": "user", "content": task}]
        }, indent=2))
        return

    # Initial screenshot
    print("📸 Capturing initial screen state...")
    screenshot_b64 = capture_screenshot()

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": screenshot_b64,
                    },
                },
                {
                    "type": "text",
                    "text": task,
                },
            ],
        }
    ]

    iteration = 0
    while iteration < MAX_ITERATIONS:
        iteration += 1
        print(f"\n[Step {iteration}/{MAX_ITERATIONS}] Querying Claude...")

        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            tools=COMPUTER_USE_TOOLS,
            messages=messages,
            betas=["computer-use-2024-10-22"],
        )

        if verbose:
            print(f"  Stop reason: {response.stop_reason}")
            print(f"  Content blocks: {len(response.content)}")

        # Collect assistant turn
        messages.append({"role": "assistant", "content": response.content})

        # Handle tool use
        tool_results = []
        for block in response.content:
            if block.type == "text":
                print(f"\n💬 Claude: {block.text}")
            elif block.type == "tool_use":
                print(f"\n⚡ Action: {block.name} → {block.input.get('action', '')}")
                result = execute_tool(block.name, block.input, verbose=verbose)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": result,
                            },
                        }
                    ],
                })

        if response.stop_reason == "end_turn":
            print(f"\n{'='*60}")
            print(f"  ✅ Task complete after {iteration} step(s)")
            print(f"  Finished: {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}\n")
            break

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            # No tools used and not end_turn — unexpected, bail out
            print("\n⚠ No tool calls and stop_reason is not end_turn. Stopping.")
            break
    else:
        print(f"\n⚠ Reached maximum iterations ({MAX_ITERATIONS}). Task may be incomplete.")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude computer use API demo — AIStackInsights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python claude_computer_use_api.py --task "Open TextEdit and write Hello from Claude"
  python claude_computer_use_api.py --task "Take a screenshot and describe what you see" --verbose
  python claude_computer_use_api.py --dry-run
        """,
    )
    parser.add_argument("--task", type=str, default="Take a screenshot and describe what you see on screen.")
    parser.add_argument("--verbose", action="store_true", help="Print detailed tool call info")
    parser.add_argument("--dry-run", action="store_true", help="Print request without calling API")
    args = parser.parse_args()

    run_computer_use_task(task=args.task, verbose=args.verbose, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
