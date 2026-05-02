from app.clients.s3_client import S3Client


class UploadService:
    def __init__(self, s3_client=None):
        self._s3_client = s3_client

    def upload(self, file_obj, filename: str):
        return self._get_s3_client().upload_file(file_obj, filename)

    def _get_s3_client(self):
        if self._s3_client is None:
            self._s3_client = S3Client()
        return self._s3_client
