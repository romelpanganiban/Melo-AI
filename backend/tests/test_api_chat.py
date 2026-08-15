from fastapi.testclient import TestClient

from main import app

# Note: client and test_session_id fixtures are provided by conftest.py


def test_chat(client, test_session_id):
    """Test sending a chat message"""
    response = client.post(
        "/chat",
        json={
            "session_id": test_session_id,
            "message": "Hello Melo"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "response" in data
    assert "recent_history" in data
    assert "session_id" in data
    assert isinstance(data["recent_history"], list)


def test_history(client, test_session_id):
    """Test retrieving chat history"""
    # Send a message first
    client.post(
        "/chat",
        json={
            "session_id": test_session_id,
            "message": "Test message"
        }
    )

    # Get history
    response = client.get(f"/history/{test_session_id}")

    assert response.status_code == 200

    data = response.json()

    # Response should have session_id, messages list, and count
    assert "session_id" in data
    assert "messages" in data
    assert "message_count" in data
    assert isinstance(data["messages"], list)
    assert data["message_count"] >= 1


def test_chat_invalid_session(client):
    """Test chat with invalid session ID"""
    response = client.post(
        "/chat",
        json={
            "session_id": "invalid-uuid-format",
            "message": "Hello"
        }
    )

    # Should return 422 (validation error) for invalid UUID format
    assert response.status_code in [422, 400]


def test_history_invalid_session(client):
    """Test history with invalid session ID"""
    response = client.get("/history/invalid-uuid-format")

    # Should return 422 (validation error) for invalid UUID format
    assert response.status_code in [422, 400]