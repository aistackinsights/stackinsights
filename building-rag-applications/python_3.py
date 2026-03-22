# Hybrid search: combine semantic + keyword
retriever = vectorstore.as_retriever(
    search_type="mmr",  # Maximum Marginal Relevance
    search_kwargs={
        "k": 5,
        "fetch_k": 20,
        "lambda_mult": 0.7,  # Balance relevance vs diversity
    },
)
