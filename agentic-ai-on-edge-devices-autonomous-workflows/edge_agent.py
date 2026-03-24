# edge_agent.py -- full agentic ReAct loop running entirely on device via ollama
import json, sqlite3, datetime, urllib.request
from typing import Any

OLLAMA_MODEL = "phi4-mini"  # or qwen2.5:3b, gemma3:2b

def call_local_llm(messages: list[dict], tools: list[dict] | None = None) -> dict:
    payload = {"model": OLLAMA_MODEL, "messages": messages, "stream": False}
    if tools:
        payload["tools"] = tools
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

TOOLS = [
    {"type": "function", "function": {
        "name": "read_sensor",
        "description": "Read a sensor value by sensor ID.",
        "parameters": {"type": "object", "properties": {
            "sensor_id": {"type": "string", "description": "Sensor ID e.g. temp_01"}
        }, "required": ["sensor_id"]}
    }},
    {"type": "function", "function": {
        "name": "log_event",
        "description": "Log an event with severity and message.",
        "parameters": {"type": "object", "properties": {
            "severity": {"type": "string", "enum": ["info", "warning", "critical"]},
            "message": {"type": "string"}
        }, "required": ["severity", "message"]}
    }},
    {"type": "function", "function": {
        "name": "trigger_action",
        "description": "Trigger a physical action on the device.",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["fan_on", "fan_off", "alert_led", "shutdown"]}
        }, "required": ["action"]}
    }}
]

def read_sensor(sensor_id: str) -> float:
    import random
    return {"temp_01": 78.5 + random.uniform(-5, 15), "humidity_01": 45.0}.get(sensor_id, 0.0)

def log_event(severity: str, message: str) -> str:
    conn = sqlite3.connect("edge_agent.db")
    conn.execute("CREATE TABLE IF NOT EXISTS events (ts TEXT, severity TEXT, message TEXT)")
    conn.execute("INSERT INTO events VALUES (?, ?, ?)", (datetime.datetime.now().isoformat(), severity, message))
    conn.commit(); conn.close()
    print(f"[{severity.upper()}] {message}")
    return "logged"

def trigger_action(action: str) -> str:
    print(f">>> ACTION: {action}")
    return f"{action} executed"

TOOL_DISPATCH = {"read_sensor": read_sensor, "log_event": log_event, "trigger_action": trigger_action}

def execute_tool(name: str, args: dict) -> Any:
    return TOOL_DISPATCH.get(name, lambda **k: f"Unknown tool: {name}")(**args)

def run_agent(task: str, max_steps: int = 6) -> str:
    messages = [
        {"role": "system", "content": "You are an autonomous edge AI agent. Use tools to observe, reason, and act. Always read sensors before acting."},
        {"role": "user", "content": task}
    ]
    for _ in range(max_steps):
        response = call_local_llm(messages, tools=TOOLS)
        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])
        if not tool_calls:
            return message.get("content", "Task complete.")
        messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
        for tc in tool_calls:
            fn = tc["function"]
            result = execute_tool(fn["name"], fn.get("arguments", {}))
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)})
    return "Max steps reached."

if __name__ == "__main__":
    print(run_agent("Check all sensors, identify anomalies, and take appropriate action."))
