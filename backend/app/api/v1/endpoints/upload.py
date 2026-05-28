from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import Config
from app.services.upload_service import UploadService

router = APIRouter(prefix="/upload", tags=["Upload"])
upload_service = UploadService()


@router.post("/")
def upload(file: UploadFile = File(...)):
    try:
        _validate_pdf_upload(file)
        file_path = upload_service.upload(file.file, file.filename)
        return {"file_path": file_path}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


def _validate_pdf_upload(file: UploadFile):
    filename = file.filename or ""
    content_type = file.content_type or ""

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    if content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    max_bytes = Config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"PDF size must be {Config.MAX_UPLOAD_SIZE_MB} MB or less",
        )
