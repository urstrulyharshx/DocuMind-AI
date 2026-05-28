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
        results = self.search_with_metadata(query_embedding, file_id=file_id, k=k)
        return [result["chunk_text"] for result in results]

    def search_with_metadata(self, query_embedding, file_id=None, k=5):
        embedding = self._format_embedding(query_embedding)

        with self._get_connection().cursor() as cur:
            if file_id:
                cur.execute(
                    """
                    SELECT
                        dc.document_id,
                        dc.chunk_text,
                        dc.page_number,
                        dc.chunk_index,
                        dc.metadata,
                        d.file_name,
                        d.s3_key,
                        dc.embedding <=> %s::vector AS distance
                    FROM document_chunks
                    dc
                    JOIN documents d ON d.id = dc.document_id
                    WHERE dc.document_id = %s
                    ORDER BY dc.embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (embedding, self._document_id(file_id), embedding, k),
                )
            else:
                cur.execute(
                    """
                    SELECT
                        dc.document_id,
                        dc.chunk_text,
                        dc.page_number,
                        dc.chunk_index,
                        dc.metadata,
                        d.file_name,
                        d.s3_key,
                        dc.embedding <=> %s::vector AS distance
                    FROM document_chunks dc
                    JOIN documents d ON d.id = dc.document_id
                    ORDER BY dc.embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (embedding, embedding, k),
                )

            return [self._search_result(row) for row in cur.fetchall()]

    def search_hybrid(self, query_text, query_embedding, file_id=None, k=5, candidate_k=20):
        vector_results = self.search_with_metadata(
            query_embedding,
            file_id=file_id,
            k=candidate_k,
        )
        keyword_results = self._keyword_search(
            query_text,
            file_id=file_id,
            k=candidate_k,
        )

        return self._merge_hybrid_results(vector_results, keyword_results, k)

    def list_documents(self):
        with self._get_connection().cursor() as cur:
            cur.execute(
                """
                SELECT
                    d.id,
                    d.file_name,
                    d.s3_key,
                    d.status,
                    d.created_at,
                    d.updated_at,
                    COUNT(dc.id) AS chunk_count
                FROM documents d
                LEFT JOIN document_chunks dc ON dc.document_id = d.id
                GROUP BY d.id
                ORDER BY d.updated_at DESC
                """
            )
            return [self._document_result(row) for row in cur.fetchall()]

    def get_document(self, document_id):
        with self._get_connection().cursor() as cur:
            cur.execute(
                """
                SELECT
                    d.id,
                    d.file_name,
                    d.s3_key,
                    d.status,
                    d.created_at,
                    d.updated_at,
                    COUNT(dc.id) AS chunk_count
                FROM documents d
                LEFT JOIN document_chunks dc ON dc.document_id = d.id
                WHERE d.id = %s
                GROUP BY d.id
                """,
                (self._document_id(document_id),),
            )
            row = cur.fetchone()
            return self._document_result(row) if row else None

    def get_document_chunks(self, document_id, limit=100):
        with self._get_connection().cursor() as cur:
            cur.execute(
                """
                SELECT
                    chunk_text,
                    page_number,
                    chunk_index,
                    metadata
                FROM document_chunks
                WHERE document_id = %s
                ORDER BY chunk_index ASC
                LIMIT %s
                """,
                (self._document_id(document_id), limit),
            )
            return [self._chunk_result(row) for row in cur.fetchall()]

    def delete_document(self, document_id):
        with self._get_connection().cursor() as cur:
            cur.execute(
                """
                DELETE FROM documents
                WHERE id = %s
                RETURNING id
                """,
                (self._document_id(document_id),),
            )
            return cur.fetchone() is not None

    def _keyword_search(self, query_text, file_id=None, k=20):
        with self._get_connection().cursor() as cur:
            if file_id:
                cur.execute(
                    """
                    SELECT
                        dc.document_id,
                        dc.chunk_text,
                        dc.page_number,
                        dc.chunk_index,
                        dc.metadata,
                        d.file_name,
                        d.s3_key,
                        ts_rank_cd(
                            to_tsvector('english', dc.chunk_text),
                            plainto_tsquery('english', %s)
                        ) AS keyword_score
                    FROM document_chunks dc
                    JOIN documents d ON d.id = dc.document_id
                    WHERE dc.document_id = %s
                      AND to_tsvector('english', dc.chunk_text) @@ plainto_tsquery('english', %s)
                    ORDER BY keyword_score DESC
                    LIMIT %s
                    """,
                    (query_text, self._document_id(file_id), query_text, k),
                )
            else:
                cur.execute(
                    """
                    SELECT
                        dc.document_id,
                        dc.chunk_text,
                        dc.page_number,
                        dc.chunk_index,
                        dc.metadata,
                        d.file_name,
                        d.s3_key,
                        ts_rank_cd(
                            to_tsvector('english', dc.chunk_text),
                            plainto_tsquery('english', %s)
                        ) AS keyword_score
                    FROM document_chunks dc
                    JOIN documents d ON d.id = dc.document_id
                    WHERE to_tsvector('english', dc.chunk_text) @@ plainto_tsquery('english', %s)
                    ORDER BY keyword_score DESC
                    LIMIT %s
                    """,
                    (query_text, query_text, k),
                )

            return [self._keyword_result(row) for row in cur.fetchall()]

    def _merge_hybrid_results(self, vector_results, keyword_results, k):
        merged = {}
        max_keyword_score = max(
            [result.get("keyword_score", 0) for result in keyword_results] or [0]
        )

        for rank, result in enumerate(vector_results):
            key = self._result_key(result)
            result["semantic_rank"] = rank + 1
            result["keyword_score"] = 0
            result["keyword_score_normalized"] = 0
            result["hybrid_score"] = 0.7 * result.get("similarity_score", 0)
            result["retrieval_mode"] = "semantic"
            merged[key] = result

        for rank, result in enumerate(keyword_results):
            key = self._result_key(result)
            normalized_keyword_score = (
                result["keyword_score"] / max_keyword_score
                if max_keyword_score
                else 0
            )

            if key not in merged:
                result["similarity_score"] = 0
                result["distance"] = None
                result["semantic_rank"] = None
                result["retrieval_mode"] = "keyword"
                merged[key] = result

            merged[key]["keyword_rank"] = rank + 1
            merged[key]["keyword_score"] = result["keyword_score"]
            merged[key]["keyword_score_normalized"] = normalized_keyword_score
            merged[key]["hybrid_score"] = (
                0.7 * merged[key].get("similarity_score", 0)
                + 0.3 * normalized_keyword_score
            )
            if merged[key]["retrieval_mode"] == "semantic":
                merged[key]["retrieval_mode"] = "hybrid"

        return sorted(
            merged.values(),
            key=lambda result: result.get("hybrid_score", 0),
            reverse=True,
        )[:k]

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

    def _search_result(self, row):
        document_id, chunk_text, page_number, chunk_index, metadata, file_name, s3_key, distance = row
        similarity_score = max(0.0, 1.0 - float(distance))

        return {
            "document_id": str(document_id),
            "chunk_text": chunk_text,
            "page_number": page_number,
            "chunk_index": chunk_index,
            "similarity_score": similarity_score,
            "distance": float(distance),
            "file_name": file_name,
            "file_key": s3_key,
            "metadata": metadata or {},
        }

    def _keyword_result(self, row):
        document_id, chunk_text, page_number, chunk_index, metadata, file_name, s3_key, keyword_score = row
        return {
            "document_id": str(document_id),
            "chunk_text": chunk_text,
            "page_number": page_number,
            "chunk_index": chunk_index,
            "keyword_score": float(keyword_score),
            "file_name": file_name,
            "file_key": s3_key,
            "metadata": metadata or {},
        }

    def _result_key(self, result):
        return (
            result.get("document_id"),
            result.get("page_number"),
            result.get("chunk_index"),
        )

    def _document_result(self, row):
        document_id, file_name, s3_key, status, created_at, updated_at, chunk_count = row
        display_name = self._display_name(file_name, s3_key, document_id)
        return {
            "document_id": str(document_id),
            "file_name": file_name,
            "display_name": display_name,
            "file_key": s3_key,
            "status": status,
            "chunk_count": chunk_count,
            "created_at": created_at.isoformat() if created_at else None,
            "updated_at": updated_at.isoformat() if updated_at else None,
        }

    def _chunk_result(self, row):
        chunk_text, page_number, chunk_index, metadata = row
        return {
            "chunk_text": chunk_text,
            "page_number": page_number,
            "chunk_index": chunk_index,
            "metadata": metadata or {},
        }

    def _display_name(self, file_name, s3_key, document_id):
        if file_name and not self._is_uuid_like(file_name):
            return file_name

        if s3_key and not self._is_uuid_like(s3_key):
            return self._file_name(s3_key)

        return f"Document {str(document_id)[:8]}"

    def _is_uuid_like(self, value):
        try:
            uuid.UUID(str(value))
            return True
        except ValueError:
            return False

    def _format_embedding(self, embedding):
        if isinstance(embedding, dict):
            embedding = embedding.get("embedding", [])
        return "[" + ",".join(str(value) for value in embedding) + "]"


pgvector_store = PGVectorStore()
