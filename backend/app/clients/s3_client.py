import boto3

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
        self.client.download_file(self.bucket, key, local_path)
        return local_path


def upload_file_to_s3(file_obj, filename: str):
    return S3Client().upload_file(file_obj, filename)

