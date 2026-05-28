import hashlib

import psycopg

from app.core.config import Config


class EmbeddingCache:
    def __init__(self):
        self.conn = None
        self._schema_ready = False

    def get(self, text: str):
        self._ensure_schema()
        cache_key = self._cache_key(text)

        with self._get_connection().cursor() as cur:
            cur.execute(
                """
                SELECT embedding::text
                FROM embedding_cache
                WHERE cache_key = %s
                  AND model_id = %s
                  AND dimensions = %s
                """,
                (cache_key, Config.BEDROCK_EMBEDDING_MODEL, Config.EMBEDDING_DIMENSIONS),
            )
            row = cur.fetchone()
            return self._parse_embedding(row[0]) if row else None

    def set(self, text: str, embedding):
        self._ensure_schema()
        cache_key = self._cache_key(text)

        with self._get_connection().cursor() as cur:
            cur.execute(
                """
                INSERT INTO embedding_cache
                    (cache_key, model_id, dimensions, embedding)
                VALUES (%s, %s, %s, %s::vector)
                ON CONFLICT (cache_key, model_id, dimensions)
                DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW()
                """,
                (
                    cache_key,
                    Config.BEDROCK_EMBEDDING_MODEL,
                    Config.EMBEDDING_DIMENSIONS,
                    self._format_embedding(embedding),
                ),
            )

    def _ensure_schema(self):
        if self._schema_ready:
            return

        with self._get_connection().cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS embedding_cache (
                    cache_key TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    dimensions INTEGER NOT NULL,
                    embedding VECTOR({Config.EMBEDDING_DIMENSIONS}) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (cache_key, model_id, dimensions)
                )
                """
            )

        self._schema_ready = True

    def _get_connection(self):
        if self.conn is None or self.conn.closed:
            self.conn = psycopg.connect(Config.DATABASE_URL)
            self.conn.autocommit = True
        return self.conn

    def _cache_key(self, text: str):
        normalized = " ".join(text.split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _format_embedding(self, embedding):
        return "[" + ",".join(str(float(value)) for value in embedding) + "]"

    def _parse_embedding(self, value: str):
        return [float(item) for item in value.strip("[]").split(",") if item]


embedding_cache = EmbeddingCache()
