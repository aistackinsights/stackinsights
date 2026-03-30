"""
hybrid_rag_pipeline.py — Hybrid RAG pipeline (semantic + BM25) with Claude
Companion script for: https://aistackinsights.ai/blog/context-engineering-developer-guide-2026

Architecture:
  1. Index a source directory with LlamaIndex (vector store in-memory by default)
  2. Build a BM25 keyword index over the same nodes
  3. Merge results with QueryFusionRetriever (Reciprocal Rank Fusion)
  4. Inject retrieved context into a Claude claude-sonnet-4-6 prompt
  5. Return the grounded answer

Requirements:
    pip install llama_index anthropic llama-index-retrievers-bm25

Usage:
    python hybrid_rag_pipeline.py "How does authentication work in this codebase?"

    # Or import and call directly:
    from hybrid_rag_pipeline import build_index, ask
    index = build_index("./src")
    answer = ask("What does the UserService do?", index=index)
    print(answer)
"""

import os
import sys
from pathlib import Path

import anthropic
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_SOURCE_DIR = "./src"
CLAUDE_MODEL = "claude-sonnet-4-6"
TOP_K = 5          # candidates per retriever before fusion
SIMILARITY_TOP_K = 3   # final fused results passed to the LLM

SYSTEM_PROMPT = """You are a senior software engineer helping a developer understand their codebase.
Answer questions using ONLY the context provided. If the context doesn't contain enough information
to answer confidently, say so clearly rather than guessing. Be concise and precise."""


# ---------------------------------------------------------------------------
# Index builder
# ---------------------------------------------------------------------------

def build_index(source_dir: str = DEFAULT_SOURCE_DIR) -> VectorStoreIndex:
    """
    Load all documents from source_dir and build an in-memory vector index.

    For production use, replace the in-memory store with a persistent one:
        from llama_index.vector_stores.chroma import ChromaVectorStore
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_or_create_collection("codebase")
        store = ChromaVectorStore(chroma_collection=collection)
        index = VectorStoreIndex.from_documents(docs, vector_store=store)
    """
    src_path = Path(source_dir)
    if not src_path.exists():
        raise FileNotFoundError(f"Source directory not found: {src_path.resolve()}")

    print(f"📂 Loading documents from {src_path.resolve()} ...")

    # LlamaIndex's SimpleDirectoryReader handles .py, .ts, .tsx, .md, .txt, etc.
    documents = SimpleDirectoryReader(
        input_dir=str(src_path),
        recursive=True,
        exclude_hidden=True,
    ).load_data()

    if not documents:
        raise ValueError(f"No documents found in {src_path}. "
                         "Check the path and ensure it contains readable files.")

    print(f"✅ Loaded {len(documents)} document chunk(s). Building vector index ...")
    index = VectorStoreIndex.from_documents(documents, show_progress=True)
    print("✅ Vector index ready.")
    return index


# ---------------------------------------------------------------------------
# Hybrid retriever
# ---------------------------------------------------------------------------

def build_hybrid_retriever(index: VectorStoreIndex) -> QueryFusionRetriever:
    """
    Combine a vector (semantic) retriever and a BM25 (keyword) retriever
    using Reciprocal Rank Fusion for balanced hybrid retrieval.
    """
    vector_retriever = index.as_retriever(similarity_top_k=TOP_K)

    # BM25 operates over the raw nodes (no embedding needed)
    bm25_retriever = BM25Retriever.from_defaults(
        index=index,
        similarity_top_k=TOP_K,
    )

    hybrid_retriever = QueryFusionRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        similarity_top_k=SIMILARITY_TOP_K,
        num_queries=1,       # Set >1 to auto-generate query variants (increases LLM calls)
        mode="reciprocal_rerank",
        use_async=True,
        verbose=False,
    )

    return hybrid_retriever


# ---------------------------------------------------------------------------
# Ask function
# ---------------------------------------------------------------------------

def ask(
    question: str,
    index: VectorStoreIndex | None = None,
    source_dir: str = DEFAULT_SOURCE_DIR,
) -> str:
    """
    Retrieve relevant context from the codebase and answer using Claude.

    Args:
        question:   Natural-language question about the codebase.
        index:      Pre-built VectorStoreIndex. If None, builds one from source_dir.
        source_dir: Directory to index if index is None.

    Returns:
        Claude's grounded answer as a string.
    """
    if index is None:
        index = build_index(source_dir)

    retriever = build_hybrid_retriever(index)

    print(f"\n🔍 Retrieving context for: \"{question}\" ...")
    nodes = retriever.retrieve(question)

    if not nodes:
        return "No relevant context found in the codebase for that question."

    # Build context block from retrieved nodes
    context_parts: list[str] = []
    for i, node in enumerate(nodes, start=1):
        source = node.metadata.get("file_name", "unknown")
        score = f"{node.score:.3f}" if node.score is not None else "n/a"
        context_parts.append(
            f"--- Source {i}: {source} (relevance: {score}) ---\n{node.get_content()}"
        )

    context_block = "\n\n".join(context_parts)

    user_message = (
        f"Here is relevant context from the codebase:\n\n"
        f"{context_block}\n\n"
        f"---\n\n"
        f"Question: {question}"
    )

    # Call Claude
    print(f"🤖 Querying Claude ({CLAUDE_MODEL}) ...")
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return response.content[0].text


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hybrid_rag_pipeline.py \"your question here\"")
        print("       python hybrid_rag_pipeline.py \"your question\" --src ./my_project/src")
        sys.exit(1)

    question_arg = sys.argv[1]

    # Optional --src flag
    src_dir = DEFAULT_SOURCE_DIR
    if "--src" in sys.argv:
        src_idx = sys.argv.index("--src")
        if src_idx + 1 < len(sys.argv):
            src_dir = sys.argv[src_idx + 1]

    answer = ask(question_arg, source_dir=src_dir)
    print(f"\n💬 Answer:\n{answer}\n")
