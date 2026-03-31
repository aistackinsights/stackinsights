# spec-files — CLAUDE.md Companion Scripts

Companion tools for the article  
**[CLAUDE.md & Spec Files: The Complete Guide to AI Coding Agents](https://aistackinsights.ai/blog/claude-md-spec-files-ai-coding-agents-guide)**

These scripts help you create, template, and validate spec files (`CLAUDE.md`, `AGENTS.md`) for AI coding agents like Claude Code, Codex, Cursor, and Copilot Workspace.

---

## Files

| File | Purpose |
|------|---------|
| `generate_claude_md.py` | Auto-generate a `CLAUDE.md` by inspecting your project |
| `agents_md_template.md` | Ready-to-use `AGENTS.md` template for multi-agent workflows |
| `spec_linter.py` | Validate and score a `CLAUDE.md` or `AGENTS.md` file |

---

## Quick Install

No external dependencies required — all scripts use Python's standard library only.

```bash
# Python 3.10+ required (uses modern type hints)
python --version

# pathlib, json, re, argparse are all stdlib — nothing to install
# Optional: if you want to double-check
pip show pathlib  # it's built in since Python 3.4
```

---

## Usage

### `generate_claude_md.py` — Auto-generate a CLAUDE.md

Inspect any project and generate a starter `CLAUDE.md`:

```bash
# Print to stdout (review before saving)
python generate_claude_md.py --dir /path/to/your/project

# Save directly to CLAUDE.md in the project root
python generate_claude_md.py --dir /path/to/your/project --write

# Run in the current directory
python generate_claude_md.py --write
```

**What it detects automatically:**
- Tech stack from `package.json`, `requirements.txt`, `Cargo.toml`, or `go.mod`
- Package manager (npm / pnpm / yarn) from lock files
- `npm run` scripts from `package.json`
- Top-level directory structure for architecture mapping
- Project name and description from `package.json` or README

**Always review the output** — the generator gives you an 80% starting point, not a finished file.

---

### `spec_linter.py` — Lint a spec file

Validate and score your `CLAUDE.md` or `AGENTS.md`:

```bash
python spec_linter.py CLAUDE.md

python spec_linter.py AGENTS.md

# Strict mode: exit 1 if score < 80 (great for CI)
python spec_linter.py --strict CLAUDE.md

# Machine-readable JSON output
python spec_linter.py --json CLAUDE.md
```

**What it checks:**
- Required sections: Stack, Conventions, Commands, Anti-Patterns
- File length (> 200 lines starts hurting token efficiency)
- Presence of "Never do this" style anti-pattern rules
- Response Style / output behavior section
- Vague stack entries (e.g., "React" without a version number)
- Unfilled placeholder text

**Score guide:**

| Score | Grade |
|-------|-------|
| 90–100 | 🟢 Excellent |
| 75–89 | 🟡 Good — minor improvements needed |
| 50–74 | 🟠 Needs work |
| 0–49 | 🔴 Poor — significant gaps |

---

### `agents_md_template.md` — AGENTS.md starter template

Copy this file to your project root and fill it in:

```bash
cp agents_md_template.md /path/to/your/project/AGENTS.md
# Edit it, then validate:
python spec_linter.py /path/to/your/project/AGENTS.md
```

---

## Recommended CLAUDE.md Response Style Rules

Every spec file should include a **Response Style** section. These 5 rules eliminate the most common agent annoyances:

```markdown
## Response Style

1. **No preamble.** Don't restate the task or explain what you're about to do. Just do it.

2. **No sycophancy.** Skip "Great question!", "Certainly!", "Sure, I'd be happy to help!" 
   and all similar filler. Start with substance.

3. **No post-task summaries.** Don't explain what you just did after doing it. 
   The code/output speaks for itself.

4. **Minimal comments.** Only comment code when the logic is genuinely non-obvious. 
   Don't narrate what the code is doing — that's what the code is for.

5. **Be direct.** If a change is small and unambiguous, make it without asking for permission. 
   Surface blockers fast; don't spin wheels on things you can't resolve alone.
```

These rules work because they address the default behavior that makes AI agents feel slow and bureaucratic. Agents trained on human feedback tend toward excessive politeness and over-explanation — these rules override that.

---

## Related

- 📖 [Full article: CLAUDE.md & Spec Files Guide](https://aistackinsights.ai/blog/claude-md-spec-files-ai-coding-agents-guide)
- 🤖 [AI Stack Insights](https://aistackinsights.ai) — practical guides for building with AI agents
