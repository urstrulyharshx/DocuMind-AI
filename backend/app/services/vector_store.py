import faiss
import numpy as np
import pickle
import os

class VectorStore:
    def __init__(self, dim: int, index_path="faiss.index", meta_path="meta.pkl"):
        self.dim = dim
        self.index_path = index_path
        self.meta_path = meta_path

        # Load index and metadata if they exist
        if os.path.exists(index_path) and os.path.exists(meta_path):
            self.index = faiss.read_index(index_path)
            with open(meta_path, "rb") as f:
                self.texts = pickle.load(f)
        else:
            self.index = faiss.IndexFlatL2(dim)
            self.texts = []

    def add(self, embeddings, texts):
        vectors = np.array(embeddings).astype("float32")
        self.index.add(vectors)
        self.texts.extend(texts)

        # Save index and metadata to disk
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.texts, f)

    def search(self, query_embedding, k=3):
        if self.index.ntotal == 0:
            return []

        query = np.array([query_embedding]).astype("float32")
        distances, indices = self.index.search(query, k)

        results = []
        for idx in indices[0]:
            if idx == -1:  # Skip invalid indices
                continue
            if 0 <= idx < len(self.texts):  # Ensure index is within bounds
                results.append(self.texts[idx])

        return results

# Global instance of VectorStore
vector_store = VectorStore(dim=1024)