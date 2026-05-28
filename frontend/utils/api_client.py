import requests

BASE_URL = "http://127.0.0.1:8000"


def _json_or_error(response: requests.Response):
    if response.status_code == 200:
        return response.json()

    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = response.text

    raise RuntimeError(detail or "Backend request failed")


def send_chat(query: str):
    response = requests.post(
        f"{BASE_URL}/chat/",
        json={"query": query},
    )

    if response.status_code != 200:
        return "Error: Unable to fetch response"

    return response.json().get("response", "")


def upload_pdf(uploaded_file):
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "application/pdf",
        )
    }
    response = requests.post(f"{BASE_URL}/upload/", files=files)
    return _json_or_error(response)


def ingest_pdf(file_key: str):
    response = requests.post(
        f"{BASE_URL}/ingest/",
        json={"file_key": file_key},
    )
    return _json_or_error(response)


def query_document(question: str, document_id: str):
    response = requests.post(
        f"{BASE_URL}/query/",
        json={
            "question": question,
            "document_id": document_id,
        },
    )
    return _json_or_error(response)


def list_documents():
    response = requests.get(f"{BASE_URL}/documents/")
    return _json_or_error(response)


def get_document_chunks(document_id: str, limit: int = 100):
    response = requests.get(
        f"{BASE_URL}/documents/{document_id}/chunks",
        params={"limit": limit},
    )
    return _json_or_error(response)


def delete_document(document_id: str):
    response = requests.delete(f"{BASE_URL}/documents/{document_id}")
    return _json_or_error(response)
