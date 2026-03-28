"""
custom_skill_template.py
────────────────────────
Annotated template for building a custom DeerFlow 2.0 skill.

DeerFlow skills are discrete, reusable workflow modules that agents can load on demand.
A skill defines: its name/description, input schema, execution logic, and output format.
The lead agent selects skills based on task requirements and loads them into sub-agent contexts.

Article: https://aistackinsights.ai/blog/deerflow-2-superagent-developer-guide
Repo:    https://github.com/aistackinsights/stackinsights/tree/main/deerflow-2-superagent-developer-guide
DeerFlow repo: https://github.com/bytedance/deer-flow

To install this skill:
  1. Copy this file to deer-flow/backend/src/skills/
  2. Register it in deer-flow/backend/src/skills/__init__.py
  3. Restart the DeerFlow backend

Requirements (same as DeerFlow backend):
    pip install langchain-core pydantic
"""

from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


# ─── Input schema ─────────────────────────────────────────────────────────────
# Pydantic model defining what inputs your skill accepts.
# DeerFlow uses this schema to validate agent tool calls.

class MyCustomSkillInput(BaseModel):
    """Input schema for MyCustomSkill."""

    query: str = Field(
        description="The primary query or topic to process.",
        min_length=1,
        max_length=2000,
    )
    depth: int = Field(
        default=2,
        description="Depth of analysis: 1 = summary, 2 = standard, 3 = deep dive.",
        ge=1,
        le=3,
    )
    output_format: str = Field(
        default="markdown",
        description="Output format: 'markdown', 'json', or 'plain'.",
    )


# ─── Skill implementation ─────────────────────────────────────────────────────

class MyCustomSkill(BaseTool):
    """
    Template for a DeerFlow custom skill.

    Replace the class name, description, and _run logic with your own implementation.
    This template demonstrates: input validation, structured output, error handling,
    and the DeerFlow skill registration pattern.
    """

    name: str = "my_custom_skill"
    description: str = (
        "Processes a query and returns structured analysis. "
        "Use this skill when you need [describe your skill's purpose]. "
        "Input: a query string. Output: formatted analysis report."
    )
    args_schema: type[BaseModel] = MyCustomSkillInput
    return_direct: bool = False  # False = result feeds back to agent; True = returns to user

    def _run(self, query: str, depth: int = 2, output_format: str = "markdown") -> str:
        """
        Synchronous execution of the skill.
        Replace this with your actual logic.
        """
        try:
            # ── Your skill logic goes here ──────────────────────────────────
            #
            # Examples of what skills can do:
            #   - Call an external API
            #   - Query a database
            #   - Run a Python computation
            #   - Process files in the sandbox filesystem
            #   - Invoke a sub-agent for parallel work
            #
            # DeerFlow provides these utilities via the skill context:
            #   self.sandbox_exec(cmd)       # run bash in Docker sandbox
            #   self.read_file(path)         # read from sandbox filesystem
            #   self.write_file(path, data)  # write to sandbox filesystem
            #   self.web_search(query)       # built-in search (if configured)
            # ───────────────────────────────────────────────────────────────

            # Example: a simple analysis scaffold
            result = self._analyze(query, depth)

            if output_format == "json":
                return json.dumps(result, indent=2, ensure_ascii=False)
            elif output_format == "plain":
                return result.get("summary", "")
            else:
                return self._to_markdown(result, query)

        except Exception as e:
            # Always return a string — never raise from _run.
            # DeerFlow agents handle error strings gracefully.
            return f"Error in my_custom_skill: {type(e).__name__}: {e}"

    async def _arun(self, query: str, depth: int = 2, output_format: str = "markdown") -> str:
        """
        Async execution (DeerFlow prefers async for long-running skills).
        For I/O-bound work, implement this instead of _run.
        """
        # For simple skills, delegate to sync:
        return self._run(query, depth, output_format)

    # ─── Internal helpers ──────────────────────────────────────────────────────

    def _analyze(self, query: str, depth: int) -> dict[str, Any]:
        """
        Placeholder analysis logic.
        Replace with your actual implementation.
        """
        sections = ["Overview", "Key Points", "Analysis"]
        if depth >= 2:
            sections.append("Implications")
        if depth >= 3:
            sections.extend(["Deep Dive", "Technical Details", "Recommendations"])

        return {
            "query": query,
            "depth": depth,
            "summary": f"Analysis of: {query}",
            "sections": {s: f"[Content for {s} at depth {depth}]" for s in sections},
            "metadata": {
                "skill": self.name,
                "depth_level": depth,
                "section_count": len(sections),
            },
        }

    def _to_markdown(self, result: dict[str, Any], query: str) -> str:
        lines = [f"# Analysis: {query}\n"]
        for section, content in result.get("sections", {}).items():
            lines.append(f"## {section}\n")
            lines.append(f"{content}\n")
        return "\n".join(lines)


# ─── Skill registration helper ────────────────────────────────────────────────

def get_skill() -> MyCustomSkill:
    """
    Factory function called by DeerFlow's skill loader.
    Register this in backend/src/skills/__init__.py:

        from .my_custom_skill import get_skill as get_my_custom_skill
        SKILL_REGISTRY["my_custom_skill"] = get_my_custom_skill

    Then any agent can invoke it via:
        tool_call: { name: "my_custom_skill", args: { query: "...", depth: 2 } }
    """
    return MyCustomSkill()


# ─── Local test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test DeerFlow custom skill locally")
    parser.add_argument("--query", default="AI agent frameworks comparison 2026")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--format", default="markdown", dest="output_format")
    args = parser.parse_args()

    skill = get_skill()
    print(f"Skill: {skill.name}")
    print(f"Description: {skill.description}\n")
    print("─" * 60)
    result = skill._run(
        query=args.query,
        depth=args.depth,
        output_format=args.output_format
    )
    print(result)
