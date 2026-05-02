from fastapi import APIRouter
from pydantic import BaseModel
from app.services.embedding_client import EmbeddingClient
from app.services.vector_store import VectorStore, vector_store 
from app.services.chat_client import ChatClient
import numpy as np

router = APIRouter(prefix="/query", tags=["Query"])

embedding_client = EmbeddingClient()
chat_client = ChatClient()

class QueryRequest(BaseModel):
    question: str

@router.post("/")
def query(req: QueryRequest):
    # 1. Embed query
    query_embedding = embedding_client.embed(req.question)
    print(f"Query embedding: {query_embedding}")

    # 2. Retrieve relevant chunks
    distances, indices = vector_store.index.search(
        np.array([query_embedding]).astype("float32"), k=3
    )
    print(f"Distances: {distances}")
    print(f"Indices: {indices}")

    relevant_chunks = vector_store.search(query_embedding, k=3)
    print(f"Relevant chunks: {relevant_chunks}")

    # 3. Build prompt
    context = "\n".join(relevant_chunks)

    prompt = f"""
    You are an assistant that answers questions based on the provided context.

    Context:
    {context}

    Question:
    {req.question}

    If the context does not contain the answer, respond with: "The context does not contain the answer."
    """
    print(f"Prompt: {prompt}")

    # 4. Call LLM
    answer = chat_client.chat(prompt)

    return {
        "answer": answer,
        "context_used": relevant_chunks
    }