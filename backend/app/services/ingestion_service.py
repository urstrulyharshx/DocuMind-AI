import uuid
from pypdf import PdfReader

from app.clients.embedding_client import EmbeddingClient
from app.clients.s3_client import S3Client
from app.db.vector_store import pgvector_store
from app.utils.helpers import chunk_text


class IngestionService:
    def __init__(self, s3_client=None, embedding_client=None, store=None):
        self._s3_client = s3_client
        self._embedding_client = embedding_client
        self.vector_store = store or pgvector_store

    def process_pdf(self, file_key: str):
        local_path = self._local_path_for(file_key)

        # 1️Generate document_id (UUID)
        document_id = str(uuid.uuid4())

        # 2️ Download file
        self._get_s3_client().download_file(file_key, local_path)

        # 3️Extract text
        text = self._extract_text(local_path)

        # 4️ Chunk text
        chunks = chunk_text(text)

        # 5️ Generate embeddings
        embeddings = self._embed_chunks(chunks)

        print(f"[INGEST] Chunks: {len(chunks)}")
        print(f"[INGEST] Embeddings: {len(embeddings)}")

        # 6️Store in DB (documents + document_chunks)
        self.vector_store.add(
            embeddings=embeddings,
            texts=chunks,
            file_id=document_id   
        )

        return {
            "chunks": len(chunks),
            "stored_in_vector_db": len(embeddings),
            "document_id": document_id,   
            "file_key": file_key
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
                print(f"[ERROR] Page {i}: {e}")

        return "\n".join(text_parts).strip()

    def _embed_chunks(self, chunks):
        embeddings = []
        client = self._get_embedding_client()

        for chunk in chunks:
            emb = client.embed(chunk)

            
            if not isinstance(emb, list):
                raise Exception("Invalid embedding format")

            embeddings.append(emb)

        return embeddings


# Singleton instance
ingestion_service = IngestionService()


def process_pdf(file_key: str):
    return ingestion_service.process_pdf(file_key)