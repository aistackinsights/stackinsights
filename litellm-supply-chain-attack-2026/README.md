# LiteLLM Supply Chain Attack 2026 — Detection and Audit Scripts

Code samples from the article: https://aistackinsights.ai/blog/litellm-supply-chain-attack-2026

## Files

- `detect_litellm_compromise.sh` — Bash detection script: checks for malicious `litellm_init.pth` and compromised installed versions
- `detect_litellm_compromise.py` — Cross-platform Python version of the same detector
- `verify_pypi_release.py` — Cross-check any PyPI package version against its GitHub release history

## Usage

```bash
# Bash (Linux/macOS)
bash detect_litellm_compromise.sh

# Python (cross-platform)
python detect_litellm_compromise.py

# Verify a specific version
python verify_pypi_release.py 1.82.7
```

## What to do if compromised

1. Rotate ALL credentials (AWS, SSH, GitHub tokens, API keys, DB passwords)
2. Run `pip uninstall litellm -y`
3. Delete any `litellm_init.pth` in site-packages
4. Check CloudTrail, GitHub audit log, K8s audit log for unauthorized activity
5. See full guide: https://aistackinsights.ai/blog/litellm-supply-chain-attack-2026
