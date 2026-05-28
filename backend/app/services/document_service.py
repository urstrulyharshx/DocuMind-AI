from app.db.vector_store import pgvector_store


class DocumentService:
    def __init__(self, store=None):
        self.vector_store = store or pgvector_store

    def list_documents(self):
        return {"documents": self.vector_store.list_documents()}

    def get_document(self, document_id: str):
        return self.vector_store.get_document(document_id)

    def get_chunks(self, document_id: str, limit: int = 100):
        return {
            "document_id": document_id,
            "chunks": self.vector_store.get_document_chunks(document_id, limit=limit),
        }

    def delete_document(self, document_id: str):
        return self.vector_store.delete_document(document_id)


document_service = DocumentService()
