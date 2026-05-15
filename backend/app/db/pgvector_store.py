import hashlib
import uuid

import psycopg
from psycopg.types.json import Jsonb

from app.core.config import Config


class PGVectorStore:
    def __init__(self):
        self.conn = None

    def add(self, embeddings, texts, file_id):
        document_id = self._document_id(file_id)
        document_metadata = self._document_metadata(texts)
        file_name = document_metadata.get("file_name") or self._file_name(file_id)
        s3_key = document_metadata.get("file_key") or str(file_id)

        with self._get_connection().cursor() as cur:
            cur.execute(
                """
                DELETE FROM documents
                WHERE s3_key = %s
                  AND id <> %s
                """,
                (s3_key, document_id),
            )

            cur.execute(
                """
                INSERT INTO documents (id, file_name, s3_key, metadata, status)
                VALUES (%s, %s, %s, %s, 'indexed')
                ON CONFLICT (id) DO UPDATE SET
                    file_name = EXCLUDED.file_name,
                    s3_key = EXCLUDED.s3_key,
                    metadata = EXCLUDED.metadata,
                    status = EXCLUDED.status,
                    updated_at = NOW()
                """,
                (document_id, file_name, s3_key, Jsonb(document_metadata)),
            )

            cur.execute(
                """
                DELETE FROM document_chunks
                WHERE document_id = %s
                """,
                (document_id,),
            )

            records = []
            for index, (embedding, chunk) in enumerate(zip(embeddings, texts)):
                chunk_record = self._chunk_record(chunk, index)
                records.append(
                    (
                        document_id,
                        chunk_record["text"],
                        chunk_record["chunk_index"],
                        chunk_record["page_number"],
                        self._format_embedding(embedding),
                        Jsonb(chunk_record["metadata"]),
                    )
                )

            if records:
                cur.executemany(
                    """
                    INSERT INTO document_chunks
                        (document_id, chunk_text, chunk_index, page_number, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s::vector, %s)
                    """,
                    records,
                )

    def search(self, query_embedding, file_id=None, k=5):
        embedding = self._format_embedding(query_embedding)

        with self._get_connection().cursor() as cur:
            if file_id:
                cur.execute(
                    """
                    SELECT chunk_text
                    FROM document_chunks
                    WHERE document_id = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (self._document_id(file_id), embedding, k),
                )
            else:
                cur.execute(
                    """
                    SELECT chunk_text
                    FROM document_chunks
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (embedding, k),
                )

            return [row[0] for row in cur.fetchall()]

    def _document_id(self, file_id):
        try:
            return str(uuid.UUID(str(file_id)))
        except ValueError:
            digest = hashlib.sha256(str(file_id).encode("utf-8")).hexdigest()
            return str(uuid.UUID(digest[:32]))

    def _get_connection(self):
        if self.conn is None or self.conn.closed:
            self.conn = psycopg.connect(Config.DATABASE_URL)
            self.conn.autocommit = True
        return self.conn

    def _file_name(self, file_id):
        return str(file_id).rstrip("/").split("/")[-1] or str(file_id)

    def _document_metadata(self, texts):
        for chunk in texts:
            if isinstance(chunk, dict):
                metadata = chunk.get("metadata") or {}
                return {
                    "file_key": metadata.get("file_key"),
                    "file_name": metadata.get("file_name"),
                }
        return {}

    def _chunk_record(self, chunk, fallback_index):
        if isinstance(chunk, dict):
            return {
                "text": chunk.get("text", ""),
                "chunk_index": chunk.get("chunk_index", fallback_index),
                "page_number": chunk.get("page_number"),
                "metadata": chunk.get("metadata") or {},
            }

        return {
            "text": chunk,
            "chunk_index": fallback_index,
            "page_number": None,
            "metadata": {},
        }

    def _format_embedding(self, embedding):
        if isinstance(embedding, dict):
            embedding = embedding.get("embedding", [])
        return "[" + ",".join(str(value) for value in embedding) + "]"


pgvector_store = PGVectorStore()
