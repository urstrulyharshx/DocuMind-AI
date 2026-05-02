from app.services.embedding_client import EmbeddingClient
from app.services.vector_store import VectorStore
from app.services.pdf_loader import download_from_s3, extract_text_from_pdf
from app.services.chunking_service import chunk_text

embedding_client = EmbeddingClient()
vector_store = VectorStore(dim=1024)

def process_pdf(file_key: str):
    local_path = f"/tmp/{file_key.replace('/', '_')}"

    download_from_s3(file_key, local_path)
    text = extract_text_from_pdf(local_path)

    chunks = chunk_text(text)

    embeddings = []
    for chunk in chunks:
        emb = embedding_client.embed(chunk)
        embeddings.append(emb)

    # Store in FAISS
    vector_store.add(embeddings, chunks)

    return {
        "chunks": len(chunks),
        "stored_in_vector_db": len(embeddings)
    }