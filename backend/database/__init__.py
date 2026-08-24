"""Database module for Melo-AI"""

from database.connection import init_database, get_db, get_db_session, DatabaseSession, engine, SessionLocal
from database.models import Base, Session as SessionModel, Message, Settings, KnowledgeCollection, Document, DocumentChunk
from database.repositories import (
    SessionRepository,
    MessageRepository,
    SettingsRepository,
    DocumentRepository,
    KnowledgeCollectionRepository,
    ChunkRepository
)

__all__ = [
    "init_database",
    "get_db",
    "get_db_session",
    "DatabaseSession",
    "engine",
    "SessionLocal",
    "Base",
    "SessionModel",
    "Message",
    "Settings",
    "KnowledgeCollection",
    "Document",
    "DocumentChunk",
    "SessionRepository",
    "MessageRepository",
    "SettingsRepository",
    "DocumentRepository",
    "KnowledgeCollectionRepository",
    "ChunkRepository",
]
