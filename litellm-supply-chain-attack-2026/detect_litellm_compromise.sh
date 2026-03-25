#!/bin/bash
# detect_litellm_compromise.sh
# Run on any machine that may have installed LiteLLM via pip
# Usage: bash detect_litellm_compromise.sh

SHA_MALICIOUS="ceNa7wMJnNHy1kRnNCcwJaFjWX3pORLfMh7xGL8TUjg"
FOUND=0

echo "=== LiteLLM Compromise Detector ==="
echo "Checking for malicious litellm_init.pth..."
echo ""

while IFS= read -r pth_file; do
    actual_sha=$(sha256sum "$pth_file" 2>/dev/null | awk '{print $1}')
    echo "Found: $pth_file"
    echo "  SHA256: $actual_sha"
    if [ "$actual_sha" = "$SHA_MALICIOUS" ]; then
        echo "  STATUS: *** MALICIOUS - ROTATE ALL CREDENTIALS NOW ***"
        FOUND=1
    else
        echo "  STATUS: Unknown .pth file - investigate"
        FOUND=1
    fi
done < <(find / -name "litellm_init.pth" 2>/dev/null)

echo ""
echo "=== Installed LiteLLM version ==="
if pip show litellm 2>/dev/null | grep -E "^Version:"; then
    INSTALLED=$(pip show litellm 2>/dev/null | grep "^Version:" | awk '{print $2}')
    if [[ "$INSTALLED" == "1.82.7" || "$INSTALLED" == "1.82.8" ]]; then
        echo "CRITICAL: Compromised version $INSTALLED is installed"
        FOUND=1
    else
        echo "Version $INSTALLED is not a known-malicious version"
    fi
else
    echo "LiteLLM not found in current environment"
fi

echo ""
if [ "$FOUND" -eq 1 ]; then
    echo "ACTION REQUIRED: Rotate all credentials immediately"
    echo "Full guide: https://aistackinsights.ai/blog/litellm-supply-chain-attack-2026"
else
    echo "No indicators found. Still audit CI/CD logs for March 23-24 installs."
fi
