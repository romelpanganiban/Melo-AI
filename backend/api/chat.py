from fastapi import APIRouter, status, Depends
from fastapi.responses import StreamingResponse, Response
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.platypus import HRFlowable
import re
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
from core.auth import require_workspace_access_from_header, WorkspaceContext
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


def markdown_to_pdf_markup(line: str) -> tuple[str, str]:
    """Convert the common Markdown produced by chat into ReportLab markup."""
    stripped = line.strip()
    if not stripped or re.fullmatch(r"(?:\*{3,}|-{3,}|_{3,})", stripped):
        return "", "separator" if stripped else "spacer"

    heading = re.match(r"^#{1,6}\s+(.+)$", stripped)
    if heading:
        heading_text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", r"\1\2", heading.group(1))
        return f"<b>{escape(heading_text)}</b>", "heading"

    bullet = re.match(r"^[-*]\s+(.+)$", stripped)
    if bullet:
        stripped = f"• {bullet.group(1)}"

    # Standard PDF fonts cannot render emoji reliably; remove them rather than
    # emitting missing-glyph squares in the downloaded document.
    stripped = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF]", "", stripped).strip()
    if not stripped:
        return "", "spacer"

    markup = escape(stripped)
    markup = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda match: f"<b>{match.group(1) or match.group(2)}</b>", markup)
    markup = re.sub(r"`([^`]+)`", lambda match: f"<font name=\"Courier\">{escape(match.group(1))}</font>", markup)
    markup = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<link href="\2" color="#0f766e"><u>\1</u></link>', markup)
    return markup, "bullet" if stripped.startswith("• ") else "body"


def enforce_chat_credits(db: Session = Depends(get_db), workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header())):
    enforce_credit_limit(db, workspace_ctx.user, workspace_ctx.workspace_id)


@router.post("/chat/export/pdf", status_code=status.HTTP_200_OK)
def export_response_pdf(
    request: PdfExportRequest,
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
):
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
        markup, line_type = markdown_to_pdf_markup(line)
        if line_type == "separator":
            story.append(HRFlowable(width="100%", thickness=0.6, color="#cbd5d1", spaceBefore=7, spaceAfter=7))
        elif line_type == "heading":
            story.append(Paragraph(markup, styles["Heading2"]))
        elif line_type == "spacer":
            story.append(Spacer(1, 8))
        else:
            story.append(Paragraph(markup or "&nbsp;", styles["BodyText"]))
            story.append(Spacer(1, 6))
    document.build(story)
    return Response(
        content=output.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    _: None = Depends(enforce_request_rate_limit),
    __: None = Depends(enforce_chat_credits),
):
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
                "message_length": len(message),
                "workspace_id": workspace_ctx.workspace_id,
            }
        )
        
        # Process message with injected database session
        service = ChatService(workspace_id=workspace_ctx.workspace_id)
        result = service.process_message(session_id, message, db, mode=request.mode, owner_id=workspace_ctx.user.id, workspace_id=workspace_ctx.workspace_id, collection_id=collection_id, document_id=document_id)
        
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
def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    _: None = Depends(enforce_request_rate_limit),
    __: None = Depends(enforce_chat_credits),
):
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
                "message_length": len(message),
                "workspace_id": workspace_ctx.workspace_id,
            }
        )

        service = ChatService(workspace_id=workspace_ctx.workspace_id)
        stream = service.process_message_stream(session_id, message, db, mode=request.mode, owner_id=workspace_ctx.user.id, workspace_id=workspace_ctx.workspace_id, collection_id=collection_id, document_id=document_id)
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
def history(
    session_id: str,
    db: Session = Depends(get_db),
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    _: None = Depends(enforce_request_rate_limit),
):
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
            extra={"session_id": session_id, "workspace_id": workspace_ctx.workspace_id}
        )
        
        service = ChatService()
        history = service.get_history(session_id, db, owner_id=workspace_ctx.user.id, workspace_id=workspace_ctx.workspace_id)
        
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
