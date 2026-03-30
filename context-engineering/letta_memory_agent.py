"""
letta_memory_agent.py — Persistent memory agent with Letta (MemGPT)
Companion script for: https://aistackinsights.ai/blog/context-engineering-developer-guide-2026

Letta gives your AI agent two types of memory:
  - Core memory   : Always in-context. Think of it as the agent's working memory.
                    Structured into "blocks" (e.g. <human>, <persona>).
                    Edited by the agent via memory_replace / memory_append tools.
  - Archival memory: Unlimited long-term storage backed by a vector database.
                    Agent retrieves relevant facts on demand via archival_memory_search.

Setup:
    pip install letta
    letta server &          # starts the Letta REST server on http://localhost:8283
    # Then run this script:
    python letta_memory_agent.py

Tip: Re-run the script multiple times and watch how the agent recalls facts
     from previous sessions — that's persistent memory in action.
"""

from letta import create_client
from letta.schemas.memory import ChatMemory
from letta.schemas.agent import AgentState


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LETTA_BASE_URL = "http://localhost:8283"  # default Letta server address

# The agent's persistent name — used to re-load the same agent across sessions
AGENT_NAME = "dev-assistant"

# Core memory: persona block
PERSONA = (
    "You are a senior developer assistant with deep knowledge of this project. "
    "You proactively store important project facts, decisions, and context in your memory "
    "so you can recall them accurately in future conversations. "
    "You are concise, precise, and never make up information."
)

# Core memory: initial human/user block
HUMAN_CONTEXT = (
    "The developer is building a full-stack SaaS application. "
    "Backend: Node.js + Prisma + PostgreSQL. "
    "Frontend: Next.js 14 (App Router) + Tailwind CSS. "
    "Auth: Clerk. Payments: Stripe. Deployed on Vercel + Railway."
)


# ---------------------------------------------------------------------------
# Helper: find or create agent
# ---------------------------------------------------------------------------

def get_or_create_agent(client) -> AgentState:
    """
    Return an existing agent by name, or create a new one.
    This is the key pattern for session persistence: same agent_id = same memory.
    """
    # List existing agents and look for one with our target name
    existing_agents = client.list_agents()
    for agent in existing_agents:
        if agent.name == AGENT_NAME:
            print(f"♻️  Resuming existing agent: {agent.name} (id={agent.id})")
            return agent

    # No existing agent found — create a fresh one
    print(f"🆕 Creating new agent: {AGENT_NAME}")
    agent = client.create_agent(
        name=AGENT_NAME,
        memory=ChatMemory(
            # Core memory block 1: persona (who the agent IS)
            persona=PERSONA,
            # Core memory block 2: human context (who the user IS + project facts)
            human=HUMAN_CONTEXT,
        ),
        # You can pin a specific LLM here; defaults to the server's configured model
        # llm_config=LLMConfig(model="claude-sonnet-4-6", model_endpoint_type="anthropic"),
    )
    return agent


# ---------------------------------------------------------------------------
# Helper: send a message and print the response
# ---------------------------------------------------------------------------

def chat(client, agent_id: str, message: str) -> str:
    """Send a message to the agent and return the assistant reply."""
    print(f"\n👤 You: {message}")
    response = client.send_message(
        agent_id=agent_id,
        message=message,
        role="user",
    )

    # Extract the assistant's text reply from the response
    reply = ""
    for msg in response.messages:
        if hasattr(msg, "text") and msg.text:
            reply = msg.text
            break

    print(f"🤖 Agent: {reply}")
    return reply


# ---------------------------------------------------------------------------
# Onboarding flow — run once on first launch
# ---------------------------------------------------------------------------

def run_onboarding(client, agent: AgentState):
    """
    Send structured project facts to the agent so it can store them in memory.
    On subsequent runs, the agent already has this context — no need to repeat.
    """
    agent_id = agent.id

    # Tell the agent to explicitly memorize key decisions
    chat(
        client, agent_id,
        "Please store these architectural decisions in your core memory:\n"
        "1. We use server actions (not API routes) for all form mutations\n"
        "2. Database queries always go through the service layer, never directly in components\n"
        "3. All monetary values are stored in cents (integers) to avoid floating-point issues\n"
        "4. Feature flags are managed via environment variables prefixed with NEXT_PUBLIC_FLAG_",
    )

    # Store a key fact in archival memory (longer-term, retrieved via vector search)
    chat(
        client, agent_id,
        "Archive this for future reference: The payments module is in src/lib/stripe.ts. "
        "It exports createCheckoutSession(), handleWebhook(), and getSubscriptionStatus(). "
        "Webhook secret is loaded from STRIPE_WEBHOOK_SECRET env var.",
    )

    print("\n✅ Onboarding complete. Facts stored in agent memory.")


# ---------------------------------------------------------------------------
# Demo: querying the agent in a new "session"
# ---------------------------------------------------------------------------

def demo_memory_recall(client, agent: AgentState):
    """
    Simulate a new session by asking questions that require recalled memory.
    The agent should answer correctly using facts from previous interactions.
    """
    agent_id = agent.id

    print("\n" + "=" * 60)
    print("DEMO: Testing memory recall across sessions")
    print("=" * 60)

    # These questions rely on facts stored in prior interactions
    questions = [
        "Where is the payments module and what does it export?",
        "How should I store a price field in the database schema?",
        "What tech stack are we using for the frontend?",
    ]

    for q in questions:
        chat(client, agent_id, q)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🚀 Connecting to Letta server at", LETTA_BASE_URL)

    # Create a REST client pointing at the local Letta server
    # For remote deployments, swap base_url with your hosted endpoint
    client = create_client(base_url=LETTA_BASE_URL)

    # Get or create the persistent agent
    agent = get_or_create_agent(client)

    # Determine if this is a first run (new agent) or returning session
    # A simple heuristic: check if the agent has any message history
    history = client.get_messages(agent_id=agent.id, limit=5)
    is_first_run = len(history) == 0

    if is_first_run:
        print("\n📝 First run — running onboarding to populate memory ...")
        run_onboarding(client, agent)
    else:
        print(f"\n📚 Returning session — agent has existing memory. Skipping onboarding.")

    # Always run the recall demo to show memory in action
    demo_memory_recall(client, agent)

    print("\n" + "=" * 60)
    print(f"Agent ID: {agent.id}")
    print("Tip: Re-run this script to see the agent recall facts from memory!")
    print("     Open http://localhost:8283 in your browser for the Letta UI.")
    print("=" * 60)
