"""Integration tests for database services"""

import pytest

from database.repositories import SessionRepository, MessageRepository
from services.chat_service_db import ChatServiceDB
from core.errors import SessionNotFoundError, ChatServiceError


class TestChatServiceDB:
    """Integration tests for ChatServiceDB"""
    
    def test_process_message_flow(self, test_db, monkeypatch):
        """Test complete message processing flow"""
        # Mock Ollama to avoid actual API calls
        monkeypatch.setattr(
            "services.chat_service_db.OllamaClient.is_available",
            lambda x: False  # Ollama not available
        )
        
        # Create session
        session_repo = SessionRepository(test_db)
        session = session_repo.create(title="Test Chat")
        session_id = session.id  # Store ID before session is detached
        
        # Create chat service
        service = ChatServiceDB(test_db)
        
        # Mock Ollama response
        monkeypatch.setattr(
            "services.chat_service_db.OllamaClient.generate_response",
            lambda *args, **kwargs: "This is a test response"
        )
        
        # Process message
        result = service.process_message(
            session_id,
            "Hello, how are you?"
        )
        
        assert result["response"] == "This is a test response"
        assert "session_id" in result
        assert "recent_history" in result
    
    def test_process_message_invalid_session(self, test_db, monkeypatch):
        """Test processing message with invalid session"""
        monkeypatch.setattr(
            "services.chat_service_db.OllamaClient.is_available",
            lambda x: False
        )
        
        service = ChatServiceDB(test_db)
        
        with pytest.raises(SessionNotFoundError):
            service.process_message("invalid-session-id", "Hello")
    
    def test_get_history(self, test_db, monkeypatch):
        """Test retrieving chat history"""
        monkeypatch.setattr(
            "services.chat_service_db.OllamaClient.is_available",
            lambda x: False
        )
        
        # Create session and add messages
        session_repo = SessionRepository(test_db)
        session = session_repo.create()
        session_id = session.id  # Store ID
        
        msg_repo = MessageRepository(test_db)
        msg_repo.create(session_id, "user", "Hello")
        msg_repo.create(session_id, "assistant", "Hi there")
        
        # Get history
        service = ChatServiceDB(test_db)
        history = service.get_history(session_id)
        
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi there"
    
    def test_get_history_invalid_session(self, test_db, monkeypatch):
        """Test getting history for invalid session"""
        monkeypatch.setattr(
            "services.chat_service_db.OllamaClient.is_available",
            lambda x: False
        )
        
        service = ChatServiceDB(test_db)
        
        with pytest.raises(SessionNotFoundError):
            service.get_history("invalid-session-id")
    
    def test_messages_persist_across_queries(self, test_db):
        """Test that messages persist in database across queries"""
        # Create session and add message
        session_repo = SessionRepository(test_db)
        session = session_repo.create()
        session_id = session.id
        
        msg_repo = MessageRepository(test_db)
        msg_repo.create(session_id, "user", "First message")
        msg_repo.create(session_id, "assistant", "First response")
        
        # Query again - should still exist
        messages = msg_repo.get_by_session(session_id)
        assert len(messages) == 2
        
        # Add more messages
        msg_repo.create(session_id, "user", "Second message")
        msg_repo.create(session_id, "assistant", "Second response")
        
        # Verify total count
        messages = msg_repo.get_by_session(session_id)
        assert len(messages) == 4


class TestSessionRepository:
    """Integration tests for SessionRepository"""
    
    def test_create_and_retrieve(self, test_db):
        """Test creating and retrieving sessions"""
        repo = SessionRepository(test_db)
        
        # Create session
        session = repo.create(title="Test Session")
        session_id = session.id
        
        # Retrieve session
        retrieved = repo.get_by_id(session_id)
        
        assert retrieved is not None
        assert retrieved.id == session_id
        assert retrieved.title == "Test Session"
    
    def test_update_title(self, test_db):
        """Test updating session title"""
        repo = SessionRepository(test_db)
        
        # Create and update
        session = repo.create(title="Original")
        session_id = session.id
        
        updated = repo.update_title(session_id, "Updated")
        
        assert updated.title == "Updated"
        
        # Verify in database
        retrieved = repo.get_by_id(session_id)
        assert retrieved.title == "Updated"
    
    def test_delete_session(self, test_db):
        """Test deleting a session"""
        repo = SessionRepository(test_db)
        
        # Create and delete
        session = repo.create()
        session_id = session.id
        
        repo.delete(session_id)
        
        # Verify deleted
        retrieved = repo.get_by_id(session_id)
        assert retrieved is None


class TestMessageRepository:
    """Integration tests for MessageRepository"""
    
    def test_create_and_retrieve_messages(self, test_db):
        """Test creating and retrieving messages"""
        # Create session first
        session_repo = SessionRepository(test_db)
        session = session_repo.create()
        session_id = session.id
        
        # Create messages
        msg_repo = MessageRepository(test_db)
        msg1 = msg_repo.create(session_id, "user", "Hello")
        msg2 = msg_repo.create(session_id, "assistant", "Hi")
        
        # Retrieve
        messages = msg_repo.get_by_session(session_id)
        
        assert len(messages) == 2
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi"
    
    def test_get_by_session_ordering(self, test_db):
        """Test messages are ordered by creation time"""
        session_repo = SessionRepository(test_db)
        session = session_repo.create()
        session_id = session.id
        
        msg_repo = MessageRepository(test_db)
        msg_repo.create(session_id, "user", "First")
        msg_repo.create(session_id, "assistant", "Second")
        msg_repo.create(session_id, "user", "Third")
        
        messages = msg_repo.get_by_session(session_id)
        
        assert len(messages) == 3
        assert messages[0].content == "First"
        assert messages[1].content == "Second"
        assert messages[2].content == "Third"
