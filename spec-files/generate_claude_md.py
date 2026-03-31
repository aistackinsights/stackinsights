#!/usr/bin/env python3
"""
generate_claude_md.py — Auto-generate a CLAUDE.md for any project.

Inspects package.json, requirements.txt, Cargo.toml, or go.mod to detect the
tech stack, lists top-level directories for architecture context, and reads
any existing README.md. Outputs a well-structured CLAUDE.md.

Usage:
    python generate_claude_md.py [--dir /path/to/project] [--write]

Options:
    --dir PATH   Project root to inspect (default: current directory)
    --write      Save output to CLAUDE.md in the project root instead of stdout
"""

import argparse
import json
import os
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_file(path: str) -> str | None:
    """Return file contents or None if not found."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except FileNotFoundError:
        return None


def top_level_dirs(root: str) -> list[str]:
    """Return top-level directory names (excluding hidden and common noise)."""
    skip = {
        ".git", ".github", "node_modules", "__pycache__", ".venv", "venv",
        "env", ".env", "dist", "build", "target", ".idea", ".vscode",
        ".mypy_cache", ".pytest_cache", "coverage",
    }
    dirs = []
    try:
        for entry in sorted(os.scandir(root), key=lambda e: e.name.lower()):
            if entry.is_dir() and entry.name not in skip and not entry.name.startswith("."):
                dirs.append(entry.name)
    except PermissionError:
        pass
    return dirs


def top_level_files(root: str) -> list[str]:
    """Return top-level file names (non-hidden)."""
    files = []
    try:
        for entry in sorted(os.scandir(root), key=lambda e: e.name.lower()):
            if entry.is_file() and not entry.name.startswith("."):
                files.append(entry.name)
    except PermissionError:
        pass
    return files


# ---------------------------------------------------------------------------
# Stack detection
# ---------------------------------------------------------------------------

def detect_stack_from_package_json(root: str) -> dict:
    """Parse package.json for framework/runtime info and scripts."""
    path = os.path.join(root, "package.json")
    raw = read_file(path)
    if not raw:
        return {}

    try:
        pkg = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    stack = {}
    all_deps = {
        **pkg.get("dependencies", {}),
        **pkg.get("devDependencies", {}),
    }

    # Runtime / language
    engines = pkg.get("engines", {})
    if "node" in engines:
        stack["Node.js"] = engines["node"]

    # Frameworks
    framework_map = {
        "next": "Next.js",
        "react": "React",
        "vue": "Vue",
        "@angular/core": "Angular",
        "svelte": "Svelte",
        "express": "Express",
        "fastify": "Fastify",
        "koa": "Koa",
        "hono": "Hono",
        "remix": "Remix",
        "nuxt": "Nuxt",
        "gatsby": "Gatsby",
        "astro": "Astro",
    }
    for dep, label in framework_map.items():
        if dep in all_deps:
            stack[label] = all_deps[dep].lstrip("^~")

    # TypeScript
    if "typescript" in all_deps:
        stack["TypeScript"] = all_deps["typescript"].lstrip("^~")

    # Test runners
    for runner in ("jest", "vitest", "mocha", "jasmine", "playwright", "cypress"):
        if runner in all_deps:
            stack[runner.capitalize()] = all_deps[runner].lstrip("^~")

    # Package manager hint
    if os.path.exists(os.path.join(root, "pnpm-lock.yaml")):
        stack["Package manager"] = "pnpm"
    elif os.path.exists(os.path.join(root, "yarn.lock")):
        stack["Package manager"] = "yarn"
    else:
        stack["Package manager"] = "npm"

    stack["_scripts"] = pkg.get("scripts", {})
    stack["_name"] = pkg.get("name", "")
    stack["_description"] = pkg.get("description", "")
    return stack


def detect_stack_from_requirements(root: str) -> dict:
    """Parse requirements.txt for Python dependencies."""
    for fname in ("requirements.txt", "requirements-dev.txt", "pyproject.toml"):
        path = os.path.join(root, fname)
        raw = read_file(path)
        if not raw:
            continue

        stack = {"Python": "3.x"}
        highlights = {
            "django": "Django",
            "flask": "Flask",
            "fastapi": "FastAPI",
            "starlette": "Starlette",
            "sqlalchemy": "SQLAlchemy",
            "pydantic": "Pydantic",
            "celery": "Celery",
            "pytest": "pytest",
            "black": "Black (formatter)",
            "ruff": "Ruff (linter)",
            "mypy": "mypy",
        }
        for line in raw.splitlines():
            pkg_name = line.split("==")[0].split(">=")[0].split("[")[0].strip().lower()
            if pkg_name in highlights:
                stack[highlights[pkg_name]] = line.strip()

        return stack
    return {}


def detect_stack_from_cargo(root: str) -> dict:
    """Minimal Cargo.toml detection."""
    path = os.path.join(root, "Cargo.toml")
    raw = read_file(path)
    if not raw:
        return {}
    stack = {"Language": "Rust"}
    for line in raw.splitlines():
        if line.startswith("edition"):
            edition = line.split("=")[-1].strip().strip('"')
            stack["Rust edition"] = edition
    return stack


def detect_stack_from_gomod(root: str) -> dict:
    """Minimal go.mod detection."""
    path = os.path.join(root, "go.mod")
    raw = read_file(path)
    if not raw:
        return {}
    stack = {"Language": "Go"}
    for line in raw.splitlines():
        if line.startswith("go "):
            stack["Go version"] = line.split()[1]
    return stack


def detect_stack(root: str) -> tuple[dict, str]:
    """Return (stack_dict, ecosystem) for the project."""
    stack = detect_stack_from_package_json(root)
    if stack:
        return stack, "node"

    stack = detect_stack_from_requirements(root)
    if stack:
        return stack, "python"

    stack = detect_stack_from_cargo(root)
    if stack:
        return stack, "rust"

    stack = detect_stack_from_gomod(root)
    if stack:
        return stack, "go"

    return {}, "unknown"


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def build_stack_section(stack: dict, ecosystem: str) -> str:
    lines = ["## Stack\n"]
    skip_keys = {"_scripts", "_name", "_description"}
    for key, val in stack.items():
        if key in skip_keys:
            continue
        lines.append(f"- **{key}**: {val}")
    if not lines[1:]:
        lines.append("- _(Could not auto-detect — fill in manually)_")
    return "\n".join(lines)


def build_architecture_section(dirs: list[str], files: list[str]) -> str:
    lines = ["## Architecture\n"]
    if dirs:
        lines.append("### Top-level directories\n")
        for d in dirs:
            lines.append(f"- `{d}/` — _(describe purpose)_")
    notable = [f for f in files if f in (
        "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
        ".env.example", "Makefile", "justfile", "turbo.json",
        "nx.json", "lerna.json",
    )]
    if notable:
        lines.append("\n### Notable config files\n")
        for f in notable:
            lines.append(f"- `{f}`")
    return "\n".join(lines)


def build_commands_section(stack: dict, ecosystem: str) -> str:
    lines = ["## Commands\n"]

    scripts = stack.get("_scripts", {})
    if scripts:
        lines.append("### npm / pnpm / yarn scripts\n")
        lines.append("```bash")
        for name, cmd in scripts.items():
            lines.append(f"# {name}")
            lines.append(f"npm run {name}")
        lines.append("```")
    elif ecosystem == "python":
        lines.append("```bash")
        lines.append("# Install deps")
        lines.append("pip install -r requirements.txt")
        lines.append("")
        lines.append("# Run tests")
        lines.append("pytest")
        lines.append("")
        lines.append("# Lint")
        lines.append("ruff check .")
        lines.append("```")
    elif ecosystem == "rust":
        lines.append("```bash")
        lines.append("cargo build")
        lines.append("cargo test")
        lines.append("cargo clippy")
        lines.append("```")
    elif ecosystem == "go":
        lines.append("```bash")
        lines.append("go build ./...")
        lines.append("go test ./...")
        lines.append("go vet ./...")
        lines.append("```")
    else:
        lines.append("_(Fill in your build/test/lint commands)_")

    return "\n".join(lines)


RESPONSE_STYLE_SECTION = """\
## Response Style

- **No preamble.** Don't restate the task before doing it.
- **No sycophancy.** Skip "Great question!" and "Sure, I'd be happy to help!"
- **No summaries.** Don't explain what you just did after doing it.
- **Minimal comments.** Only comment code when the logic is non-obvious.
- **Be direct.** If a change is small, just make it — don't ask for permission.
"""


def build_readme_context_section(readme: str | None, name: str, description: str) -> str:
    lines = ["## Project Overview\n"]
    if name:
        lines.append(f"**Name:** {name}\n")
    if description:
        lines.append(f"{description}\n")
    if readme:
        # Grab first non-empty paragraph from README
        paragraphs = [p.strip() for p in readme.split("\n\n") if p.strip()]
        for para in paragraphs[:3]:
            # Skip headings that just repeat the project name
            if para.startswith("#"):
                continue
            lines.append(para)
            break
    if len(lines) == 1:
        lines.append("_(Fill in a brief description of what this project does)_")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate(root: str) -> str:
    root = os.path.abspath(root)
    stack, ecosystem = detect_stack(root)
    dirs = top_level_dirs(root)
    files = top_level_files(root)
    readme = read_file(os.path.join(root, "README.md"))

    name = stack.get("_name", os.path.basename(root))
    description = stack.get("_description", "")

    sections = [
        f"# CLAUDE.md — {name or os.path.basename(root)}\n",
        "> Auto-generated by generate_claude_md.py — review and customise before committing.\n",
        build_readme_context_section(readme, name, description),
        "",
        build_stack_section(stack, ecosystem),
        "",
        build_architecture_section(dirs, files),
        "",
        build_commands_section(stack, ecosystem),
        "",
        RESPONSE_STYLE_SECTION,
    ]

    return "\n".join(sections)


def main():
    parser = argparse.ArgumentParser(
        description="Auto-generate a CLAUDE.md for a project."
    )
    parser.add_argument(
        "--dir",
        default=".",
        metavar="PATH",
        help="Project root to inspect (default: current directory)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write output to CLAUDE.md in the project root instead of stdout",
    )
    args = parser.parse_args()

    output = generate(args.dir)

    if args.write:
        dest = os.path.join(os.path.abspath(args.dir), "CLAUDE.md")
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"Written to {dest}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
