#!/bin/bash
# check_litellm_compromise.sh
# Checks the active Python environment for compromised litellm versions and
# the malicious litellm_init.pth file planted by the March 24, 2026 supply chain attack.
#
# Usage: bash check_litellm_compromise.sh
# Run on every machine, CI runner, and container where litellm was installed.
#
# Reference: https://github.com/BerriAI/litellm/issues/24518

MALICIOUS_PTH="litellm_init.pth"
KNOWN_BAD_SHA="ceNa7wMJnNHy1kRnNCcwJaFjWX3pORLfMh7xGL8TUjg"

echo "=== LiteLLM Compromise Checker ==="
echo "    Reference: https://github.com/BerriAI/litellm/issues/24518"
echo ""

# 1. Check installed version in active environment
echo "[1] Checking installed litellm version..."
LITELLM_VERSION=$(pip show litellm 2>/dev/null | grep "^Version:" | awk '{print $2}')
if [ -z "$LITELLM_VERSION" ]; then
  echo "    litellm not found in active environment."
else
  echo "    Installed: litellm==$LITELLM_VERSION"
  if [[ "$LITELLM_VERSION" == "1.82.7" || "$LITELLM_VERSION" == "1.82.8" ]]; then
    echo "    ⚠️  COMPROMISED VERSION DETECTED"
    echo "    ACTION: pip uninstall litellm && rotate ALL credentials immediately."
  else
    echo "    ✅ Not a known compromised version."
  fi
fi

# 2. Scan all site-packages dirs for the malicious .pth file
echo ""
echo "[2] Scanning site-packages for $MALICIOUS_PTH..."
SITE_PKGS=$(python3 -c "import site; print('\n'.join(site.getsitepackages()))" 2>/dev/null)
FOUND=0
while IFS= read -r DIR; do
  PTH_FILE="$DIR/$MALICIOUS_PTH"
  if [ -f "$PTH_FILE" ]; then
    if command -v sha256sum &>/dev/null; then
      ACTUAL_SHA=$(sha256sum "$PTH_FILE" 2>/dev/null | awk '{print $1}')
    elif command -v shasum &>/dev/null; then
      ACTUAL_SHA=$(shasum -a 256 "$PTH_FILE" 2>/dev/null | awk '{print $1}')
    else
      ACTUAL_SHA="HASH_TOOL_UNAVAILABLE"
    fi
    echo ""
    echo "    ⚠️  FOUND: $PTH_FILE"
    echo "    SHA256: $ACTUAL_SHA"
    if [ "$ACTUAL_SHA" == "$KNOWN_BAD_SHA" ]; then
      echo "    ✅ SHA256 CONFIRMED MALICIOUS — delete this file immediately."
    elif [ "$ACTUAL_SHA" == "HASH_TOOL_UNAVAILABLE" ]; then
      echo "    ⚠️  Could not compute hash — treat as malicious and delete."
    else
      echo "    ⚠️  Unknown SHA — inspect manually before trusting."
    fi
    FOUND=1
  fi
done <<< "$SITE_PKGS"

if [ "$FOUND" -eq 0 ]; then
  echo "    ✅ litellm_init.pth not found in active site-packages."
fi

echo ""
echo "[3] Scan complete."
echo "    Also run audit_python_envs.py to scan ALL virtual environments on this machine."
echo "    Full incident details: https://github.com/BerriAI/litellm/issues/24518"
