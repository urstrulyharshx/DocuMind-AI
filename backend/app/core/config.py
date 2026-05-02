import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # AWS
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_BEDROCK_API_KEY = os.getenv("AWS_BEDROCK_API_KEY")

    # Models
    BEDROCK_CHAT_MODEL = os.getenv("BEDROCK_CHAT_MODEL", "amazon.nova-lite-v1:0")
    BEDROCK_EMBEDDING_MODEL = os.getenv(
        "BEDROCK_EMBEDDING_MODEL",
        "amazon.titan-embed-text-v2:0"
    )

    # Embedding settings
    EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", 1024))
    EMBEDDING_NORMALIZE = os.getenv("EMBEDDING_NORMALIZE", "true").lower() == "true"

    #S3 configuration
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "my-app-bucket")
    S3_REGION = os.getenv("S3_REGION", AWS_REGION)

    # Database
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "documind")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "documind")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "documind_password")
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        (
            f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
            f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        ),
    )

    # Base URL
    @staticmethod
    def bedrock_url(model_id: str):
        return f"https://bedrock-runtime.{Config.AWS_REGION}.amazonaws.com/model/{model_id}/invoke"
