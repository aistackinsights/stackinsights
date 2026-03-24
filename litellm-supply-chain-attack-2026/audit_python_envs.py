#!/usr/bin/env python3
"""
audit_python_envs.py

Scans a directory tree (default: your home directory) for the malicious
litellm_init.pth file planted by the March 24, 2026 LiteLLM supply chain attack.

This script finds the malicious file across ALL Python environments on a machine:
  - System Python site-packages
  - Virtual environments (.venv, venv, env)
  - conda environments
  - uv environments
  - Any other Python installation under the scan root

Usage:
  python3 audit_python_envs.py              # scans home directory
  python3 audit_python_envs.py /path/to/scan

Reference: https://github.com/BerriAI/litellm/issues/24518
"""

import os
import hashlib
import sys
from pathlib import Path

MALICIOUS_PTH = "litellm_init.pth"
KNOWN_BAD_SHA256 = "ceNa7wMJnNHy1kRnNCcwJaFjWX3pORLfMh7xGL8TUjg"

# Directories to skip for speed (won't contain Python site-packages)
SKIP_DIRS = {
    ".git",
    ".cache",
    "node_modules",
    "__pycache__",
    ".npm",
    ".cargo",
    ".rustup",
    ".local/share/Trash",
}


def file_sha256(path: str) -> str:
    """Compute SHA-256 of a file without loading it fully into memory."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_directory(root: str) -> list:
    """
    Walk root recursively, returning a list of (path, sha256, is_known_bad)
    tuples for every file named litellm_init.pth that is found.
    """
    hits = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        if MALICIOUS_PTH in filenames:
            full_path = os.path.join(dirpath, MALICIOUS_PTH)
            try:
                sha = file_sha256(full_path)
                is_known_bad = sha == KNOWN_BAD_SHA256
                hits.append((full_path, sha, is_known_bad))
            except (PermissionError, OSError) as e:
                hits.append((full_path, f"UNREADABLE ({e})", False))

        # Prune directories that are safe to skip
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".")
            or d in {".venv", ".conda", ".pyenv"}  # keep hidden Python dirs
        ]

    return hits


def print_results(results: list) -> None:
    if not results:
        print("✅  No malicious .pth files found.")
        return

    print(f"⚠️   Found {len(results)} suspicious file(s):\n")
    for path, sha, is_known_bad in results:
        if is_known_bad:
            status = "CONFIRMED MALICIOUS"
        elif "UNREADABLE" in sha:
            status = "UNREADABLE — treat as suspicious"
        else:
            status = "UNKNOWN — inspect manually"

        print(f"  [{status}]")
        print(f"  Path:   {path}")
        print(f"  SHA256: {sha}")
        print()

    print("=" * 60)
    print("ACTION REQUIRED:")
    print("  1. Delete all flagged files.")
    print("  2. Rotate ALL credentials immediately:")
    print("     - LLM API keys (OpenAI, Anthropic, Google, etc.)")
    print("     - Cloud credentials (AWS, GCP, Azure)")
    print("     - SSH keypairs")
    print("     - GitHub/GitLab tokens")
    print("     - Kubernetes service account tokens")
    print("     - Database passwords")
    print("  3. Monitor for unauthorized access.")
    print()
    print("Full incident details: https://github.com/BerriAI/litellm/issues/24518")


if __name__ == "__main__":
    scan_root = sys.argv[1] if len(sys.argv) > 1 else str(Path.home())
    print(f"Scanning {scan_root} for {MALICIOUS_PTH}...")
    print(f"Known malicious SHA256: {KNOWN_BAD_SHA256}\n")

    results = scan_directory(scan_root)
    print_results(results)
