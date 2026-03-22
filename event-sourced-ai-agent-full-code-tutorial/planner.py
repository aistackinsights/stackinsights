import json
import os
from models import AgentPlan

SYSTEM_PROMPT = """You are an AI agent planner. Given a goal, produce a JSON plan with this exact schema:

{
  "run_id": "<provided>",
  "goal": "<the goal>",
  "max_steps": <int 1-10>,
  "budget_usd": <float 0.01-5.0>,
  "steps": [
    {
      "id": "step_1",
      "objective": "What this step achieves",
      "tool": "web_search" | "read_file" | "write_file" | "summarize",
      "input": { ... tool-specific params ... },
      "success_criteria": "How to know this step succeeded"
    }
  ],
  "stop_conditions": ["Condition that means the goal is complete"]
}

Return ONLY valid JSON. No explanation. No markdown fences."""


def generate_plan(run_id: str, goal: str, max_steps: int, budget_usd: float) -> AgentPlan:
    """Call LLM to generate a bounded, validated plan."""

    user_message = f"run_id: {run_id}\ngoal: {goal}\nmax_steps: {max_steps}\nbudget_usd: {budget_usd}"

    if os.getenv("ANTHROPIC_API_KEY"):
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        raw = response.content[0].text
    else:
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content

    data = json.loads(raw)
    return AgentPlan.model_validate(data)  # raises ValidationError if schema is wrong
