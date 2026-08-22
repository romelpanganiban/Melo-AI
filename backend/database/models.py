"""Database models for Melo-AI"""

from sqlalchemy import Column, String, DateTime, Text, Integer, Float, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone
import uuid

Base = declarative_base()


class Session(Base):
    """Chat session model"""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, title={self.title})>"


class Message(Base):
    """Chat message model"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    tokens_used = Column(Integer, nullable=True)  # For tracking API usage
    model_name = Column(String(100), nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="messages")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('ix_messages_session_id_created_at', 'session_id', 'created_at'),
        Index('ix_messages_role', 'role'),
    )
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, session_id={self.session_id}, role={self.role})>"


class Settings(Base):
    """Application settings model"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, default=1)
    model_name = Column(String(100), default="qwen3:8b", nullable=False)
    provider = Column(String(50), default="ollama", nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    top_p = Column(Float, default=0.9, nullable=False)
    top_k = Column(Integer, default=40, nullable=False)
    system_prompt = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self) -> str:
        return f"<Settings(model={self.model_name}, provider={self.provider})>"


class Document(Base):
    """Document model for knowledge base"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # "pdf", "docx", "txt"
    content = Column(Text, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename})>"


class DocumentChunk(Base):
    """Document chunk model for RAG"""
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # JSON array stored as text
    tokens = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    # Indexes
    __table_args__ = (
        Index('ix_document_chunks_document_id_chunk_index', 'document_id', 'chunk_index'),
    )
    
    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id})>"
