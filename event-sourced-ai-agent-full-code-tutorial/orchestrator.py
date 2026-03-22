import uuid
from db import append_event, get_run_events
from models import RunRequest, AgentPlan
from planner import generate_plan
from policy import evaluate
from tools import run_tool


def run_agent(request: RunRequest) -> dict:
    run_id = str(uuid.uuid4())[:8]
    seq = 0

    def emit(event_type: str, actor: str, payload: dict):
        nonlocal seq
        seq += 1
        append_event(run_id, seq, event_type, actor, payload)
        print(f"  [{seq}] {event_type} — {actor}")

    # --- RunStarted ---
    emit("RunStarted", "orchestrator", {
        "goal": request.goal,
        "max_steps": request.max_steps,
        "budget_usd": request.budget_usd,
    })

    # --- Generate Plan ---
    try:
        plan: AgentPlan = generate_plan(
            run_id=run_id,
            goal=request.goal,
            max_steps=request.max_steps,
            budget_usd=request.budget_usd,
        )
        emit("PlanGenerated", "planner", plan.model_dump())
    except Exception as e:
        emit("PlanRejected", "planner", {"error": str(e)})
        emit("RunFailed", "orchestrator", {"reason": "Plan generation failed"})
        return {"run_id": run_id, "status": "failed", "reason": str(e)}

    # --- Execute Steps ---
    observations = []

    for step in plan.steps:
        # Policy check
        decision = evaluate(step)
        if decision.allowed:
            emit("ToolApproved", "policy_guard", {
                "step_id": step.id,
                "tool": step.tool,
                "reason": decision.reason,
            })
        else:
            emit("ToolRejected", "policy_guard", {
                "step_id": step.id,
                "tool": step.tool,
                "reason": decision.reason,
            })
            continue  # skip this step, keep going

        # Execute tool
        emit("ToolExecuted", "tool_executor", {"step_id": step.id, "tool": step.tool, "input": step.input})
        result = run_tool(step.tool, step.input)

        emit("ObservationCaptured", "tool_executor", {
            "step_id": step.id,
            "tool": step.tool,
            "result": result,
        })
        observations.append({"step_id": step.id, "result": result})

    # --- Finalize Response ---
    summary = f"Completed {len(observations)} steps for goal: {request.goal}"
    emit("ResponseFinalized", "orchestrator", {"summary": summary, "step_count": len(observations)})
    emit("RunCompleted", "orchestrator", {"run_id": run_id, "status": "success"})

    return {"run_id": run_id, "status": "success", "summary": summary, "observations": observations}
