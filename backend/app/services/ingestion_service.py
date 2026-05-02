from pypdf import PdfReader

from app.clients.embedding_client import EmbeddingClient
from app.clients.s3_client import S3Client
from app.db.vector_store import vector_store
from app.utils.helpers import add_embeddings_to_store, chunk_text


class IngestionService:
    def __init__(self, s3_client=None, embedding_client=None, store=None):
        self._s3_client = s3_client
        self._embedding_client = embedding_client
        self.vector_store = store or vector_store

    def process_pdf(self, file_key: str):
        local_path = self._local_path_for(file_key)

        self._get_s3_client().download_file(file_key, local_path)
        text = self._extract_text(local_path)
        chunks = chunk_text(text)
        embeddings = self._embed_chunks(chunks)

        add_embeddings_to_store(self.vector_store, embeddings, chunks)

        return {
            "chunks": len(chunks),
            "stored_in_vector_db": len(embeddings),
        }

    def _local_path_for(self, file_key: str):
        return f"/tmp/{file_key.replace('/', '_')}"

    def _get_s3_client(self):
        if self._s3_client is None:
            self._s3_client = S3Client()
        return self._s3_client

    def _get_embedding_client(self):
        if self._embedding_client is None:
            self._embedding_client = EmbeddingClient()
        return self._embedding_client

    def _extract_text(self, file_path: str):
        reader = PdfReader(file_path)
        text_parts = []

        for i, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            except Exception as e:
                print(f"Error reading page {i}: {e}")

        full_text = "\n".join(text_parts)
        return full_text.strip()

    def _embed_chunks(self, chunks):
        embeddings = []
        for chunk in chunks:
            embeddings.append(self._get_embedding_client().embed(chunk))
        return embeddings


ingestion_service = IngestionService()


def process_pdf(file_key: str):
    return ingestion_service.process_pdf(file_key)
