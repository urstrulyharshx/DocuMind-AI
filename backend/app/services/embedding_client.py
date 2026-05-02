import requests
import json
from app.core.config import Config

class EmbeddingClient:
    def __init__(self):
        self.url = Config.bedrock_url(Config.BEDROCK_EMBEDDING_MODEL)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.AWS_BEDROCK_API_KEY}"
        }

    def embed(self, text: str):
        body = {
            "inputText": text,
            "dimensions": Config.EMBEDDING_DIMENSIONS,
            "normalize": Config.EMBEDDING_NORMALIZE
        }

        response = requests.post(
            self.url,
            headers=self.headers,
            data=json.dumps(body),
            timeout=10
        )

        if response.status_code != 200:
            raise Exception(f"Embedding error: {response.text}")

        result = response.json()

        return result.get("embedding", [])