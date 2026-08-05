from fastapi import APIRouter
from pydantic import BaseModel

from memory.session_manager import SessionManager

router = APIRouter()

manager = SessionManager()


class RenameSessionRequest(BaseModel):
    title: str


@router.post("/sessions")
def create_session():
    return manager.create_session()


@router.get("/sessions")
def get_sessions():
    return manager.get_sessions()


@router.put("/sessions/{session_id}")
def rename_session(
    session_id: str,
    request: RenameSessionRequest
):
    return manager.rename_session(
        session_id,
        request.title
    )


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    return manager.delete_session(session_id)