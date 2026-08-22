"""Repository layer for database access"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database.models import Session as SessionModel, Message, Settings, Document, DocumentChunk
from core.logging import logger
from core.errors import SessionNotFoundError, ChatServiceError


class SessionRepository:
    """Repository for session data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, title: str = "New Chat") -> SessionModel:
        """Create a new session"""
        try:
            session = SessionModel(id=str(uuid.uuid4()), title=title)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            logger.info(f"Session created: {session.id}")
            return session
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating session: {str(e)}")
            raise ChatServiceError(f"Failed to create session: {str(e)}")
    
    def get_by_id(self, session_id: str) -> Optional[SessionModel]:
        """Get session by ID"""
        try:
            return self.db.query(SessionModel).filter(
                SessionModel.id == session_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting session: {str(e)}")
            raise ChatServiceError(f"Failed to get session: {str(e)}")
    
    def get_all(self) -> List[SessionModel]:
        """Get all sessions, ordered by most recent"""
        try:
            return self.db.query(SessionModel).order_by(
                desc(SessionModel.updated_at)
            ).all()
        except Exception as e:
            logger.error(f"Error getting sessions: {str(e)}")
            raise ChatServiceError(f"Failed to get sessions: {str(e)}")
    
    def update_title(self, session_id: str, title: str) -> SessionModel:
        """Update session title"""
        try:
            session = self.get_by_id(session_id)
            if not session:
                raise SessionNotFoundError(session_id)
            
            session.title = title
            session.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(session)
            logger.info(f"Session updated: {session_id}")
            return session
        except SessionNotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating session: {str(e)}")
            raise ChatServiceError(f"Failed to update session: {str(e)}")
    
    def delete(self, session_id: str) -> None:
        """Delete a session"""
        try:
            session = self.get_by_id(session_id)
            if not session:
                raise SessionNotFoundError(session_id)
            
            self.db.delete(session)
            self.db.commit()
            logger.info(f"Session deleted: {session_id}")
        except SessionNotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting session: {str(e)}")
            raise ChatServiceError(f"Failed to delete session: {str(e)}")


class MessageRepository:
    """Repository for message data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, session_id: str, role: str, content: str, tokens_used: Optional[int] = None, model_name: Optional[str] = None) -> Message:
        """Create a new message"""
        try:
            # Verify session exists
            session = self.db.query(SessionModel).filter(
                SessionModel.id == session_id
            ).first()
            if not session:
                raise SessionNotFoundError(session_id)
            
            message = Message(
                session_id=session_id,
                role=role,
                content=content,
                tokens_used=tokens_used,
                model_name=model_name
            )
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            return message
        except SessionNotFoundError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating message: {str(e)}")
            raise ChatServiceError(f"Failed to create message: {str(e)}")
    
    def get_by_id(self, message_id: int) -> Optional[Message]:
        """Get message by ID"""
        try:
            return self.db.query(Message).filter(Message.id == message_id).first()
        except Exception as e:
            logger.error(f"Error getting message: {str(e)}")
            raise ChatServiceError(f"Failed to get message: {str(e)}")
    
    def get_by_session(self, session_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get all messages for a session"""
        try:
            query = self.db.query(Message).filter(
                Message.session_id == session_id
            ).order_by(Message.created_at)
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            raise ChatServiceError(f"Failed to get messages: {str(e)}")
    
    def get_session_context(self, session_id: str, context_size: int = 10) -> List[Message]:
        """Get recent messages for context (last N messages)"""
        try:
            return self.db.query(Message).filter(
                Message.session_id == session_id
            ).order_by(
                desc(Message.created_at)
            ).limit(context_size).all()[::-1]  # Reverse to get chronological order
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            raise ChatServiceError(f"Failed to get context: {str(e)}")
    
    def count_by_session(self, session_id: str) -> int:
        """Count messages in a session"""
        try:
            return self.db.query(Message).filter(
                Message.session_id == session_id
            ).count()
        except Exception as e:
            logger.error(f"Error counting messages: {str(e)}")
            raise ChatServiceError(f"Failed to count messages: {str(e)}")


class SettingsRepository:
    """Repository for settings data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get(self) -> Settings:
        """Get application settings (creates if not exists)"""
        try:
            settings = self.db.query(Settings).filter(Settings.id == 1).first()
            if not settings:
                settings = Settings(id=1)
                self.db.add(settings)
                self.db.commit()
                self.db.refresh(settings)
            return settings
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error getting settings: {str(e)}")
            raise ChatServiceError(f"Failed to get settings: {str(e)}")
    
    def update(self, **kwargs) -> Settings:
        """Update application settings"""
        try:
            settings = self.get()
            for key, value in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            
            settings.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(settings)
            logger.info("Settings updated")
            return settings
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating settings: {str(e)}")
            raise ChatServiceError(f"Failed to update settings: {str(e)}")


class DocumentRepository:
    """Repository for document data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, filename: str, file_type: str, content: str, session_id: Optional[str] = None) -> Document:
        """Create a new document"""
        try:
            document = Document(
                id=str(uuid.uuid4()),
                filename=filename,
                file_type=file_type,
                content=content,
                session_id=session_id
            )
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            logger.info(f"Document created: {document.id}")
            return document
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating document: {str(e)}")
            raise ChatServiceError(f"Failed to create document: {str(e)}")
    
    def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        try:
            return self.db.query(Document).filter(Document.id == document_id).first()
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            raise ChatServiceError(f"Failed to get document: {str(e)}")
    
    def get_by_session(self, session_id: str) -> List[Document]:
        """Get all documents for a session"""
        try:
            return self.db.query(Document).filter(
                Document.session_id == session_id
            ).order_by(desc(Document.created_at)).all()
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            raise ChatServiceError(f"Failed to get documents: {str(e)}")


class ChunkRepository:
    """Repository for document chunk data access"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        document_id: str,
        chunk_index: int,
        content: str,
        embedding: Optional[str] = None,
        tokens: Optional[int] = None,
    ) -> DocumentChunk:
        """Create a new document chunk"""
        try:
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                chunk_index=chunk_index,
                content=content,
                embedding=embedding,
                tokens=tokens,
            )
            self.db.add(chunk)
            self.db.commit()
            self.db.refresh(chunk)
            return chunk
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating document chunk: {str(e)}")
            raise ChatServiceError(f"Failed to create document chunk: {str(e)}")

    def create_many(self, document_id: str, chunks: list[dict]) -> List[DocumentChunk]:
        """Create multiple chunks for a document"""
        try:
            created_chunks: List[DocumentChunk] = []
            for chunk_data in chunks:
                created_chunks.append(
                    DocumentChunk(
                        id=str(uuid.uuid4()),
                        document_id=document_id,
                        chunk_index=chunk_data["chunk_index"],
                        content=chunk_data["content"],
                        embedding=chunk_data.get("embedding"),
                        tokens=chunk_data.get("tokens"),
                    )
                )

            self.db.add_all(created_chunks)
            self.db.commit()

            for chunk in created_chunks:
                self.db.refresh(chunk)

            return created_chunks
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating document chunks: {str(e)}")
            raise ChatServiceError(f"Failed to create document chunks: {str(e)}")

    def get_by_document(self, document_id: str) -> List[DocumentChunk]:
        """Get all chunks for a document"""
        try:
            return self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index).all()
        except Exception as e:
            logger.error(f"Error getting document chunks: {str(e)}")
            raise ChatServiceError(f"Failed to get document chunks: {str(e)}")

    def count_by_document(self, document_id: str) -> int:
        """Count chunks for a document"""
        try:
            return self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).count()
        except Exception as e:
            logger.error(f"Error counting document chunks: {str(e)}")
            raise ChatServiceError(f"Failed to count document chunks: {str(e)}")

    def delete_by_document(self, document_id: str) -> None:
        """Delete all chunks for a document"""
        try:
            self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).delete(synchronize_session=False)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting document chunks: {str(e)}")
            raise ChatServiceError(f"Failed to delete document chunks: {str(e)}")
