"""
mcp_server_template.py — Production-ready MCP server template
Companion script for: https://aistackinsights.ai/blog/context-engineering-developer-guide-2026

Exposes 3 tools:
  - get_schema        : Read a model definition from a Prisma schema file
  - get_recent_logs   : Return the last N lines from a log file
  - search_codebase   : Grep-style search across .ts/.tsx/.py files in a directory

Requirements:
    pip install mcp

Run:
    python mcp_server_template.py
"""

import asyncio
import json
import os
import re
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult,
    ListToolsResult,
    TextContent,
    Tool,
)

# ---------------------------------------------------------------------------
# Server initialization
# ---------------------------------------------------------------------------

server = Server("codebase-context-server")


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> ListToolsResult:
    return ListToolsResult(
        tools=[
            Tool(
                name="get_schema",
                description=(
                    "Read a Prisma schema file and return the definition for a "
                    "specific model. Useful for giving an LLM precise data-model "
                    "context without pasting the entire schema."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "schema_path": {
                            "type": "string",
                            "description": "Absolute or relative path to the Prisma schema file (e.g. ./prisma/schema.prisma)",
                        },
                        "model_name": {
                            "type": "string",
                            "description": "Name of the Prisma model to extract (case-sensitive, e.g. 'User')",
                        },
                    },
                    "required": ["schema_path", "model_name"],
                },
            ),
            Tool(
                name="get_recent_logs",
                description=(
                    "Return the last N lines from a log file. Ideal for surfacing "
                    "recent errors or warnings into the LLM context window."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "log_path": {
                            "type": "string",
                            "description": "Absolute or relative path to the log file",
                        },
                        "lines": {
                            "type": "integer",
                            "description": "Number of lines to return from the end of the file (default: 50)",
                            "default": 50,
                        },
                    },
                    "required": ["log_path"],
                },
            ),
            Tool(
                name="search_codebase",
                description=(
                    "Grep-style search across .ts, .tsx, and .py files in a directory. "
                    "Returns matching file paths, line numbers, and surrounding context."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Root directory to search (e.g. './src')",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Regex or literal string to search for",
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Whether the search is case-sensitive (default: false)",
                            "default": False,
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of matching lines to return (default: 30)",
                            "default": 30,
                        },
                    },
                    "required": ["directory", "pattern"],
                },
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    if name == "get_schema":
        return await _get_schema(arguments)
    elif name == "get_recent_logs":
        return await _get_recent_logs(arguments)
    elif name == "search_codebase":
        return await _search_codebase(arguments)
    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")],
            isError=True,
        )


async def _get_schema(args: dict) -> CallToolResult:
    schema_path = Path(args["schema_path"])
    model_name = args["model_name"]

    if not schema_path.exists():
        return CallToolResult(
            content=[TextContent(type="text", text=f"Schema file not found: {schema_path}")],
            isError=True,
        )

    text = schema_path.read_text(encoding="utf-8")

    # Extract the model block using a simple state machine
    lines = text.splitlines()
    in_model = False
    brace_depth = 0
    model_lines: list[str] = []

    for line in lines:
        if not in_model:
            # Match: model ModelName {
            if re.match(rf"^\s*model\s+{re.escape(model_name)}\s*{{", line):
                in_model = True
                brace_depth = line.count("{") - line.count("}")
                model_lines.append(line)
        else:
            brace_depth += line.count("{") - line.count("}")
            model_lines.append(line)
            if brace_depth <= 0:
                break

    if not model_lines:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Model '{model_name}' not found in {schema_path}")],
            isError=True,
        )

    return CallToolResult(
        content=[TextContent(type="text", text="\n".join(model_lines))]
    )


async def _get_recent_logs(args: dict) -> CallToolResult:
    log_path = Path(args["log_path"])
    n_lines = int(args.get("lines", 50))

    if not log_path.exists():
        return CallToolResult(
            content=[TextContent(type="text", text=f"Log file not found: {log_path}")],
            isError=True,
        )

    # Memory-efficient tail implementation
    with open(log_path, "rb") as f:
        # Seek from end
        try:
            f.seek(0, 2)
            file_size = f.tell()
            block_size = min(8192, file_size)
            collected: list[bytes] = []
            lines_found = 0
            pos = file_size

            while pos > 0 and lines_found <= n_lines:
                pos = max(0, pos - block_size)
                f.seek(pos)
                block = f.read(min(block_size, file_size - pos))
                collected.insert(0, block)
                lines_found += block.count(b"\n")

            content = b"".join(collected).decode("utf-8", errors="replace")
            tail = "\n".join(content.splitlines()[-n_lines:])
        except OSError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error reading log: {e}")],
                isError=True,
            )

    result = f"Last {n_lines} lines of {log_path}:\n\n{tail}"
    return CallToolResult(content=[TextContent(type="text", text=result)])


async def _search_codebase(args: dict) -> CallToolResult:
    directory = Path(args["directory"])
    pattern = args["pattern"]
    case_sensitive = args.get("case_sensitive", False)
    max_results = int(args.get("max_results", 30))

    if not directory.exists():
        return CallToolResult(
            content=[TextContent(type="text", text=f"Directory not found: {directory}")],
            isError=True,
        )

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Invalid regex pattern: {e}")],
            isError=True,
        )

    extensions = {".ts", ".tsx", ".py"}
    matches: list[str] = []

    for root, _, files in os.walk(directory):
        # Skip common noise directories
        root_path = Path(root)
        if any(part in {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}
               for part in root_path.parts):
            continue

        for filename in files:
            if Path(filename).suffix not in extensions:
                continue

            filepath = root_path / filename
            try:
                file_text = filepath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            for lineno, line in enumerate(file_text.splitlines(), start=1):
                if regex.search(line):
                    matches.append(f"{filepath}:{lineno}: {line.rstrip()}")
                    if len(matches) >= max_results:
                        break

            if len(matches) >= max_results:
                break

    if not matches:
        result = f"No matches found for '{pattern}' in {directory}"
    else:
        header = f"Found {len(matches)} match(es) for '{pattern}' in {directory}:\n\n"
        result = header + "\n".join(matches)
        if len(matches) == max_results:
            result += f"\n\n(Results truncated at {max_results}. Increase max_results or narrow your pattern.)"

    return CallToolResult(content=[TextContent(type="text", text=result)])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(main())
