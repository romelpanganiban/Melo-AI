from fastapi import APIRouter, status, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy.orm import Session

from services.chat_service import ChatService
from core.errors import ValidationError, ChatServiceError, SessionNotFoundError
from core.validation import validate_message, validate_uuid
from core.logging import logger
from core.settings import settings
from database.connection import get_db
from core.auth import get_current_membership
from core.rate_limit import enforce_request_rate_limit

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Session ID (UUID)")
    message: str = Field(..., min_length=1, max_length=settings.MAX_MESSAGE_LENGTH, description="User message")
    mode: Literal["chat", "ask", "study", "plan", "agent", "auto"] = Field(default="chat", description="Response mode")
    collection_id: str | None = Field(None, description="Optional private knowledge collection ID")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    recent_history: list[dict]
    sources: list[dict] = []  # List of {"filename": str, "relevance": float}


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat(request: ChatRequest, db: Session = Depends(get_db), membership=Depends(get_current_membership), _: None = Depends(enforce_request_rate_limit)):
    """Process a chat message for a session
    
    Args:
        request: ChatRequest containing session_id and message
        db: Database session dependency
    
    Returns:
        ChatResponse with assistant response and recent history
        
    Raises:
        ValidationError: If input validation fails
        SessionNotFoundError: If session not found
        ChatServiceError: If chat processing fails
    """
    try:
        # Validate inputs
        session_id = validate_uuid(request.session_id, field_name="session_id")
        message = validate_message(request.message, max_length=settings.MAX_MESSAGE_LENGTH)
        collection_id = validate_uuid(request.collection_id, field_name="collection_id") if request.collection_id else None
        
        logger.info(
            f"Processing chat message",
            extra={
                "session_id": session_id,
                "message_length": len(message)
            }
        )
        
        # Process message with injected database session
        service = ChatService(workspace_id=membership.workspace_id)
        result = service.process_message(session_id, message, db, mode=request.mode, workspace_id=membership.workspace_id, collection_id=collection_id)
        
        return result
        
    except ValidationError:
        raise
    except SessionNotFoundError:
        raise
    except Exception as e:
        logger.error(
            f"Error processing chat message: {str(e)}",
            extra={"session_id": request.session_id}
        )
        raise ChatServiceError(f"Failed to process message: {str(e)}")


@router.post("/chat/stream", status_code=status.HTTP_200_OK)
def chat_stream(request: ChatRequest, db: Session = Depends(get_db), membership=Depends(get_current_membership), _: None = Depends(enforce_request_rate_limit)):
    """Process a chat message and stream assistant response chunks.

    Response format is newline-delimited JSON (NDJSON) with events:
    - {"type":"chunk","content":"..."}
    - {"type":"done","session_id":"...","response":"..."}
    - {"type":"error","error_code":"...","message":"..."}
    """
    try:
        session_id = validate_uuid(request.session_id, field_name="session_id")
        message = validate_message(request.message, max_length=settings.MAX_MESSAGE_LENGTH)
        collection_id = validate_uuid(request.collection_id, field_name="collection_id") if request.collection_id else None

        logger.info(
            "Processing streaming chat message",
            extra={
                "session_id": session_id,
                "message_length": len(message)
            }
        )

        service = ChatService(workspace_id=membership.workspace_id)
        stream = service.process_message_stream(session_id, message, db, mode=request.mode, workspace_id=membership.workspace_id, collection_id=collection_id)
        return StreamingResponse(stream, media_type="application/x-ndjson")

    except ValidationError:
        raise
    except SessionNotFoundError:
        raise
    except Exception as e:
        logger.error(
            f"Error processing streaming chat message: {str(e)}",
            extra={"session_id": request.session_id}
        )
        raise ChatServiceError(f"Failed to process streaming message: {str(e)}")


@router.get("/history/{session_id}", status_code=status.HTTP_200_OK)
def history(session_id: str, db: Session = Depends(get_db), membership=Depends(get_current_membership)):
    """Get chat history for a session
    
    Args:
        session_id: Session ID (UUID)
        db: Database session dependency
    
    Returns:
        List of messages with role and content
        
    Raises:
        ValidationError: If session_id is invalid
        SessionNotFoundError: If session not found
    """
    try:
        # Validate input
        session_id = validate_uuid(session_id, field_name="session_id")
        
        logger.info(
            f"Retrieving chat history",
            extra={"session_id": session_id}
        )
        
        service = ChatService()
        history = service.get_history(session_id, db, workspace_id=membership.workspace_id)
        
        return {
            "session_id": session_id,
            "messages": history,
            "message_count": len(history)
        }
        
    except ValidationError:
        raise
    except SessionNotFoundError:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving chat history: {str(e)}",
            extra={"session_id": session_id}
        )
        raise ChatServiceError(f"Failed to retrieve history: {str(e)}")
