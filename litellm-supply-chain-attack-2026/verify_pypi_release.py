#!/usr/bin/env python3
"""
verify_pypi_release.py
Cross-check a PyPI package version against its GitHub releases.
A version on PyPI with no matching GitHub release tag is suspicious.
Article: https://aistackinsights.ai/blog/litellm-supply-chain-attack-2026
"""
import urllib.request, json, sys

PACKAGE = "litellm"
GITHUB_REPO = "BerriAI/litellm"
VERSION_TO_CHECK = sys.argv[1] if len(sys.argv) > 1 else "1.82.7"

print(f"Verifying {PACKAGE}=={VERSION_TO_CHECK}...\n")

# Check PyPI
pypi_url = f"https://pypi.org/pypi/{PACKAGE}/{VERSION_TO_CHECK}/json"
try:
    with urllib.request.urlopen(pypi_url) as r:
        pypi_data = json.load(r)
    upload_time = pypi_data["urls"][0]["upload_time"] if pypi_data.get("urls") else "unknown"
    uploader = pypi_data["urls"][0].get("uploaded_by", "unknown") if pypi_data.get("urls") else "unknown"
    print(f"PyPI: version exists, uploaded {upload_time} by '{uploader}'")
except Exception as e:
    print(f"PyPI: {e}")

# Check GitHub releases
gh_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
try:
    req = urllib.request.Request(gh_url, headers={"User-Agent": "verify-script/1.0"})
    with urllib.request.urlopen(req) as r:
        releases = json.load(r)
    gh_tags = {r["tag_name"].lstrip("v") for r in releases}
    if VERSION_TO_CHECK in gh_tags:
        print(f"GitHub: release tag v{VERSION_TO_CHECK} found - LEGITIMATE")
    else:
        print(f"GitHub: NO release tag found for {VERSION_TO_CHECK}")
        print("  WARNING: This version was not released via GitHub CI/CD.")
        print("  It was published directly to PyPI. Treat as SUSPICIOUS.")
except Exception as e:
    print(f"GitHub: {e}")
