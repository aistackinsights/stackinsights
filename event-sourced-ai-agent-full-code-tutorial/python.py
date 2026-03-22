import httpx
import os

def _web_search(params: dict) -> dict:
    query = params.get("query", "")
    api_key = os.getenv("BRAVE_API_KEY")

    response = httpx.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={"Accept": "application/json", "X-Subscription-Token": api_key},
        params={"q": query, "count": 5},
        timeout=10,
    )
    data = response.json()
    results = [
        {"title": r["title"], "url": r["url"], "snippet": r.get("description", "")}
        for r in data.get("web", {}).get("results", [])
    ]
    return {"success": True, "query": query, "results": results}
