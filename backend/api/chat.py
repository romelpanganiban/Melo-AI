from fastapi import APIRouter, status, Depends
from fastapi.responses import StreamingResponse, Response
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from xml.sax.saxutils import escape
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
from services.usage_service import enforce_credit_limit

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Session ID (UUID)")
    message: str = Field(..., min_length=1, max_length=settings.MAX_MESSAGE_LENGTH, description="User message")
    mode: Literal["chat", "ask", "study", "plan", "agent", "auto"] = Field(default="chat", description="Response mode")
    collection_id: str | None = Field(None, description="Optional private knowledge collection ID")
    document_id: str | None = Field(None, description="Optional uploaded document ID to use as context")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    recent_history: list[dict]
    sources: list[dict] = []  # List of {"filename": str, "relevance": float}


class PdfExportRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=settings.MAX_MESSAGE_LENGTH * 10)
    filename: str = Field(default="melo-response.pdf", min_length=1, max_length=120)


def enforce_chat_credits(db: Session = Depends(get_db), membership=Depends(get_current_membership)):
    enforce_credit_limit(db, membership.user, membership.workspace_id)


@router.post("/chat/export/pdf", status_code=status.HTTP_200_OK)
def export_response_pdf(request: PdfExportRequest, membership=Depends(get_current_membership)):
    """Render an assistant response as a downloadable PDF."""
    filename = request.filename.replace("/", "_").replace("\\", "_")
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
    )
    styles = getSampleStyleSheet()
    story = []
    for line in request.content.splitlines() or [request.content]:
        story.append(Paragraph(escape(line) or "&nbsp;", styles["BodyText"]))
        story.append(Spacer(1, 6))
    document.build(story)
    return Response(
        content=output.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat(request: ChatRequest, db: Session = Depends(get_db), membership=Depends(get_current_membership), _: None = Depends(enforce_request_rate_limit), __: None = Depends(enforce_chat_credits)):
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
        document_id = validate_uuid(request.document_id, field_name="document_id") if request.document_id else None
        
        logger.info(
            f"Processing chat message",
            extra={
                "session_id": session_id,
                "message_length": len(message)
            }
        )
        
        # Process message with injected database session
        service = ChatService(workspace_id=membership.workspace_id)
        result = service.process_message(session_id, message, db, mode=request.mode, owner_id=membership.user_id, workspace_id=membership.workspace_id, collection_id=collection_id, document_id=document_id)
        
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
def chat_stream(request: ChatRequest, db: Session = Depends(get_db), membership=Depends(get_current_membership), _: None = Depends(enforce_request_rate_limit), __: None = Depends(enforce_chat_credits)):
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
        document_id = validate_uuid(request.document_id, field_name="document_id") if request.document_id else None

        logger.info(
            "Processing streaming chat message",
            extra={
                "session_id": session_id,
                "message_length": len(message)
            }
        )

        service = ChatService(workspace_id=membership.workspace_id)
        stream = service.process_message_stream(session_id, message, db, mode=request.mode, owner_id=membership.user_id, workspace_id=membership.workspace_id, collection_id=collection_id, document_id=document_id)
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
def history(session_id: str, db: Session = Depends(get_db), membership=Depends(get_current_membership), _: None = Depends(enforce_request_rate_limit)):
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
        history = service.get_history(session_id, db, owner_id=membership.user_id, workspace_id=membership.workspace_id)
        
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
