from app.clients.chat_client import ChatClient
from app.clients.embedding_client import EmbeddingClient
from app.db.vector_store import pgvector_store


class QueryService:
    def __init__(self, embedding_client=None, chat_client=None, store=None):
        self.embedding_client = embedding_client or EmbeddingClient()
        self.chat_client = chat_client or ChatClient()
        self.vector_store = store or pgvector_store

    def query(self, question: str, document_id: str):
        query_embedding = self.embedding_client.embed(question)
        retrieved_chunks = self.vector_store.search_with_metadata(
            query_embedding,
            file_id=document_id,
            k=5,
        )
        relevant_chunks = [chunk["chunk_text"] for chunk in retrieved_chunks]

        if not relevant_chunks:
            return {
                "answer": "No relevant information found in the document.",
                "context_used": [],
                "sources": [],
            }

        prompt = self._build_prompt(question, relevant_chunks)
        answer = self.chat_client.chat(prompt)

        return {
            "answer": answer,
            "context_used": relevant_chunks,
            "sources": self._format_sources(retrieved_chunks),
        }

    def _build_prompt(self, question: str, relevant_chunks):
        context = "\n\n".join(relevant_chunks)

        return f"""
            You are an AI assistant answering questions strictly from the provided document.

            Rules:
            - Use ONLY the context below
            - If answer is not present, say: "Not found in document"
            - Be precise and concise

            Context:
            {context}

            Question:
            {question}

            Answer:
            """

    def _format_sources(self, retrieved_chunks):
        sources = []

        for chunk in retrieved_chunks:
            sources.append(
                {
                    "file_name": chunk.get("file_name"),
                    "file_key": chunk.get("file_key"),
                    "page_number": chunk.get("page_number"),
                    "chunk_index": chunk.get("chunk_index"),
                    "similarity_score": round(chunk.get("similarity_score", 0), 4),
                    "distance": round(chunk.get("distance", 0), 4),
                }
            )

        return sources
