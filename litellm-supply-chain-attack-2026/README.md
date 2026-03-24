# The LiteLLM PyPI Attack: How a Compromised Security Scanner Became a Credential Harvester

Code samples from the article: https://aistackinsights.ai/blog/litellm-supply-chain-attack-2026

## What This Is

On March 24, 2026, LiteLLM versions 1.82.7 and 1.82.8 on PyPI were found to contain a credential-stealing payload that executes on every Python startup via a malicious `.pth` file — **no import required**. The root cause was a compromised Trivy security scanner dependency in LiteLLM's CI/CD pipeline.

These scripts help you detect compromise and harden your supply chain.

## Files

| File | Description |
|------|-------------|
| `check_litellm_compromise.sh` | Bash script: checks active Python env for compromised litellm versions and the malicious `litellm_init.pth` file |
| `audit_python_envs.py` | Python script: walks your entire home directory (or any specified path) to find `litellm_init.pth` across all venvs, conda envs, and system Python installs |
| `publish.yml` | GitHub Actions workflow: publish to PyPI using OIDC Trusted Publishers — no stored API tokens, resistant to stolen CI credentials |
| `audit.yml` | GitHub Actions workflow: run pip-audit on every push/PR and daily to catch vulnerable dependencies before they reach your environments |

## Quick Start

### Check if you're compromised

```bash
# Bash (active environment only)
bash check_litellm_compromise.sh

# Python (scans all environments on the machine)
python3 audit_python_envs.py

# Scan a specific path
python3 audit_python_envs.py /home/youruser
```

### Harden your supply chain

1. Copy `publish.yml` to `.github/workflows/publish.yml` in your PyPI package repo
2. [Configure a Trusted Publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/) for your project on PyPI
3. Copy `audit.yml` to `.github/workflows/audit.yml` in any Python project

## Malicious File Reference

| Property | Value |
|----------|-------|
| Filename | `litellm_init.pth` |
| SHA256 | `ceNa7wMJnNHy1kRnNCcwJaFjWX3pORLfMh7xGL8TUjg` |
| File size | 34,628 bytes |
| Affected versions | `litellm==1.82.7`, `litellm==1.82.8` |

## Incident Resources

- [Detailed technical analysis (Issue #24512)](https://github.com/BerriAI/litellm/issues/24512)
- [LiteLLM team official response (Issue #24518)](https://github.com/BerriAI/litellm/issues/24518)
- [Hacker News discussion](https://news.ycombinator.com/item?id=47501426)
- [Python .pth file documentation](https://docs.python.org/3/library/site.html)
- [pip-audit](https://github.com/pypa/pip-audit)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
