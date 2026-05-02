from app.clients.chat_client import ChatClient
from app.clients.embedding_client import EmbeddingClient
from app.db.vector_store import vector_store
from app.utils.helpers import search_similar_chunks


class QueryService:
    def __init__(self, embedding_client=None, chat_client=None, store=None):
        self.embedding_client = embedding_client or EmbeddingClient()
        self.chat_client = chat_client or ChatClient()
        self.vector_store = store or vector_store

    def query(self, question: str):
        query_embedding = self.embedding_client.embed(question)
        relevant_chunks = search_similar_chunks(self.vector_store, query_embedding, k=3)
        prompt = self._build_prompt(question, relevant_chunks)
        answer = self.chat_client.chat(prompt)

        return {
            "answer": answer,
            "context_used": relevant_chunks,
        }

    def _build_prompt(self, question: str, relevant_chunks):
        context = "\n".join(relevant_chunks)

        return f"""
    You are an assistant that answers questions based on the provided context.

    Context:
    {context}

    Question:
    {question}

    If the context does not contain the answer, respond with: "The context does not contain the answer."
    """
