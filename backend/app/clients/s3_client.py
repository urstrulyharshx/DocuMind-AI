import boto3
import botocore.exceptions

from app.core.config import Config


class S3Client:
    def __init__(self):
        self.bucket = Config.S3_BUCKET_NAME
        self.client = boto3.client(
            "s3",
            region_name=Config.AWS_REGION,
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
        )

    def upload_file(self, file_obj, filename: str):
        self.client.upload_fileobj(file_obj, self.bucket, filename)
        return f"s3://{self.bucket}/{filename}"

    def download_file(self, key: str, local_path: str):
        try:
            self.client.download_file(self.bucket, key, local_path)
            return local_path
        except botocore.exceptions.ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                raise FileNotFoundError(f"S3 object not found: s3://{self.bucket}/{key}") from exc
            raise


def upload_file_to_s3(file_obj, filename: str):
    return S3Client().upload_file(file_obj, filename)

