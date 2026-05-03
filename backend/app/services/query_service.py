from app.clients.chat_client import ChatClient
from app.clients.embedding_client import EmbeddingClient
from app.db.vector_store import pgvector_store


class QueryService:
    def __init__(self, embedding_client=None, chat_client=None, store=None):
        self.embedding_client = embedding_client or EmbeddingClient()
        self.chat_client = chat_client or ChatClient()
        self.vector_store = store or pgvector_store

    def query(self, question: str, document_id: str):
        # 1️Embed query
        query_embedding = self.embedding_client.embed(question)

        # 2️etrieve relevant chunks (filtered)
        relevant_chunks = self.vector_store.search(
            query_embedding,
            file_id=document_id,   
            k=5                    
        )

        # 3️Handle empty case
        if not relevant_chunks:
            return {
                "answer": "No relevant information found in the document.",
                "context_used": []
            }

        # 4️Build prompt
        prompt = self._build_prompt(question, relevant_chunks)

        # 5️ Generate answer
        answer = self.chat_client.chat(prompt)

        return {
            "answer": answer,
            "context_used": relevant_chunks,
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