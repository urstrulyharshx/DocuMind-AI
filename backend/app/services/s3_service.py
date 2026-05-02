import boto3
from app.core.config import Config

def get_s3_client():
    return boto3.client(
        "s3",
        region_name=Config.AWS_REGION,
        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    )

def upload_file_to_s3(file_obj, filename: str):
    s3 = get_s3_client()
    bucket = Config.S3_BUCKET_NAME

    # Upload
    s3.upload_fileobj(file_obj, bucket, filename)

    # Return S3 path
    return f"s3://{bucket}/{filename}"