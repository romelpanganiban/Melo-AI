"""Document API endpoints"""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from services.document_service import DocumentService
from core.errors import ValidationError, ChatServiceError
from core.validation import validate_uuid
from core.logging import logger

router = APIRouter()

service = DocumentService()


class UploadDocumentRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255, description="Document filename")
    file_type: str = Field(..., description="File type: pdf, docx, or txt")
    content: str = Field(..., min_length=1, description="Document content")
    session_id: str = Field(None, description="Optional session ID to associate document with")


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    created_at: str = None


class DocumentDetailResponse(DocumentResponse):
    content: str


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
                "filename": request.filename,
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
        logger.error(f"Error uploading document: {str(e)}")
        raise ChatServiceError(f"Failed to upload document: {str(e)}")


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
            extra={"document_id": document_id}
        )
        
        document = service.get_document(document_id)
        return document
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving document: {str(e)}",
            extra={"document_id": document_id}
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
            extra={"document_id": document_id}
        )
        
        service.delete_document(document_id)
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting document: {str(e)}",
            extra={"document_id": document_id}
        )
        raise ChatServiceError(f"Failed to delete document: {str(e)}")
