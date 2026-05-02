from fastapi import APIRouter
from app.services.chat_client import ChatClient
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


chat_client = ChatClient()

@router.post("/",response_model=ChatResponse)
def chat(chat_request: ChatRequest):
    response = chat_client.chat(chat_request.query)
    return ChatResponse(response=response)