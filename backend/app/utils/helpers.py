def chunk_text(text: str, chunk_size=900, overlap=120):
    if not text:
        return []

    chunks = []
    current_parts = []
    current_length = 0

    for paragraph in _paragraphs(text):
        paragraph_length = len(paragraph)

        if paragraph_length > chunk_size:
            if current_parts:
                chunks.append(" ".join(current_parts).strip())
                current_parts = []
                current_length = 0
            chunks.extend(_sliding_chunks(paragraph, chunk_size, overlap))
            continue

        projected_length = current_length + paragraph_length + 1
        if current_parts and projected_length > chunk_size:
            chunks.append(" ".join(current_parts).strip())
            current_parts = _overlap_parts(current_parts, overlap)
            current_length = sum(len(part) + 1 for part in current_parts)

        current_parts.append(paragraph)
        current_length += paragraph_length + 1

    if current_parts:
        chunks.append(" ".join(current_parts).strip())

    return [chunk for chunk in chunks if chunk]


def _paragraphs(text: str):
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = [block.strip() for block in normalized.split("\n\n") if block.strip()]
    if blocks:
        return blocks

    return [line.strip() for line in normalized.split("\n") if line.strip()]


def _sliding_chunks(text: str, chunk_size: int, overlap: int):
    chunks = []
    start = 0
    step = max(1, chunk_size - overlap)
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks


def _overlap_parts(parts, overlap):
    if overlap <= 0:
        return []

    selected = []
    total = 0

    for part in reversed(parts):
        selected.append(part)
        total += len(part)
        if total >= overlap:
            break

    return list(reversed(selected))
