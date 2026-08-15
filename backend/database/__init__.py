"""Database module for Melo-AI"""

from database.connection import init_database, get_db, get_db_session, DatabaseSession, engine, SessionLocal
from database.models import Base, Session as SessionModel, Message, Settings, Document, DocumentChunk
from database.repositories import (
    SessionRepository,
    MessageRepository,
    SettingsRepository,
    DocumentRepository
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
    "Document",
    "DocumentChunk",
    "SessionRepository",
    "MessageRepository",
    "SettingsRepository",
    "DocumentRepository",
]
