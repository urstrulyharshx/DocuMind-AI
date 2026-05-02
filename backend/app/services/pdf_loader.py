import boto3
import os
from pypdf import PdfReader
from app.core.config import Config

def download_from_s3(key: str, local_path: str):
    s3 = boto3.client(
        "s3",
        region_name=Config.AWS_REGION,
        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
    )

    s3.download_file(Config.S3_BUCKET_NAME, key, local_path)


def extract_text_from_pdf(file_path: str):
    reader = PdfReader(file_path)
    text_parts = []

    for i, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        except Exception as e:
            print(f"Error reading page {i}: {e}")

    full_text = "\n".join(text_parts)
    return full_text.strip()