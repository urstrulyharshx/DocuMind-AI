from app.clients.chat_client import ChatClient


class ChatService:
    def __init__(self, chat_client=None):
        self.chat_client = chat_client or ChatClient()

    def chat(self, query: str):
        return self.chat_client.chat(query)

