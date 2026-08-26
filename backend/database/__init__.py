"""Database module for Melo-AI"""

from database.connection import init_database, get_db, get_db_session, DatabaseSession, engine, SessionLocal
from database.models import Base, User, Workspace, WorkspaceMember, UsageLedger, Session as SessionModel, Message, Settings, KnowledgeCollection, StudyProgress, Document, DocumentChunk
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
    "User",
    "Workspace",
    "WorkspaceMember",
    "UsageLedger",
    "SessionModel",
    "Message",
    "Settings",
    "KnowledgeCollection",
    "StudyProgress",
    "Document",
    "DocumentChunk",
    "SessionRepository",
    "MessageRepository",
    "SettingsRepository",
    "DocumentRepository",
    "KnowledgeCollectionRepository",
    "ChunkRepository",
]
