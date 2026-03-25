#!/usr/bin/env python3
"""
detect_litellm_compromise.py
Cross-platform detection script for the LiteLLM supply chain attack.
Checks for the malicious litellm_init.pth file in all Python environments.
Article: https://aistackinsights.ai/blog/litellm-supply-chain-attack-2026
"""
import hashlib, sys
from pathlib import Path

MALICIOUS_SHA = "ceNa7wMJnNHy1kRnNCcwJaFjWX3pORLfMh7xGL8TUjg"

def check():
    print("=== LiteLLM Compromise Detector ===\n")
    found = False

    try:
        import site
        dirs = site.getsitepackages() + [site.getusersitepackages()]
    except Exception:
        import sysconfig
        dirs = [sysconfig.get_path("purelib"), sysconfig.get_path("platlib")]

    for d in dirs:
        p = Path(d) / "litellm_init.pth"
        if p.exists():
            sha = hashlib.sha256(p.read_bytes()).hexdigest()
            print(f"FOUND: {p}")
            print(f"  SHA256: {sha}")
            if sha == MALICIOUS_SHA:
                print("  STATUS: *** MALICIOUS - ROTATE ALL CREDENTIALS NOW ***")
            else:
                print("  STATUS: Unknown .pth file - investigate immediately")
            found = True

    try:
        import importlib.metadata
        version = importlib.metadata.version("litellm")
        print(f"\nInstalled litellm version: {version}")
        if version in ("1.82.7", "1.82.8"):
            print("CRITICAL: Compromised version installed - credential exfiltration occurred at startup")
            found = True
        else:
            print(f"Version {version} - not a known-malicious version (audit CI/CD history)")
    except importlib.metadata.PackageNotFoundError:
        print("\nLiteLLM not installed in this environment")

    print()
    if found:
        print("ACTION REQUIRED: https://aistackinsights.ai/blog/litellm-supply-chain-attack-2026")
    else:
        print("No indicators found. Still audit CI/CD logs for March 23-24 installs.")

if __name__ == "__main__":
    check()
