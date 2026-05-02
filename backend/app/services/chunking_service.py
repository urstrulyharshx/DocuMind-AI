def chunk_text(text: str, chunk_size=500, overlap=50):
    if not text:
        return []

    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end]
        
        if chunk.strip():  # avoid empty chunks
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks