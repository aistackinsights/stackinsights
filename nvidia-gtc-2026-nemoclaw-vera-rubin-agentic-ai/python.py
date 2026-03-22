from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun

# AI-Q hybrid pattern: orchestrator + open model for research tasks
orchestrator = ChatNVIDIA(model="meta/llama-3.3-70b-instruct")  # frontier for planning
researcher = ChatNVIDIA(model="nvidia/nemotron-nano-8b-instruct")  # open model for subtasks

search_tool = DuckDuckGoSearchRun()

# The orchestrator delegates research sub-tasks to the cheaper open model
def hybrid_research_agent(query: str) -> str:
    # Step 1: Orchestrator decomposes the query
    plan = orchestrator.invoke(
        f"Decompose this research question into 3-5 search sub-queries: {query}"
    )
    
    # Step 2: Open model executes each sub-query cheaply
    findings = []
    for sub_query in parse_subqueries(plan.content):
        result = search_tool.run(sub_query)
        summary = researcher.invoke(
            f"Summarize the key facts from this search result for: {sub_query}\n\n{result}"
        )
        findings.append(summary.content)
    
    # Step 3: Orchestrator synthesizes the final answer
    return orchestrator.invoke(
        f"Synthesize these research findings into a comprehensive answer to: {query}\n\n"
        + "\n\n".join(findings)
    ).content

def parse_subqueries(text: str) -> list[str]:
    # Simple parser — production use would be more robust
    lines = [l.strip("- ").strip() for l in text.split("\n") if l.strip().startswith("-")]
    return lines[:5] if lines else [text]
