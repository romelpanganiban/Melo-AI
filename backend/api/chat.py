from fastapi import APIRouter
from pydantic import BaseModel

from services.chat_service import ChatService

router = APIRouter()

service = ChatService()


class ChatRequest(BaseModel):
    session_id: str
    message: str


@router.post("/chat")
def chat(request: ChatRequest):

    return service.process_message(
        request.session_id,
        request.message
    )

@router.get("/history/{session_id}")
def history(session_id: str):

    return service.get_history(
        session_id
    )
