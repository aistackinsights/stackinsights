# Quick NemoClaw agent setup (once NemoClaw is installed)
import subprocess
import json

def deploy_secure_claw(task: str, privacy_level: str = "standard") -> dict:
    """
    Deploy a task to a NemoClaw-secured OpenClaw agent.
    Requires NemoClaw to be installed: curl -sSL https://get.nemoclaw.ai | sh
    """
    cmd = [
        "openclaw", "run",
        "--sandbox", "nemoclaw",
        "--privacy-profile", privacy_level,
        "--output-format", "json",
        "--model", "nemotron-super-49b",
        task
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    
    if result.returncode != 0:
        raise RuntimeError(f"Claw execution failed: {result.stderr}")
    
    return json.loads(result.stdout)

# Example: Run a coding agent with enterprise privacy guardrails
output = deploy_secure_claw(
    task="Review the auth.py module for security vulnerabilities and suggest fixes",
    privacy_level="enterprise"  # blocks all external network egress
)

print(f"Agent result: {output['result']}")
print(f"Tools used: {output['tools_called']}")
print(f"Network requests blocked: {output['security']['blocked_requests']}")
