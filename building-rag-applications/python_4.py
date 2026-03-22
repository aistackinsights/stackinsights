from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant. Answer the question based ONLY
    on the provided context. If the context doesn't contain enough information,
    say so clearly. Cite your sources by referencing document names.

    Context:
    {context}"""),
    ("human", "{question}"),
])
