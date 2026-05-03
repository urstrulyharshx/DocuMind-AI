import time
import requests
from app.core.config import Config


class EmbeddingClient:
    def __init__(self):
        self.url = Config.bedrock_url(Config.BEDROCK_EMBEDDING_MODEL)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.AWS_BEDROCK_API_KEY}",
        }

    def embed(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Input text for embedding is empty")

        body = {
            "inputText": text,
            "dimensions": Config.EMBEDDING_DIMENSIONS,
            "normalize": Config.EMBEDDING_NORMALIZE,
        }

        retries = 3
        last_error = None

        for attempt in range(retries):
            try:
                print(f"[Embedding] Attempt {attempt + 1}")

                response = requests.post(
                    self.url,
                    headers=self.headers,
                    json=body,
                    timeout=30,   #  increased timeout
                )

                if response.status_code != 200:
                    raise Exception(f"Bedrock error: {response.text}")

                result = response.json()
                embedding = result.get("embedding")

                # validation
                if not embedding or not isinstance(embedding, list):
                    raise Exception("Invalid embedding response")

                #ensure float values
                embedding = [float(x) for x in embedding]

                return embedding  # success → exit immediately

            except Exception as e:
                last_error = e
                print(f"[Retry {attempt + 1}] Embedding failed: {e}")
                time.sleep(2)

        # nly reached if all retries fail
        raise Exception(f"Embedding failed after {retries} attempts: {last_error}")