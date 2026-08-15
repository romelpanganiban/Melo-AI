from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from services.session_service import SessionService
from core.errors import ValidationError, SessionNotFoundError
from core.validation import validate_uuid, validate_session_title
from core.logging import logger

router = APIRouter()

service = SessionService()


class RenameSessionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="New session title")


class SessionResponse(BaseModel):
    id: str
    title: str


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session():
    """Create a new chat session
    
    Returns:
        SessionResponse with session id and title
    """
    try:
        logger.info("Creating new session")
        session = service.create_session()
        return session
        
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise


@router.get("/sessions", status_code=status.HTTP_200_OK)
def get_sessions():
    """Get all sessions
    
    Returns:
        List of sessions with id and title
    """
    try:
        logger.info("Retrieving all sessions")
        sessions = service.get_sessions()
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving sessions: {str(e)}")
        raise


@router.put("/sessions/{session_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK)
def rename_session(
    session_id: str,
    request: RenameSessionRequest
):
    """Rename an existing session
    
    Args:
        session_id: Session ID (UUID)
        request: RenameSessionRequest with new title
        
    Returns:
        Updated SessionResponse
        
    Raises:
        ValidationError: If input validation fails
        SessionNotFoundError: If session not found
    """
    try:
        # Validate inputs
        session_id = validate_uuid(session_id, field_name="session_id")
        title = validate_session_title(request.title)
        
        logger.info(
            f"Renaming session",
            extra={"session_id": session_id, "new_title": title}
        )
        
        session = service.rename_session(session_id, title)
        return session
        
    except ValidationError:
        raise
    except SessionNotFoundError:
        raise
    except Exception as e:
        logger.error(
            f"Error renaming session: {str(e)}",
            extra={"session_id": session_id}
        )
        raise


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str):
    """Delete a session
    
    Args:
        session_id: Session ID (UUID)
        
    Raises:
        ValidationError: If session_id is invalid
        SessionNotFoundError: If session not found
    """
    try:
        # Validate input
        session_id = validate_uuid(session_id, field_name="session_id")
        
        logger.info(
            f"Deleting session",
            extra={"session_id": session_id}
        )
        
        service.delete_session(session_id)
        
    except ValidationError:
        raise
    except SessionNotFoundError:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting session: {str(e)}",
            extra={"session_id": session_id}
        )
        raise