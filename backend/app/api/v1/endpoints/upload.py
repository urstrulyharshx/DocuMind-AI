from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.upload_service import UploadService

router = APIRouter(prefix="/upload", tags=["Upload"])
upload_service = UploadService()


@router.post("/")
def upload(file: UploadFile = File(...)):
    try:
        file_path = upload_service.upload(file.file, file.filename)
        return {"file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

