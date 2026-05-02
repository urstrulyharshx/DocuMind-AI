def chunk_text(text: str, chunk_size=500, overlap=50):
    if not text:
        return []

    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def add_embeddings_to_store(store, embeddings, texts):
    store.add(embeddings, texts)


def search_similar_chunks(store, query_embedding, k=3):
    return store.search(query_embedding, k=k)

