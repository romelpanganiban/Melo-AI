"""Unit tests for chat service with database backend"""

import pytest
from services.chat_service_db import ChatServiceDB
from database import get_db_session
from database.repositories import SessionRepository


def test_process_message(test_db, test_session_id):
    """Test processing a message with ChatServiceDB"""
    service = ChatServiceDB(test_db)

    result = service.process_message(
        test_session_id,
        "Hello Melo"
    )

    assert "response" in result
    assert "recent_history" in result
    assert "session_id" in result
    assert result["session_id"] == test_session_id
    assert len(result["recent_history"]) >= 1


def test_get_history(test_db, test_session_id):
    """Test retrieving chat history with ChatServiceDB"""
    service = ChatServiceDB(test_db)

    # Send a message first
    service.process_message(test_session_id, "Hello")

    # Get history
    history = service.get_history(test_session_id)

    assert isinstance(history, list)
    assert len(history) >= 2  # User message + assistant response
    
    # Verify message structure
    for msg in history:
        assert "role" in msg
        assert "content" in msg
        assert msg["role"] in ["user", "assistant"]


def test_process_message_invalid_session(test_db):
    """Test processing message for non-existent session"""
    from core.errors import SessionNotFoundError
    
    service = ChatServiceDB(test_db)

    with pytest.raises(SessionNotFoundError):
        service.process_message(
            "invalid-session-id",
            "Hello"
        )


def test_chat_history_persistence(test_db, test_session_id):
    """Test that messages persist in database"""
    from database.repositories import MessageRepository
    
    service = ChatServiceDB(test_db)

    # Process multiple messages
    messages = [
        "Hello",
        "How are you?",
        "Tell me a joke"
    ]

    for msg in messages:
        service.process_message(test_session_id, msg)

    # Verify all messages are in database
    msg_repo = MessageRepository(test_db)
    db_messages = msg_repo.get_by_session(test_session_id)

    # Should have user messages + assistant responses
    assert len(db_messages) >= len(messages)