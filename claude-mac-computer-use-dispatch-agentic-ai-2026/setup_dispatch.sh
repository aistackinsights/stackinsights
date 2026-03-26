#!/usr/bin/env bash
# setup_dispatch.sh — macOS setup helper for Claude computer use + Dispatch
# Article: https://aistackinsights.ai/blog/claude-mac-computer-use-dispatch-agentic-ai-2026
# Repo:    https://github.com/aistackinsights/stackinsights/tree/main/claude-mac-computer-use-dispatch-agentic-ai-2026

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Claude Computer Use + Dispatch — macOS Setup Helper    ║${NC}"
echo -e "${BLUE}║          aistackinsights.ai                               ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ─── 1. OS check ─────────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/6] Checking macOS version...${NC}"
OS=$(uname -s)
if [[ "$OS" != "Darwin" ]]; then
  echo -e "${RED}✗ This script is macOS only. Claude computer use is not yet available on other platforms.${NC}"
  exit 1
fi

MACOS_VERSION=$(sw_vers -productVersion)
MACOS_MAJOR=$(echo "$MACOS_VERSION" | cut -d. -f1)
if [[ "$MACOS_MAJOR" -lt 14 ]]; then
  echo -e "${YELLOW}⚠ macOS $MACOS_VERSION detected. Sonoma (14.0+) is recommended for best performance.${NC}"
else
  echo -e "${GREEN}✓ macOS $MACOS_VERSION — compatible${NC}"
fi

# ─── 2. Claude desktop app ───────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[2/6] Checking for Claude desktop app...${NC}"
CLAUDE_APP="/Applications/Claude.app"
if [[ -d "$CLAUDE_APP" ]]; then
  CLAUDE_VERSION=$(/usr/libexec/PlistBuddy -c "Print CFBundleShortVersionString" \
    "$CLAUDE_APP/Contents/Info.plist" 2>/dev/null || echo "unknown")
  echo -e "${GREEN}✓ Claude.app found (version: $CLAUDE_VERSION)${NC}"
else
  echo -e "${RED}✗ Claude.app not found in /Applications${NC}"
  echo ""
  echo "  Download Claude for Mac:"
  echo "  https://claude.ai/download"
  echo ""
  read -p "  Press Enter after installing Claude to continue, or Ctrl+C to exit..."
fi

# ─── 3. Accessibility permissions ────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[3/6] Checking Accessibility permissions...${NC}"
echo ""
echo "  Claude needs Accessibility access to control your screen."
echo "  → System Settings → Privacy & Security → Accessibility"
echo "  → Ensure 'Claude' is toggled ON"
echo ""

# Check if accessibility is granted via tccutil (requires SIP off or specific entitlements)
# We'll do a soft check — open System Settings to the right pane
read -p "  Open Accessibility settings now? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
  echo -e "${YELLOW}  ↳ Toggle Claude ON in the list, then return here.${NC}"
  read -p "  Press Enter when done..."
fi
echo -e "${GREEN}✓ Accessibility step complete${NC}"

# ─── 4. Screen Recording permissions ─────────────────────────────────────────
echo ""
echo -e "${YELLOW}[4/6] Checking Screen Recording permissions...${NC}"
echo ""
echo "  Claude also needs Screen Recording to take screenshots during computer use tasks."
echo "  → System Settings → Privacy & Security → Screen Recording"
echo "  → Ensure 'Claude' is toggled ON"
echo ""
read -p "  Open Screen Recording settings now? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
  echo -e "${YELLOW}  ↳ Toggle Claude ON in the list, then return here.${NC}"
  read -p "  Press Enter when done..."
fi
echo -e "${GREEN}✓ Screen Recording step complete${NC}"

# ─── 5. Dispatch pairing instructions ────────────────────────────────────────
echo ""
echo -e "${YELLOW}[5/6] Setting up Dispatch (mobile → desktop pipeline)...${NC}"
echo ""
echo "  Dispatch lets you send Claude tasks from your iPhone to your Mac."
echo ""
echo "  Steps:"
echo "    1. Open the Claude app on your iPhone"
echo "    2. Tap the ⚡ Dispatch icon in the bottom navigation"
echo "    3. Tap 'Pair a Mac'"
echo "    4. Open Claude.app on your Mac"
echo "    5. Go to Claude Cowork → Settings → Dispatch"
echo "    6. Click 'Show QR Code' and scan it with your iPhone"
echo ""
echo -e "${GREEN}  Once paired, tasks sent from your phone route to this Mac automatically.${NC}"
echo ""

# ─── 6. Computer use research preview ────────────────────────────────────────
echo ""
echo -e "${YELLOW}[6/6] Enabling computer use research preview...${NC}"
echo ""
echo "  Computer use is currently a research preview and must be enabled manually:"
echo ""
echo "    1. Open Claude.app on your Mac"
echo "    2. Go to Settings (⌘ + ,)"
echo "    3. Navigate to 'Cowork' or 'Beta Features'"
echo "    4. Toggle ON: 'Computer Use (Research Preview)'"
echo ""
echo -e "${YELLOW}  ⚠ Note: This feature takes screenshots of your screen during tasks.${NC}"
echo -e "${YELLOW}    Review active applications and close sensitive documents before${NC}"
echo -e "${YELLOW}    starting any computer use session.${NC}"
echo ""

# ─── Done ────────────────────────────────────────────────────────────────────
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Setup Complete! 🎉                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  You're ready to use Claude computer use + Dispatch."
echo ""
echo "  Quick test:"
echo "    → Open Claude Cowork on your Mac"
echo "    → Type: 'Open Notes and write: Hello from Claude'"
echo "    → Watch Claude take control of your screen"
echo ""
echo "  Docs: https://support.claude.com/en/articles/14128542-let-claude-use-your-computer-in-cowork"
echo "  Article: https://aistackinsights.ai/blog/claude-mac-computer-use-dispatch-agentic-ai-2026"
echo ""
