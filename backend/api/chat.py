from fastapi import APIRouter
from pydantic import BaseModel

from services.chat_service import ChatService

router = APIRouter()

service = ChatService()


class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
def chat(request: ChatRequest):

    service.add_message("user", request.message)

    history = service.get_history()

    last_messages = history[-5:]

    response = (
        f"Hello! I currently remember "
        f"{len(history)} messages in this conversation."
    )

    service.add_message(
        "assistant",
        response
    )

    return {
        "response": response,
        "recent_history": last_messages
    }

@router.get("/history")
def history():
    return service.get_history()