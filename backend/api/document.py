"""Document API endpoints"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from services.document_service import DocumentService
from services.document_parser import get_document_parser
from core.errors import ChatServiceError, DocumentNotFoundError, ValidationError
from core.validation import validate_uuid
from core.logging import logger
from core.auth import require_workspace_access_from_header, WorkspaceContext
from core.rate_limit import enforce_request_rate_limit
from core.settings import settings
from core.logging import audit_log

router = APIRouter()

service = DocumentService()
parser = get_document_parser()
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


class UploadDocumentRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255, description="Document filename")
    file_type: str = Field(..., description="File type: pdf, docx, or txt")
    content: str = Field(..., min_length=1, max_length=settings.MAX_DOCUMENT_CONTENT_LENGTH, description="Document content")
    session_id: Optional[str] = Field(None, description="Optional session ID to associate document with")
    collection_id: Optional[str] = Field(None, description="Optional knowledge collection ID")


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    chunk_count: int | None = None
    collection_id: Optional[str] = None
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


class ShareDocumentRequest(BaseModel):
    is_shared: bool = Field(..., description="Whether document should be shared with workspace")


class ShareDocumentResponse(BaseModel):
    id: str
    filename: str
    is_shared: bool
    message: str


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str
    collection_id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=10)


class CollectionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


@router.get("/collections", status_code=status.HTTP_200_OK)
def get_collections(
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    _: None = Depends(enforce_request_rate_limit),
):
    """List named private knowledge collections."""
    return {"collections": service.get_collections(workspace_id=workspace_ctx.workspace_id)}


@router.post("/collections", status_code=status.HTTP_201_CREATED)
def create_collection(
    request: CollectionRequest,
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    _: None = Depends(enforce_request_rate_limit),
):
    """Create a named private knowledge collection."""
    return service.create_collection(
        request.name,
        request.description,
        owner_id=workspace_ctx.user.id,
        workspace_id=workspace_ctx.workspace_id,
    )


@router.post("/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    collection_id: Optional[str] = Form(None),
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    _: None = Depends(enforce_request_rate_limit),
):
    """Extract and store a TXT, PDF, or DOCX upload."""
    try:
        if session_id:
            session_id = validate_uuid(session_id, field_name="session_id")
        if collection_id:
            collection_id = validate_uuid(collection_id, field_name="collection_id")

        content_bytes = file.file.read(MAX_UPLOAD_SIZE + 1)
        if len(content_bytes) > MAX_UPLOAD_SIZE:
            raise ValidationError("File exceeds the 10 MB upload limit")

        file_type, content = parser.parse(file.filename or "", content_bytes)
        return service.upload_document(
            filename=file.filename or "uploaded-document",
            file_type=file_type,
            content=content,
            session_id=session_id,
            collection_id=collection_id,
            owner_id=workspace_ctx.user.id,
            workspace_id=workspace_ctx.workspace_id,
        )
    except ValidationError:
        raise
    except DocumentNotFoundError:
        raise
    except ChatServiceError:
        raise
    except Exception as e:
        import traceback
        error_detail = str(e)
        error_type = type(e).__name__
        logger.error(
            f"Document file upload error: {error_type}: {error_detail}",
            extra={"traceback": traceback.format_exc()}
        )
        # Provide more informative error to frontend
        if "decode" in error_detail.lower() or "encoding" in error_detail.lower():
            raise ChatServiceError("File encoding error. Please ensure the file is UTF-8 encoded text.")
        elif "pdf" in error_detail.lower():
            raise ChatServiceError("PDF parsing failed. The file may be corrupted or encrypted.")
        elif "docx" in error_detail.lower():
            raise ChatServiceError("DOCX parsing failed. The file may be corrupted.")
        else:
            raise ChatServiceError(f"Failed to process file: {error_detail[:100]}")


@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    request: UploadDocumentRequest,
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    _: None = Depends(enforce_request_rate_limit),
):
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
        if request.collection_id:
            request.collection_id = validate_uuid(request.collection_id, field_name="collection_id")
        
        logger.info(
            f"Uploading document",
            extra={
                "doc_filename": request.filename,
                "file_type": request.file_type,
                "session_id": request.session_id,
                "workspace_id": workspace_ctx.workspace_id,
            }
        )
        audit_log(
            "document.upload",
            user_id=str(workspace_ctx.user.id),
            workspace_id=str(workspace_ctx.workspace_id),
            document_name=request.filename,
            session_id=request.session_id,
            file_type=request.file_type,
            outcome="success",
        )
        
        document = service.upload_document(
            filename=request.filename,
            file_type=request.file_type,
            content=request.content,
            session_id=request.session_id,
            collection_id=request.collection_id,
            owner_id=workspace_ctx.user.id,
            workspace_id=workspace_ctx.workspace_id,
        )
        
        return document
        
    except ValidationError:
        raise
    except DocumentNotFoundError:
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
        
        import traceback
        logger.error(
            f"Document upload error: {str(e)}",
            extra={"traceback": traceback.format_exc()}
        )
        raise ChatServiceError(user_friendly_msg)


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse, status_code=status.HTTP_200_OK)
def get_document(
    document_id: str,
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    _: None = Depends(enforce_request_rate_limit),
):
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
            extra={"doc_id": document_id, "workspace_id": workspace_ctx.workspace_id}
        )
        audit_log(
            "document.read",
            user_id=str(workspace_ctx.user.id),
            workspace_id=str(workspace_ctx.workspace_id),
            document_id=str(document_id),
            outcome="success",
        )
        
        document = service.get_document(
            document_id,
            workspace_id=workspace_ctx.workspace_id,
            user_id=workspace_ctx.user.id
        )
        return document
        
    except ValidationError:
        raise
    except DocumentNotFoundError:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving document: {str(e)}",
            extra={"doc_id": document_id}
        )
        raise ChatServiceError(f"Failed to retrieve document: {str(e)}")


@router.get("/sessions/{session_id}/documents", status_code=status.HTTP_200_OK)
def get_session_documents(
    session_id: str,
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    _: None = Depends(enforce_request_rate_limit),
):
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
            extra={"session_id": session_id, "workspace_id": workspace_ctx.workspace_id}
        )
        
        documents = service.get_session_documents(session_id, workspace_id=workspace_ctx.workspace_id)
        
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
def get_document_chunks(
    document_id: str,
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    _: None = Depends(enforce_request_rate_limit),
):
    """Get stored chunks for a document.

    This works offline with the current text-based chunking pipeline.
    """
    try:
        document_id = validate_uuid(document_id, field_name="document_id")

        logger.info(
            "Retrieving document chunks",
            extra={"doc_id": document_id, "workspace_id": workspace_ctx.workspace_id}
        )

        chunks = service.get_document_chunks(
            document_id,
            workspace_id=workspace_ctx.workspace_id,
            user_id=workspace_ctx.user.id,
        )

        return {
            "document_id": document_id,
            "chunks": chunks,
            "count": len(chunks)
        }

    except ValidationError:
        raise
    except DocumentNotFoundError:
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving document chunks: {str(e)}",
            extra={"doc_id": document_id}
        )
        raise ChatServiceError(f"Failed to retrieve document chunks: {str(e)}")


@router.post("/documents/search", status_code=status.HTTP_200_OK)
def search_documents(
    request: DocumentSearchRequest,
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    _: None = Depends(enforce_request_rate_limit),
):
    """Search indexed documents in a session without asking the language model."""
    try:
        session_id = validate_uuid(request.session_id, field_name="session_id")
        collection_id = validate_uuid(request.collection_id, field_name="collection_id") if request.collection_id else None
        return service.search_documents(
            request.query,
            session_id,
            collection_id,
            request.top_k,
            workspace_id=workspace_ctx.workspace_id,
            user_id=workspace_ctx.user.id
        )
    except ValidationError:
        raise
    except Exception as e:
        logger.error("Document search endpoint failed", extra={"session_id": request.session_id})
        raise ChatServiceError("Failed to search documents") from e


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    _: None = Depends(enforce_request_rate_limit),
):
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
            extra={"doc_id": document_id, "workspace_id": workspace_ctx.workspace_id}
        )
        audit_log(
            "document.delete",
            user_id=str(workspace_ctx.user.id),
            workspace_id=str(workspace_ctx.workspace_id),
            document_id=str(document_id),
            outcome="success",
        )
        
        service.delete_document(
            document_id,
            workspace_id=workspace_ctx.workspace_id,
            user_id=workspace_ctx.user.id
        )
        
    except ValidationError:
        raise
    except DocumentNotFoundError:
        raise
    except Exception as e:
        logger.error(
            f"Error deleting document: {str(e)}",
            extra={"doc_id": document_id}
        )
        raise ChatServiceError(f"Failed to delete document: {str(e)}")


@router.post("/documents/{document_id}/share", response_model=ShareDocumentResponse)
def share_document(
    document_id: str,
    request: ShareDocumentRequest,
    workspace_ctx: WorkspaceContext = Depends(require_workspace_access_from_header()),
    _: None = Depends(enforce_request_rate_limit),
    db: Session = Depends(get_db),
):
    """Share or unshare a document with workspace members
    
    Only the document owner can control sharing. Shared documents are readable
    by all workspace members, but only the owner can modify or delete.
    
    Args:
        document_id: Document ID (UUID)
        request: ShareDocumentRequest with is_shared boolean
        
    Returns:
        ShareDocumentResponse with updated sharing status
        
    Raises:
        ValidationError: If document_id is invalid
        ChatServiceError: If document not found or operation fails
    """
    try:
        # Validate input
        document_id = validate_uuid(document_id, field_name="document_id")
        
        # Check authorization - only document owner can share
        from core.authz import AuthorizationPolicy
        authz = AuthorizationPolicy(db)
        decision = authz.authorize_document_share(
            workspace_ctx.user.id,
            document_id,
            workspace_ctx.workspace_id
        )
        
        if not decision.allowed:
            raise HTTPException(status_code=decision.status_code, detail=decision.reason)
        
        logger.info(
            f"{'Sharing' if request.is_shared else 'Unsharing'} document",
            extra={"doc_id": document_id, "workspace_id": workspace_ctx.workspace_id, "is_shared": request.is_shared}
        )
        
        # Update document sharing status
        result = service.share_document(
            document_id,
            is_shared=request.is_shared,
            workspace_id=workspace_ctx.workspace_id,
            user_id=workspace_ctx.user.id
        )
        
        return ShareDocumentResponse(
            id=result["id"],
            filename=result["filename"],
            is_shared=result["is_shared"],
            message=f"Document {'shared with' if request.is_shared else 'unshared from'} workspace"
        )
        
    except ValidationError:
        raise
    except HTTPException:
        raise
    except ChatServiceError:
        raise
    except Exception as e:
        logger.error(
            f"Error sharing document: {str(e)}",
            extra={"doc_id": document_id}
        )
        raise ChatServiceError(f"Failed to share document: {str(e)}")
