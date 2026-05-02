from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.s3_service import upload_file_to_s3

router = APIRouter(prefix="/upload", tags=["Upload"])

@router.post("/")
def upload(file: UploadFile = File(...)):
    try:
        file_path = upload_file_to_s3(file.file, file.filename)
        return {"file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))