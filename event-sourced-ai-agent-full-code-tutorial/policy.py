from models import PlanStep, PolicyDecision

# Simple in-memory rules. In production: load from YAML or a config service.
POLICY_RULES = [
    {
        "name": "deny_write_without_explicit_path",
        "when": {"tool": "write_file"},
        "require_field": "path",
        "deny_if_missing": True,
        "reason": "write_file requires an explicit path in input",
    },
    {
        "name": "deny_search_with_empty_query",
        "when": {"tool": "web_search"},
        "require_field": "query",
        "deny_if_missing": True,
        "reason": "web_search requires a non-empty query",
    },
]


def evaluate(step: PlanStep) -> PolicyDecision:
    """Evaluate a plan step against all policy rules. First deny wins."""
    for rule in POLICY_RULES:
        if rule["when"].get("tool") == step.tool:
            required_field = rule.get("require_field")
            if required_field and not step.input.get(required_field):
                return PolicyDecision(
                    step_id=step.id,
                    tool=step.tool,
                    allowed=False,
                    reason=rule["reason"],
                )

    return PolicyDecision(
        step_id=step.id,
        tool=step.tool,
        allowed=True,
        reason="All policy rules passed",
    )
