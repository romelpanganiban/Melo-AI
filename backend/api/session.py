from fastapi import APIRouter, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.session_service import SessionService
from core.errors import ValidationError, SessionNotFoundError
from core.validation import validate_uuid, validate_session_title
from core.logging import logger
from database.connection import get_db
from core.auth import require_workspace_access_from_header, WorkspaceContext
from core.rate_limit import enforce_request_rate_limit

router = APIRouter(dependencies=[Depends(enforce_request_rate_limit)])


class RenameSessionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="New session title")


class SessionResponse(BaseModel):
    id: str
    title: str


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    db: Session = Depends(get_db),
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
):
    """Create a new chat session
    
    Returns:
        SessionResponse with session id and title
    """
    try:
        logger.info("Creating new session", extra={"workspace_id": workspace_ctx.workspace_id})
        service = SessionService()
        session = service.create_session(db, owner_id=workspace_ctx.user.id, workspace_id=workspace_ctx.workspace_id)
        return session
        
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise


@router.get("/sessions", status_code=status.HTTP_200_OK)
def get_sessions(
    db: Session = Depends(get_db),
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
):
    """Get all sessions
    
    Returns:
        List of sessions with id and title
    """
    try:
        logger.info("Retrieving all sessions", extra={"workspace_id": workspace_ctx.workspace_id})
        service = SessionService()
        sessions = service.get_sessions(db, owner_id=workspace_ctx.user.id, workspace_id=workspace_ctx.workspace_id)
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
    request: RenameSessionRequest,
    db: Session = Depends(get_db),
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
):
    """Rename an existing session
    
    Args:
        session_id: Session ID (UUID)
        request: RenameSessionRequest with new title
        db: Database session dependency
        
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
            extra={"session_id": session_id, "new_title": title, "workspace_id": workspace_ctx.workspace_id}
        )
        
        service = SessionService()
        session = service.rename_session(session_id, title, db, owner_id=workspace_ctx.user.id, workspace_id=workspace_ctx.workspace_id)
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
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
):
    """Delete an existing session
    
    Args:
        session_id: Session ID (UUID)
        db: Database session dependency
        
    Raises:
        ValidationError: If input validation fails
        SessionNotFoundError: If session not found
    """
    try:
        # Validate input
        session_id = validate_uuid(session_id, field_name="session_id")
        
        logger.info(
            f"Deleting session",
            extra={"session_id": session_id, "workspace_id": workspace_ctx.workspace_id}
        )
        
        service = SessionService()
        service.delete_session(session_id, db, owner_id=workspace_ctx.user.id, workspace_id=workspace_ctx.workspace_id)
        
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