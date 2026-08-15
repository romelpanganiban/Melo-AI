"""Unit tests for database repositories"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from database.models import Base, Session as SessionModel, Message, Settings
from database.repositories import (
    SessionRepository,
    MessageRepository,
    SettingsRepository
)
from core.errors import SessionNotFoundError, ChatServiceError


# Use in-memory SQLite for testing
@pytest.fixture(scope="function")
def test_db():
    """Create a test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


class TestSessionRepository:
    """Tests for SessionRepository"""
    
    def test_create_session(self, test_db):
        """Test creating a session"""
        repo = SessionRepository(test_db)
        session = repo.create(title="Test Chat")
        
        assert session.id is not None
        assert session.title == "Test Chat"
        assert isinstance(session.created_at, datetime)
    
    def test_get_session_by_id(self, test_db):
        """Test retrieving session by ID"""
        repo = SessionRepository(test_db)
        created = repo.create(title="Test")
        
        retrieved = repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Test"
    
    def test_get_nonexistent_session(self, test_db):
        """Test getting nonexistent session returns None"""
        repo = SessionRepository(test_db)
        result = repo.get_by_id("nonexistent-id")
        assert result is None
    
    def test_get_all_sessions(self, test_db):
        """Test retrieving all sessions"""
        repo = SessionRepository(test_db)
        repo.create(title="Session 1")
        repo.create(title="Session 2")
        repo.create(title="Session 3")
        
        sessions = repo.get_all()
        assert len(sessions) == 3
    
    def test_get_all_sessions_ordered(self, test_db):
        """Test sessions ordered by most recent"""
        repo = SessionRepository(test_db)
        session1 = repo.create(title="Session 1")
        session2 = repo.create(title="Session 2")
        
        sessions = repo.get_all()
        assert sessions[0].id == session2.id  # Most recent first
        assert sessions[1].id == session1.id
    
    def test_update_session_title(self, test_db):
        """Test updating session title"""
        repo = SessionRepository(test_db)
        session = repo.create(title="Original")
        
        updated = repo.update_title(session.id, "Updated Title")
        assert updated.title == "Updated Title"
        assert updated.id == session.id
    
    def test_update_nonexistent_session(self, test_db):
        """Test updating nonexistent session raises error"""
        repo = SessionRepository(test_db)
        with pytest.raises(SessionNotFoundError):
            repo.update_title("nonexistent-id", "New Title")
    
    def test_delete_session(self, test_db):
        """Test deleting a session"""
        repo = SessionRepository(test_db)
        session = repo.create(title="To Delete")
        
        repo.delete(session.id)
        
        retrieved = repo.get_by_id(session.id)
        assert retrieved is None
    
    def test_delete_nonexistent_session(self, test_db):
        """Test deleting nonexistent session raises error"""
        repo = SessionRepository(test_db)
        with pytest.raises(SessionNotFoundError):
            repo.delete("nonexistent-id")


class TestMessageRepository:
    """Tests for MessageRepository"""
    
    def test_create_message(self, test_db):
        """Test creating a message"""
        # Create session first
        session_repo = SessionRepository(test_db)
        session = session_repo.create(title="Test")
        
        msg_repo = MessageRepository(test_db)
        message = msg_repo.create(
            session_id=session.id,
            role="user",
            content="Hello"
        )
        
        assert message.session_id == session.id
        assert message.role == "user"
        assert message.content == "Hello"
    
    def test_create_message_invalid_session(self, test_db):
        """Test creating message with invalid session raises error"""
        msg_repo = MessageRepository(test_db)
        with pytest.raises(SessionNotFoundError):
            msg_repo.create(
                session_id="nonexistent",
                role="user",
                content="Test"
            )
    
    def test_get_message_by_id(self, test_db):
        """Test retrieving message by ID"""
        session_repo = SessionRepository(test_db)
        session = session_repo.create()
        
        msg_repo = MessageRepository(test_db)
        created = msg_repo.create(session.id, "user", "Test")
        
        retrieved = msg_repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.content == "Test"
    
    def test_get_messages_by_session(self, test_db):
        """Test retrieving all messages for a session"""
        session_repo = SessionRepository(test_db)
        session = session_repo.create()
        
        msg_repo = MessageRepository(test_db)
        msg_repo.create(session.id, "user", "Message 1")
        msg_repo.create(session.id, "assistant", "Response 1")
        msg_repo.create(session.id, "user", "Message 2")
        
        messages = msg_repo.get_by_session(session.id)
        assert len(messages) == 3
        assert messages[0].content == "Message 1"
        assert messages[1].content == "Response 1"
    
    def test_count_messages(self, test_db):
        """Test counting messages in session"""
        session_repo = SessionRepository(test_db)
        session = session_repo.create()
        
        msg_repo = MessageRepository(test_db)
        msg_repo.create(session.id, "user", "Msg 1")
        msg_repo.create(session.id, "assistant", "Resp 1")
        
        count = msg_repo.count_by_session(session.id)
        assert count == 2
    
    def test_get_session_context(self, test_db):
        """Test getting recent messages for context"""
        session_repo = SessionRepository(test_db)
        session = session_repo.create()
        
        msg_repo = MessageRepository(test_db)
        for i in range(15):
            msg_repo.create(session.id, "user", f"Message {i}")
        
        context = msg_repo.get_session_context(session.id, context_size=10)
        assert len(context) == 10
        # Should be in chronological order
        assert context[0].content == "Message 5"
        assert context[-1].content == "Message 14"
    
    def test_message_with_tokens(self, test_db):
        """Test creating message with token tracking"""
        session_repo = SessionRepository(test_db)
        session = session_repo.create()
        
        msg_repo = MessageRepository(test_db)
        message = msg_repo.create(
            session.id,
            "assistant",
            "Response",
            tokens_used=150
        )
        
        retrieved = msg_repo.get_by_id(message.id)
        assert retrieved.tokens_used == 150


class TestSettingsRepository:
    """Tests for SettingsRepository"""
    
    def test_get_settings_creates_default(self, test_db):
        """Test getting settings creates default if none exists"""
        repo = SettingsRepository(test_db)
        settings = repo.get()
        
        assert settings.id == 1
        assert settings.model_name == "qwen3:8b"
        assert settings.provider == "ollama"
    
    def test_get_settings_returns_same(self, test_db):
        """Test getting settings returns same instance"""
        repo = SettingsRepository(test_db)
        settings1 = repo.get()
        settings2 = repo.get()
        
        assert settings1.id == settings2.id
    
    def test_update_settings(self, test_db):
        """Test updating settings"""
        repo = SettingsRepository(test_db)
        updated = repo.update(
            model_name="qwen3:32b",
            temperature=0.5
        )
        
        assert updated.model_name == "qwen3:32b"
        assert updated.temperature == 0.5
    
    def test_update_settings_partial(self, test_db):
        """Test partial settings update"""
        repo = SettingsRepository(test_db)
        original = repo.get()
        
        repo.update(temperature=0.3)
        
        updated = repo.get()
        assert updated.temperature == 0.3
        assert updated.model_name == original.model_name  # Unchanged
    
    def test_settings_updated_at(self, test_db):
        """Test settings updated_at timestamp"""
        repo = SettingsRepository(test_db)
        original = repo.get()
        original_time = original.updated_at
        
        updated = repo.update(temperature=0.5)
        
        assert updated.updated_at >= original_time


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
