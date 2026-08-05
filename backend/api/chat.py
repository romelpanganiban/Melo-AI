from fastapi import APIRouter
from pydantic import BaseModel

from memory.memory_manager import MemoryManager

router = APIRouter()

memory = MemoryManager()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
def chat(request: ChatRequest):

    memory.add_message("user", request.message)

    history = memory.get_history()

    response = f"""
Message received.

Current message:
{request.message}

Messages stored:
{len(history)}
"""

    memory.add_message(
        "assistant",
        response
    )

    return {
        "response": response,
        "history_count": len(history)
    }

@router.get("/history")
def history():
    return memory.get_history()