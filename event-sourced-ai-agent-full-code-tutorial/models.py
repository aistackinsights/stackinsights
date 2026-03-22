from typing import Literal
from pydantic import BaseModel, Field


ALLOWED_TOOLS = Literal["web_search", "read_file", "write_file", "summarize"]


class PlanStep(BaseModel):
    id: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=5)
    tool: ALLOWED_TOOLS
    input: dict
    success_criteria: str = Field(..., min_length=5)


class AgentPlan(BaseModel):
    run_id: str
    goal: str
    max_steps: int = Field(..., ge=1, le=10)
    budget_usd: float = Field(..., ge=0.01, le=5.0)
    steps: list[PlanStep] = Field(..., min_length=1)
    stop_conditions: list[str] = Field(..., min_length=1)


class RunRequest(BaseModel):
    goal: str
    max_steps: int = 5
    budget_usd: float = 1.0


class PolicyDecision(BaseModel):
    step_id: str
    tool: str
    allowed: bool
    reason: str
