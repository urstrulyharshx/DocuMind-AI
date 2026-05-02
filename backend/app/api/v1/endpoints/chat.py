from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])
chat_service = ChatService()


@router.post("/", response_model=ChatResponse)
def chat(chat_request: ChatRequest):
    response = chat_service.chat(chat_request.query)
    return ChatResponse(response=response)

