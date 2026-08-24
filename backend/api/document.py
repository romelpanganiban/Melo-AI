"""Document API endpoints"""

from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile, status
from pydantic import BaseModel, Field

from services.document_service import DocumentService
from services.document_parser import get_document_parser
from core.errors import ValidationError, ChatServiceError
from core.validation import validate_uuid
from core.logging import logger

router = APIRouter()

service = DocumentService()
parser = get_document_parser()
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


class UploadDocumentRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255, description="Document filename")
    file_type: str = Field(..., description="File type: pdf, docx, or txt")
    content: str = Field(..., min_length=1, description="Document content")
    session_id: Optional[str] = Field(None, description="Optional session ID to associate document with")


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    chunk_count: int | None = None
    created_at: str = None


class DocumentDetailResponse(DocumentResponse):
    content: str


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    tokens: int | None = None
    created_at: str | None = None


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str
    top_k: int = Field(default=5, ge=1, le=10)


@router.post("/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
):
    """Extract and store a TXT, PDF, or DOCX upload."""
    try:
        if session_id:
            session_id = validate_uuid(session_id, field_name="session_id")

        content_bytes = file.file.read(MAX_UPLOAD_SIZE + 1)
        if len(content_bytes) > MAX_UPLOAD_SIZE:
            raise ValidationError("File exceeds the 10 MB upload limit")

        file_type, content = parser.parse(file.filename or "", content_bytes)
        return service.upload_document(
            filename=file.filename or "uploaded-document",
            file_type=file_type,
            content=content,
            session_id=session_id,
        )
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Document file upload error: {str(e)}")
        raise ChatServiceError("Failed to extract and upload document")


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(request: UploadDocumentRequest):
    """Upload a new document
    
    Args:
        request: UploadDocumentRequest with file details
        
    Returns:
        DocumentResponse with document id and metadata
        
    Raises:
        ValidationError: If input validation fails
        ChatServiceError: If upload fails
    """
    try:
        # Validate session_id if provided
        if request.session_id:
            request.session_id = validate_uuid(request.session_id, field_name="session_id")
        
        logger.info(
            f"Uploading document",
            extra={
                "doc_filename": request.filename,
                "file_type": request.file_type,
                "session_id": request.session_id
            }
        )
        
        document = service.upload_document(
            filename=request.filename,
            file_type=request.file_type,
            content=request.content,
            session_id=request.session_id
        )
        
        return document
        
    except ValidationError:
        raise
    except Exception as e:
        error_msg = str(e)
        # Hide technical details from user, show friendly message
        if "LogRecord" in error_msg or "overwrite" in error_msg:
            user_friendly_msg = "Failed to save document. Please try again or contact support if the problem persists."
        elif "filename" in error_msg.lower():
            user_friendly_msg = "The filename format is invalid. Please use a valid filename."
        else:
            user_friendly_msg = "Failed to upload document. Please check your file and try again."
        
        logger.error(f"Document upload error: {str(e)}")
        raise ChatServiceError(user_friendly_msg)


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse, status_code=status.HTTP_200_OK)
def get_document(document_id: str):
    """Get document details including content
    
    Args:
        document_id: Document ID (UUID)
        
    Returns:
        DocumentDetailResponse with full document content
        
    Raises:
        ValidationError: If document_id is invalid
        ChatServiceError: If document not found or retrieval fails
    """
    try:
        # Validate input
        document_id = validate_uuid(document_id, field_name="document_id")
        
        logger.info(
            f"Retrieving document",
            extra={"doc_id": document_id}
        )
        
        document = service.get_document(document_id)
        return document
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving document: {str(e)}",
            extra={"doc_id": document_id}
        )
        raise ChatServiceError(f"Failed to retrieve document: {str(e)}")


@router.get("/sessions/{session_id}/documents", status_code=status.HTTP_200_OK)
def get_session_documents(session_id: str):
    """Get all documents for a session
    
    Args:
        session_id: Session ID (UUID)
        
    Returns:
        List of documents metadata
        
    Raises:
        ValidationError: If session_id is invalid
        ChatServiceError: If retrieval fails
    """
    try:
        # Validate input
        session_id = validate_uuid(session_id, field_name="session_id")
        
        logger.info(
            f"Retrieving session documents",
            extra={"session_id": session_id}
        )
        
        documents = service.get_session_documents(session_id)
        
        return {
            "session_id": session_id,
            "documents": documents,
            "count": len(documents)
        }
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving session documents: {str(e)}",
            extra={"session_id": session_id}
        )
        raise ChatServiceError(f"Failed to retrieve session documents: {str(e)}")


@router.get("/documents/{document_id}/chunks", status_code=status.HTTP_200_OK)
def get_document_chunks(document_id: str):
    """Get stored chunks for a document.

    This works offline with the current text-based chunking pipeline.
    """
    try:
        document_id = validate_uuid(document_id, field_name="document_id")

        logger.info(
            "Retrieving document chunks",
            extra={"doc_id": document_id}
        )

        chunks = service.get_document_chunks(document_id)

        return {
            "document_id": document_id,
            "chunks": chunks,
            "count": len(chunks)
        }

    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving document chunks: {str(e)}",
            extra={"doc_id": document_id}
        )
        raise ChatServiceError(f"Failed to retrieve document chunks: {str(e)}")


@router.post("/documents/search", status_code=status.HTTP_200_OK)
def search_documents(request: DocumentSearchRequest):
    """Search indexed documents in a session without asking the language model."""
    try:
        session_id = validate_uuid(request.session_id, field_name="session_id")
        return service.search_documents(request.query, session_id, request.top_k)
    except ValidationError:
        raise
    except Exception as e:
        logger.error("Document search endpoint failed", extra={"session_id": request.session_id})
        raise ChatServiceError("Failed to search documents") from e


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str):
    """Delete a document
    
    Args:
        document_id: Document ID (UUID)
        
    Raises:
        ValidationError: If document_id is invalid
        ChatServiceError: If document not found or deletion fails
    """
    try:
        # Validate input
        document_id = validate_uuid(document_id, field_name="document_id")
        
        logger.info(
            f"Deleting document",
            extra={"doc_id": document_id}
        )
        
        service.delete_document(document_id)
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting document: {str(e)}",
            extra={"doc_id": document_id}
        )
        raise ChatServiceError(f"Failed to delete document: {str(e)}")
