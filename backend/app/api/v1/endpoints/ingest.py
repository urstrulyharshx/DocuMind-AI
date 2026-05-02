from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ingestion_service import ingestion_service

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


class IngestRequest(BaseModel):
    file_key: str


@router.post("/")
def ingest(req: IngestRequest):
    return ingestion_service.process_pdf(req.file_key)

