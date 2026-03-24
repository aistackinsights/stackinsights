# agent_knowledge_query.py
# Query the cq commons before starting a task; propose knowledge after completing it.
import httpx, asyncio

CQ_BASE_URL = "http://localhost:8080"

async def query_cq_commons(task_context: str, min_confidence: float = 0.6) -> list[dict]:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{CQ_BASE_URL}/api/query",
            json={"context": task_context, "min_confidence": min_confidence, "max_results": 10})
        r.raise_for_status()
        return r.json()["entries"]

async def propose_knowledge(content: str, context: str, confidence: float = 0.5) -> str:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{CQ_BASE_URL}/api/propose",
            json={"content": content, "context": context, "initial_confidence": confidence})
        r.raise_for_status()
        return r.json()["id"]

async def record_feedback(entry_id: str, confirmed: bool) -> None:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{CQ_BASE_URL}/api/feedback/{entry_id}",
            json={"confirmed": confirmed})
        r.raise_for_status()

if __name__ == "__main__":
    async def demo():
        print("Querying commons for Stripe knowledge...")
        entries = await query_cq_commons("stripe api rate limiting")
        for e in entries:
            print(f"  [{e['confidence']:.2f}] {e['content'][:80]}")

        print("\nProposing new knowledge...")
        eid = await propose_knowledge(
            content="Stripe returns HTTP 200 with error body on rate limits. Check response.error, not status code.",
            context="stripe payments api rate limiting",
            confidence=0.9
        )
        print(f"  Proposed: {eid}")

    asyncio.run(demo())
