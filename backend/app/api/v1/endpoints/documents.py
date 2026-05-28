from fastapi import APIRouter, HTTPException, Query

from app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/")
def list_documents():
    return document_service.list_documents()


@router.get("/{document_id}")
def get_document(document_id: str):
    document = document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/chunks")
def get_document_chunks(document_id: str, limit: int = Query(default=100, ge=1, le=500)):
    document = document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document_service.get_chunks(document_id, limit=limit)


@router.delete("/{document_id}")
def delete_document(document_id: str):
    deleted = document_service.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": True, "document_id": document_id}
