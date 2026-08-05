from fastapi import APIRouter
from pydantic import BaseModel

from services.chat_service import ChatService

router = APIRouter()

service = ChatService()


class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
def chat(request: ChatRequest):

    memory.add_message("user", request.message)

    history = memory.get_history()

    last_messages = history[-5:]

    response = (
        f"Hello! I currently remember "
        f"{len(history)} messages in this conversation."
    )

    memory.add_message(
        "assistant",
        response
    )

    return {
        "response": response,
        "recent_history": last_messages
    }

@router.get("/history")
def history():
    return memory.get_history()