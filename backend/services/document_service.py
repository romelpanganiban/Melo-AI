"""Document service for knowledge base operations"""

from database import DocumentRepository, get_db_session
from core.logging import logger
from core.errors import SessionNotFoundError, ChatServiceError, ValidationError


class DocumentService:
    """Service for handling document operations"""

    def upload_document(self, filename: str, file_type: str, content: str, session_id: str = None) -> dict:
        """Upload a document
        
        Args:
            filename: Name of the document file
            file_type: Type of file (pdf, docx, txt)
            content: Document content text
            session_id: Optional session ID to associate document with
            
        Returns:
            Dictionary with document id and filename
            
        Raises:
            ValidationError: If inputs are invalid
            ChatServiceError: If upload fails
        """
        db = get_db_session()
        try:
            # Validate inputs
            if not filename or not filename.strip():
                raise ValidationError("filename is required")
            
            if file_type not in ["pdf", "docx", "txt"]:
                raise ValidationError("file_type must be 'pdf', 'docx', or 'txt'")
            
            if not content or not content.strip():
                raise ValidationError("content is required")
            
            repo = DocumentRepository(db)
            document = repo.create(
                filename=filename,
                file_type=file_type,
                content=content,
                session_id=session_id
            )
            
            logger.info(
                f"Document uploaded",
                extra={
                    "document_id": document.id,
                    "filename": filename,
                    "file_type": file_type
                }
            )
            
            return {
                "id": document.id,
                "filename": document.filename,
                "file_type": document.file_type,
                "created_at": document.created_at.isoformat() if document.created_at else None
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise ChatServiceError(f"Failed to upload document: {str(e)}")
        finally:
            db.close()

    def get_document(self, document_id: str) -> dict:
        """Get a document by ID
        
        Args:
            document_id: Document identifier
            
        Returns:
            Dictionary with document details
            
        Raises:
            ChatServiceError: If document not found or retrieval fails
        """
        db = get_db_session()
        try:
            repo = DocumentRepository(db)
            document = repo.get_by_id(document_id)
            
            if not document:
                raise ChatServiceError(f"Document not found: {document_id}")
            
            logger.info(
                f"Document retrieved",
                extra={"document_id": document_id}
            )
            
            return {
                "id": document.id,
                "filename": document.filename,
                "file_type": document.file_type,
                "content": document.content,
                "created_at": document.created_at.isoformat() if document.created_at else None
            }
            
        except ChatServiceError:
            raise
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            raise ChatServiceError(f"Failed to get document: {str(e)}")
        finally:
            db.close()

    def get_session_documents(self, session_id: str) -> list[dict]:
        """Get all documents for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of document dictionaries
            
        Raises:
            ChatServiceError: If retrieval fails
        """
        db = get_db_session()
        try:
            repo = DocumentRepository(db)
            documents = repo.get_by_session(session_id)
            
            logger.info(
                f"Session documents retrieved",
                extra={"session_id": session_id, "count": len(documents)}
            )
            
            return [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None
                }
                for doc in documents
            ]
            
        except Exception as e:
            logger.error(f"Error getting session documents: {str(e)}")
            raise ChatServiceError(f"Failed to get session documents: {str(e)}")
        finally:
            db.close()

    def delete_document(self, document_id: str) -> None:
        """Delete a document
        
        Args:
            document_id: Document identifier
            
        Raises:
            ChatServiceError: If deletion fails
        """
        db = get_db_session()
        try:
            repo = DocumentRepository(db)
            document = repo.get_by_id(document_id)
            
            if not document:
                raise ChatServiceError(f"Document not found: {document_id}")
            
            db.delete(document)
            db.commit()
            
            logger.info(
                f"Document deleted",
                extra={"document_id": document_id}
            )
            
        except ChatServiceError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting document: {str(e)}")
            raise ChatServiceError(f"Failed to delete document: {str(e)}")
        finally:
            db.close()
