from app.clients.embedding_client import EmbeddingClient
from app.db.embedding_cache import embedding_cache


class EmbeddingService:
    def __init__(self, embedding_client=None, cache=None):
        self.embedding_client = embedding_client or EmbeddingClient()
        self.cache = cache or embedding_cache

    def embed(self, text: str):
        cached_embedding = self.cache.get(text)
        if cached_embedding is not None:
            print("[EmbeddingCache] hit")
            return cached_embedding

        print("[EmbeddingCache] miss")
        embedding = self.embedding_client.embed(text)
        self.cache.set(text, embedding)
        return embedding
