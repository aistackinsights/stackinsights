# query_claude_code.py
import subprocess, json, sys

def run_claude(prompt: str, cwd: str = ".") -> str:
    result = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)["result"]

# Example: auto-generate changelogs in CI
if __name__ == "__main__":
    diff = subprocess.run(["git", "diff", "HEAD~1"], capture_output=True, text=True).stdout
    changelog = run_claude(f"Write a user-facing changelog entry for this diff:\n{diff}")
    print(changelog)
