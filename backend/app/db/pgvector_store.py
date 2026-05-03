import hashlib
import uuid

import psycopg

from app.core.config import Config


class PGVectorStore:
    def __init__(self):
        self.conn = psycopg.connect(Config.DATABASE_URL)
        self.conn.autocommit = True

    def add(self, embeddings, texts, file_id):
        document_id = self._document_id(file_id)
        file_name = self._file_name(file_id)

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (id, file_name, s3_key)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (document_id, file_name, file_id),
            )

            records = []
            for i, (embedding, text) in enumerate(zip(embeddings, texts)):
                records.append(
                    (
                        document_id,
                        text,
                        i,
                        self._format_embedding(embedding),
                    )
                )

            cur.executemany(
                """
                INSERT INTO document_chunks
                    (document_id, chunk_text, chunk_index, embedding)
                VALUES (%s, %s, %s, %s::vector)
                """,
                records,
            )

    def search(self, query_embedding, file_id=None, k=5):
        embedding = self._format_embedding(query_embedding)

        with self.conn.cursor() as cur:
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

    def _file_name(self, file_id):
        return str(file_id).rstrip("/").split("/")[-1] or str(file_id)

    def _format_embedding(self, embedding):
        if isinstance(embedding, dict):
            embedding = embedding.get("embedding", [])
        return "[" + ",".join(str(value) for value in embedding) + "]"


pgvector_store = PGVectorStore()
