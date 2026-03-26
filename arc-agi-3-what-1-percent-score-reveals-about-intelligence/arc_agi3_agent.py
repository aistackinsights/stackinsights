#!/usr/bin/env python3
"""
arc_agi3_agent.py — Minimal agent framework for ARC-AGI-3
Article: https://aistackinsights.ai/blog/arc-agi-3-what-1-percent-score-reveals-about-intelligence
Docs: https://docs.arcprize.org/
"""
import httpx, json, time
from dataclasses import dataclass, field

API_BASE = "https://api.arcprize.org/v3"

@dataclass
class WorldModel:
    observations: list[dict] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    step_count: int = 0

    def observe(self, obs: dict) -> None:
        self.observations.append(obs)
        self.step_count += 1

    def summarize(self) -> str:
        if not self.observations:
            return "No observations yet."
        recent = self.observations[-5:]
        changes = []
        for i in range(1, len(recent)):
            if recent[i-1] != recent[i]:
                changes.append(f"Step {self.step_count - len(recent) + i}: state changed")
        return f"Steps taken: {self.step_count}. Recent changes: {'; '.join(changes) or 'none'}."


class ARCAgent:
    def __init__(self, api_key: str, model_fn):
        self.client = httpx.Client(
            base_url=API_BASE,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30
        )
        self.model_fn = model_fn
        self.world = WorldModel()

    def start_episode(self, task_id: str) -> dict:
        resp = self.client.post("/episodes", json={"task_id": task_id})
        resp.raise_for_status()
        self.world = WorldModel()
        return resp.json()

    def act(self, episode_id: str, observation: dict) -> str:
        self.world.observe(observation)
        prompt = f"""You are solving an unknown interactive environment.
World model: {self.world.summarize()}
Current observation: {json.dumps(observation, indent=2)}
Available actions: {observation.get('available_actions', ['up','down','left','right','interact'])}

Think step by step:
1. What do observations tell you about the environment rules?
2. What hypothesis can you test next?
3. What action is most informative or most likely to progress toward the goal?

Respond with ONLY the action name."""
        return self.model_fn(prompt).strip().lower()

    def submit_action(self, episode_id: str, action: str) -> dict:
        resp = self.client.post(f"/episodes/{episode_id}/actions", json={"action": action})
        resp.raise_for_status()
        return resp.json()

    def run_episode(self, task_id: str, max_steps: int = 200) -> dict:
        episode = self.start_episode(task_id)
        episode_id = episode["episode_id"]
        obs = episode["initial_observation"]
        print(f"Starting episode {episode_id}")
        for step in range(max_steps):
            action = self.act(episode_id, obs)
            result = self.submit_action(episode_id, action)
            obs = result.get("observation", {})
            if result.get("done"):
                print(f"  Done at step {step+1}. Score: {result.get('score', 0):.3f}")
                return result
            time.sleep(0.1)
        return {"done": False, "score": 0, "reason": "max_steps_reached"}


def ollama_model(prompt: str) -> str:
    import urllib.request
    body = json.dumps({"model": "phi4-mini", "messages": [{"role": "user", "content": prompt}], "stream": False}).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)["message"]["content"]


if __name__ == "__main__":
    agent = ARCAgent(api_key="YOUR_API_KEY", model_fn=ollama_model)
    result = agent.run_episode(task_id="arc3-task-001")
    print(f"Final score: {result.get('score', 0):.3f}")
