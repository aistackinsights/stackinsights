# Install NemoClaw with a single command (requires NVIDIA GPU or RTX PC)
curl -sSL https://get.nemoclaw.ai | sh

# After install, launch your first secure claw
openclaw --sandbox nemoclaw --model nemotron-ultra-253b "Summarize my emails and flag anything urgent"

# Or start a persistent always-on agent with defined privacy policy
openclaw serve \
  --sandbox nemoclaw \
  --privacy-profile enterprise \
  --network-policy block-egress \
  --model nemotron-nano-8b
