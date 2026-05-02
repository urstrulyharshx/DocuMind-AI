from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ingestion_service import process_pdf

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

class IngestRequest(BaseModel):
    file_key: str

@router.post("/")
def ingest(req: IngestRequest):
    result = process_pdf(req.file_key)
    return result