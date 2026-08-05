from fastapi import APIRouter
from pydantic import BaseModel

from services.session_service import SessionService

router = APIRouter()

service = SessionService()


class RenameSessionRequest(BaseModel):
    title: str


@router.post("/sessions")
def create_session():
    return service.create_session()


@router.get("/sessions")
def get_sessions():
    return service.get_sessions()


@router.put("/sessions/{session_id}")
def rename_session(
    session_id: str,
    request: RenameSessionRequest
):
    return service.rename_session(
        session_id,
        request.title
    )


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    return service.delete_session(session_id)