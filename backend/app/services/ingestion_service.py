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

        document_id = str(uuid.uuid4())

        self._get_s3_client().download_file(file_key, local_path)

        chunk_records = self._build_chunk_records(local_path, file_key)
        embeddings = self._embed_chunks([chunk["text"] for chunk in chunk_records])

        print(f"[INGEST] Chunks: {len(chunk_records)}")
        print(f"[INGEST] Embeddings: {len(embeddings)}")

        self.vector_store.add(
            embeddings=embeddings,
            texts=chunk_records,
            file_id=document_id,
        )

        return {
            "chunks": len(chunk_records),
            "stored_in_vector_db": len(embeddings),
            "document_id": document_id,
            "file_key": file_key,
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

    def _extract_pages(self, file_path: str):
        reader = PdfReader(file_path)
        pages = []

        for page_index, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text:
                    pages.append(
                        {
                            "page_number": page_index,
                            "text": page_text.strip(),
                        }
                    )
            except Exception as e:
                print(f"[ERROR] Page {page_index}: {e}")

        return pages

    def _build_chunk_records(self, file_path: str, file_key: str):
        chunk_records = []
        global_chunk_index = 0

        for page in self._extract_pages(file_path):
            page_chunks = chunk_text(page["text"])

            for page_chunk_index, text in enumerate(page_chunks):
                chunk_records.append(
                    {
                        "text": text,
                        "page_number": page["page_number"],
                        "chunk_index": global_chunk_index,
                        "metadata": {
                            "file_key": file_key,
                            "file_name": self._file_name(file_key),
                            "page_chunk_index": page_chunk_index,
                        },
                    }
                )
                global_chunk_index += 1

        return chunk_records

    def _file_name(self, file_key: str):
        return file_key.rstrip("/").split("/")[-1] or file_key

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
