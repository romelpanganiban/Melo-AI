from fastapi import APIRouter

from memory.session_manager import SessionManager

router = APIRouter()

manager = SessionManager()

@router.post("/sessions")
def create_session():
    return manager.create_session()

@router.get("/sessions")
def get_sessions():
    return manager.get_sessions()