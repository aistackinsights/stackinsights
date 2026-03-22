from dotenv import load_dotenv
load_dotenv()

from models import RunRequest
from orchestrator import run_agent
from replay import replay_run, replay_all
from db import get_run_events, get_all_runs


def demo_run():
    print("=== Running Agent ===\n")
    request = RunRequest(
        goal="Research the latest developments in AI agent frameworks and summarize the key findings",
        max_steps=4,
        budget_usd=0.50,
    )
    result = run_agent(request)
    print(f"\nResult: {result['status']} — {result['summary']}")
    return result["run_id"]


def show_events(run_id: str):
    print(f"\n=== Event Log for {run_id} ===")
    events = get_run_events(run_id)
    for e in events:
        print(f"  [{e['seq']}] {e['event_type']} ({e['actor']})")


def demo_replay(run_id: str):
    print("\n=== Replaying Run ===")
    delta = replay_run(run_id, verbose=True)
    return delta


if __name__ == "__main__":
    # 1. Run the agent
    run_id = demo_run()

    # 2. Print the event log
    show_events(run_id)

    # 3. Replay it (simulates testing a prompt change)
    demo_replay(run_id)
