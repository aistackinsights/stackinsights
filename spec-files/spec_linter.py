#!/usr/bin/env python3
"""
spec_linter.py — Validate a CLAUDE.md or AGENTS.md spec file.

Checks for structural completeness, token efficiency, and quality of
anti-pattern rules and response style guidance.

Usage:
    python spec_linter.py CLAUDE.md
    python spec_linter.py AGENTS.md
    python spec_linter.py --strict CLAUDE.md   # exit 1 if score < 80
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    level: str          # "error", "warning", "info"
    code: str           # short machine-readable id
    message: str
    suggestion: str = ""
    penalty: int = 0    # points deducted from 100


@dataclass
class LintResult:
    score: int
    findings: list[Finding] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_file_length(lines: list[str]) -> list[Finding]:
    """Long files hurt token efficiency and agent attention."""
    n = len(lines)
    findings = []
    if n > 300:
        findings.append(Finding(
            level="error",
            code="TOO_LONG",
            message=f"File is {n} lines — far too long (>300). Agents will miss rules buried at the bottom.",
            suggestion="Split into focused sections or move low-priority content to a separate reference file.",
            penalty=20,
        ))
    elif n > 200:
        findings.append(Finding(
            level="warning",
            code="GETTING_LONG",
            message=f"File is {n} lines (>200). Token efficiency starts to degrade above 200 lines.",
            suggestion="Trim duplicate or vague rules. Keep only what an agent actually needs to know.",
            penalty=10,
        ))
    elif n < 20:
        findings.append(Finding(
            level="warning",
            code="TOO_SHORT",
            message=f"File is only {n} lines. This is unlikely to provide meaningful guidance.",
            suggestion="Add Stack, Commands, Conventions, and Response Style sections.",
            penalty=10,
        ))
    return findings


def check_required_sections(content: str) -> list[Finding]:
    """Ensure the file contains the sections agents rely on most."""
    findings = []

    required = [
        (
            r"##\s+stack",
            "MISSING_STACK",
            "No Stack section found.",
            "Add a ## Stack section listing your language, framework, and key library versions.",
            15,
        ),
        (
            r"##\s+(conventions|rules|guidelines|coding\s+style)",
            "MISSING_CONVENTIONS",
            "No Conventions / Coding Style section found.",
            "Add a ## Conventions section with naming, import, and style rules.",
            10,
        ),
        (
            r"##\s+commands",
            "MISSING_COMMANDS",
            "No Commands section found.",
            "Add a ## Commands section with exact build, test, and lint commands.",
            10,
        ),
    ]

    for pattern, code, message, suggestion, penalty in required:
        if not re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            findings.append(Finding(
                level="error",
                code=code,
                message=message,
                suggestion=suggestion,
                penalty=penalty,
            ))

    return findings


def check_anti_patterns(content: str) -> list[Finding]:
    """Check for the presence and quality of anti-pattern / 'Never do this' rules."""
    findings = []

    # Look for an anti-pattern section
    has_section = bool(re.search(
        r"##\s+(anti.?patterns?|never|forbidden|do\s+not|avoid|pitfalls)",
        content,
        re.IGNORECASE | re.MULTILINE,
    ))

    # Also accept inline "Never" bullet rules anywhere in the doc
    never_bullets = re.findall(
        r"[-*]\s+.{0,10}(never|do not|don't|avoid|forbidden).{0,80}",
        content,
        re.IGNORECASE,
    )

    if not has_section and len(never_bullets) < 2:
        findings.append(Finding(
            level="warning",
            code="NO_ANTI_PATTERNS",
            message="No anti-pattern / 'Never do this' rules found.",
            suggestion=(
                "Add a ## Anti-Patterns section. Example: "
                "'Never use `any` — fix the type instead.' "
                "These are the rules agents are most likely to violate without explicit guidance."
            ),
            penalty=15,
        ))
    elif not has_section and len(never_bullets) >= 2:
        findings.append(Finding(
            level="info",
            code="INLINE_ANTI_PATTERNS",
            message=f"Found {len(never_bullets)} inline 'never/avoid' rules but no dedicated Anti-Patterns section.",
            suggestion="Consider grouping them under a ## Anti-Patterns heading for clarity.",
            penalty=0,
        ))

    return findings


def check_response_style(content: str) -> list[Finding]:
    """Check for a Response Style / output behavior section."""
    findings = []

    has_section = bool(re.search(
        r"##\s+(response\s+style|output\s+(style|behavior|format)|communication|tone)",
        content,
        re.IGNORECASE | re.MULTILINE,
    ))

    # Inline signals
    style_signals = re.findall(
        r"(no preamble|no sycoph|no summar|be direct|concise|skip.*greet|don.t restate)",
        content,
        re.IGNORECASE,
    )

    if not has_section and not style_signals:
        findings.append(Finding(
            level="warning",
            code="NO_RESPONSE_STYLE",
            message="No Response Style / output behavior guidance found.",
            suggestion=(
                "Add a ## Response Style section. At minimum: "
                "'No preamble. No sycophancy. No unnecessary summaries. Minimal comments. Be direct.'"
            ),
            penalty=10,
        ))

    return findings


def check_stack_vagueness(content: str) -> list[Finding]:
    """Warn if the stack section names technologies without versions."""
    findings = []

    # Find the stack section
    stack_match = re.search(
        r"##\s+stack\s*\n(.*?)(?=\n##\s|\Z)",
        content,
        re.IGNORECASE | re.DOTALL,
    )
    if not stack_match:
        return findings  # Already caught by check_required_sections

    stack_block = stack_match.group(1)

    # Technologies that should have versions
    version_sensitive = [
        "react", "next", "vue", "angular", "svelte", "nuxt",
        "django", "flask", "fastapi",
        "typescript", "node", "python", "go", "rust",
        "prisma", "sqlalchemy", "mongoose",
    ]

    vague_entries = []
    for tech in version_sensitive:
        # Check if the tech is mentioned but has no version-like string nearby
        pattern = rf"\b{re.escape(tech)}\b[^\n]{{0,60}}"
        matches = re.findall(pattern, stack_block, re.IGNORECASE)
        for match in matches:
            # Version pattern: digits with dots, or "v\d", or "latest"
            if not re.search(r"\d+\.\d+|\bv\d|\blatest\b", match, re.IGNORECASE):
                vague_entries.append(tech.capitalize())
                break

    if vague_entries:
        unique = list(dict.fromkeys(vague_entries))  # deduplicate, preserve order
        findings.append(Finding(
            level="warning",
            code="VAGUE_STACK",
            message=f"Stack entries without versions: {', '.join(unique)}.",
            suggestion=(
                "Include version numbers in your Stack section. "
                "'React 18.3' is far more useful to an agent than just 'React'. "
                "Agents use versions to pick the correct APIs and avoid deprecated patterns."
            ),
            penalty=5,
        ))

    return findings


def check_placeholder_content(content: str, filename: str) -> list[Finding]:
    """Warn if the file still has obvious placeholder / template text."""
    findings = []

    placeholders = [
        r"\[Project Name\]",
        r"FILL\s+IN",
        r"_\(describe purpose\)_",
        r"_\(Fill in",
        r"auto-generated by generate_claude_md\.py",
    ]

    found = []
    for pattern in placeholders:
        if re.search(pattern, content, re.IGNORECASE):
            found.append(pattern.replace(r"\_", "_").replace("\\", ""))

    if found:
        findings.append(Finding(
            level="warning",
            code="PLACEHOLDER_CONTENT",
            message=f"File contains {len(found)} placeholder(s) that haven't been filled in.",
            suggestion="Review and replace all placeholder text before using this file with an agent.",
            penalty=10,
        ))

    return findings


def check_commands_have_examples(content: str) -> list[Finding]:
    """Warn if commands section exists but lacks actual shell commands."""
    findings = []

    commands_match = re.search(
        r"##\s+commands?\s*\n(.*?)(?=\n##\s|\Z)",
        content,
        re.IGNORECASE | re.DOTALL,
    )
    if not commands_match:
        return findings

    block = commands_match.group(1)
    # A useful commands section has code fences or obvious shell commands
    has_code = "```" in block or re.search(r"^\s*(npm|pnpm|yarn|pip|cargo|go|make|python|node)\b", block, re.MULTILINE)

    if not has_code:
        findings.append(Finding(
            level="warning",
            code="COMMANDS_MISSING_EXAMPLES",
            message="Commands section exists but doesn't contain runnable shell commands.",
            suggestion="Add a ```bash code block with the exact commands agents should run.",
            penalty=5,
        ))

    return findings


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def lint(path: Path) -> LintResult:
    content = path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    all_findings: list[Finding] = []
    all_findings += check_file_length(lines)
    all_findings += check_required_sections(content)
    all_findings += check_anti_patterns(content)
    all_findings += check_response_style(content)
    all_findings += check_stack_vagueness(content)
    all_findings += check_placeholder_content(content, path.name)
    all_findings += check_commands_have_examples(content)

    total_penalty = sum(f.penalty for f in all_findings)
    score = max(0, 100 - total_penalty)

    return LintResult(score=score, findings=all_findings)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

LEVEL_ICON = {"error": "✖", "warning": "⚠", "info": "ℹ"}
LEVEL_ORDER = {"error": 0, "warning": 1, "info": 2}


def render(result: LintResult, path: Path) -> str:
    lines = []
    lines.append(f"\n📋  Linting: {path}")
    lines.append(f"{'─' * 50}")

    if not result.findings:
        lines.append("✅  No issues found — perfect score!")
    else:
        sorted_findings = sorted(result.findings, key=lambda f: LEVEL_ORDER[f.level])
        for f in sorted_findings:
            icon = LEVEL_ICON[f.level]
            lines.append(f"\n{icon}  [{f.code}] {f.message}")
            if f.suggestion:
                lines.append(f"   → {f.suggestion}")
            if f.penalty:
                lines.append(f"   Penalty: -{f.penalty} points")

    lines.append(f"\n{'─' * 50}")

    # Score with emoji rating
    score = result.score
    if score >= 90:
        grade = "🟢  Excellent"
    elif score >= 75:
        grade = "🟡  Good — minor improvements needed"
    elif score >= 50:
        grade = "🟠  Needs work"
    else:
        grade = "🔴  Poor — significant gaps"

    lines.append(f"Score: {score}/100  {grade}")

    # Prioritised suggestions
    errors = [f for f in result.findings if f.level == "error"]
    warnings = [f for f in result.findings if f.level == "warning"]
    if errors or warnings:
        lines.append("\nTop improvements:")
        for f in (errors + warnings)[:3]:
            lines.append(f"  • {f.suggestion or f.message}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Lint a CLAUDE.md or AGENTS.md spec file."
    )
    parser.add_argument("file", help="Path to CLAUDE.md or AGENTS.md")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if score < 80 (useful in CI)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output findings as JSON",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(2)

    result = lint(path)

    if args.json:
        import json
        data = {
            "score": result.score,
            "findings": [
                {
                    "level": f.level,
                    "code": f.code,
                    "message": f.message,
                    "suggestion": f.suggestion,
                    "penalty": f.penalty,
                }
                for f in result.findings
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(render(result, path))

    if args.strict and result.score < 80:
        sys.exit(1)


if __name__ == "__main__":
    main()
