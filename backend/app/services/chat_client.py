import requests
import json
from app.core.config import Config

class ChatClient:
    def __init__(self):
        self.url = Config.bedrock_url(Config.BEDROCK_CHAT_MODEL)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.AWS_BEDROCK_API_KEY}"
        }

    def chat(self, prompt: str):
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 100,
                "temperature": 0.5
            }
        }

        response = requests.post(
            self.url,
            headers=self.headers,
            data=json.dumps(body),
            timeout=15
        )

        if response.status_code != 200:
            raise Exception(f"Chat error: {response.text}")

        result = response.json()
        return result["output"]["message"]["content"][0]["text"]