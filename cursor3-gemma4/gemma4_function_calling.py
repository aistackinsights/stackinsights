"""
Gemma 4 Function-Calling Agent Template
========================================
Uses Google AI's OpenAI-compatible endpoint with the `openai` Python SDK.
Demonstrates tool definition, multi-turn conversation, and result handling.

Usage:
    GOOGLE_API_KEY=your_key_here python gemma4_function_calling.py

Requirements:
    pip install openai
"""

import json
import os
import sys
from openai import OpenAI

# ── Client setup ─────────────────────────────────────────────────────────────

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY environment variable is not set.")
    sys.exit(1)

client = OpenAI(
    api_key=GOOGLE_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

MODEL = "gemma-3-27b-it"  # Use gemma-3-27b-it via Google AI Studio


# ── Tool definitions (JSON Schema) ───────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": (
                "Get the current weather for a given location. "
                "Returns temperature, conditions, and humidity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": (
                            "City and country, e.g. 'San Francisco, US' "
                            "or 'London, UK'"
                        ),
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": (
                "Search the local codebase for files or symbols matching a query. "
                "Returns a list of matching file paths and line numbers."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search term, symbol name, or pattern to look for.",
                    },
                    "path": {
                        "type": "string",
                        "description": (
                            "Directory path to search within. "
                            "Defaults to the current working directory."
                        ),
                        "default": ".",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_github_issue",
            "description": (
                "Create a new GitHub issue in the current repository. "
                "Returns the issue number and URL."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "A short, descriptive title for the issue.",
                    },
                    "body": {
                        "type": "string",
                        "description": (
                            "Detailed description of the issue in Markdown format."
                        ),
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional list of label names to attach, "
                            "e.g. ['bug', 'good first issue']"
                        ),
                    },
                },
                "required": ["title", "body"],
            },
        },
    },
]


# ── Simulated tool implementations ───────────────────────────────────────────

def get_weather(location: str) -> dict:
    """Simulated weather lookup (replace with a real API call)."""
    return {
        "location": location,
        "temperature_c": 18,
        "conditions": "Partly cloudy",
        "humidity_pct": 62,
    }


def search_codebase(query: str, path: str = ".") -> dict:
    """Simulated codebase search (replace with ripgrep or similar)."""
    return {
        "query": query,
        "path": path,
        "matches": [
            {"file": "src/auth/login.py", "line": 42, "snippet": f"def {query}(user):"},
            {"file": "tests/test_auth.py", "line": 17, "snippet": f"# TODO: test {query}"},
        ],
    }


def create_github_issue(title: str, body: str, labels: list[str] | None = None) -> dict:
    """Simulated GitHub issue creation (replace with PyGithub or gh CLI)."""
    issue_number = 99  # stub
    return {
        "issue_number": issue_number,
        "title": title,
        "labels": labels or [],
        "url": f"https://github.com/your-org/your-repo/issues/{issue_number}",
        "status": "created",
    }


TOOL_REGISTRY = {
    "get_weather": get_weather,
    "search_codebase": search_codebase,
    "create_github_issue": create_github_issue,
}


# ── Tool dispatch ─────────────────────────────────────────────────────────────

def dispatch_tool_call(tool_call) -> str:
    """Execute a tool call returned by the model and return the result as JSON."""
    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as exc:
        return json.dumps({"error": f"Failed to parse tool arguments: {exc}"})

    handler = TOOL_REGISTRY.get(name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        result = handler(**args)
        return json.dumps(result)
    except TypeError as exc:
        return json.dumps({"error": f"Tool call failed: {exc}"})


# ── Multi-turn agent loop ─────────────────────────────────────────────────────

def run_agent(user_message: str) -> None:
    """Run a multi-turn agentic conversation until the model stops calling tools."""
    print(f"\n{'='*60}")
    print(f"User: {user_message}")
    print(f"{'='*60}\n")

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful developer assistant. "
                "Use the provided tools when they can help answer the question. "
                "Always be concise and accurate."
            ),
        },
        {"role": "user", "content": user_message},
    ]

    turn = 0
    max_turns = 10  # safety limit

    while turn < max_turns:
        turn += 1
        print(f"[Turn {turn}] Calling model...")

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        except Exception as exc:
            print(f"API error: {exc}")
            break

        message = response.choices[0].message

        # Append assistant message (may contain tool_calls)
        messages.append(message)

        # If no tool calls, we're done
        if not message.tool_calls:
            print(f"\nAssistant: {message.content}")
            break

        # Process each tool call
        for tool_call in message.tool_calls:
            fn_name = tool_call.function.name
            print(f"  → Tool call: {fn_name}({tool_call.function.arguments})")
            result_json = dispatch_tool_call(tool_call)
            print(f"  ← Result: {result_json}")

            # Feed tool result back into the conversation
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_json,
                }
            )
    else:
        print("Warning: reached maximum turn limit without a final response.")


# ── Demo conversations ────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 1. Weather query
    run_agent("What's the weather like in Tokyo right now?")

    # 2. Codebase search
    run_agent(
        "Find where the `authenticate_user` function is defined in our codebase "
        "and then create a GitHub issue to add unit tests for it."
    )

    # 3. Multi-tool chain
    run_agent(
        "Check the weather in London and search for any weather-related code "
        "in the src/ directory."
    )
