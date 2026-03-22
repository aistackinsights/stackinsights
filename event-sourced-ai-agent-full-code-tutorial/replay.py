from db import get_run_events, get_all_runs
from models import RunRequest
from orchestrator import run_agent


def replay_run(run_id: str, verbose: bool = True) -> dict:
    """
    Load a historical run and re-execute it with the current code.
    Useful for regression testing after prompt or tool changes.
    """
    events = get_run_events(run_id)
    if not events:
        return {"error": f"No events found for run_id={run_id}"}

    # Extract original RunStarted event to get the original goal
    started = next((e for e in events if e["event_type"] == "RunStarted"), None)
    if not started:
        return {"error": "RunStarted event not found — cannot replay"}

    original_goal = started["payload"]["goal"]
    original_steps = started["payload"]["max_steps"]
    original_budget = started["payload"]["budget_usd"]

    if verbose:
        print(f"\n--- REPLAYING run_id={run_id} ---")
        print(f"Original goal: {original_goal}")
        print(f"Original events: {len(events)}")
        print(f"Re-running with current code...\n")

    # Re-run with current code
    new_result = run_agent(RunRequest(
        goal=original_goal,
        max_steps=original_steps,
        budget_usd=original_budget,
    ))

    # Compare step counts as a basic quality signal
    original_completed = sum(1 for e in events if e["event_type"] == "ObservationCaptured")
    new_completed = len(new_result.get("observations", []))

    delta = {
        "original_run_id": run_id,
        "new_run_id": new_result["run_id"],
        "original_steps_completed": original_completed,
        "new_steps_completed": new_completed,
        "regression": new_completed < original_completed,
    }

    if verbose:
        print(f"\n--- REPLAY DELTA ---")
        print(f"Original: {original_completed} steps completed")
        print(f"New:      {new_completed} steps completed")
        print(f"Regression: {delta['regression']}")

    return delta


def replay_all(verbose: bool = False) -> list[dict]:
    """Replay every historical run. Use in CI before deploying prompt changes."""
    run_ids = get_all_runs()
    results = []
    regressions = 0

    for run_id in run_ids:
        delta = replay_run(run_id, verbose=verbose)
        results.append(delta)
        if delta.get("regression"):
            regressions += 1

    print(f"\n=== Replay Summary: {len(run_ids)} runs, {regressions} regressions ===")
    return results
