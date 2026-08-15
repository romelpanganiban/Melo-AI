from fastapi.testclient import TestClient

from main import app

# Note: client fixture is provided by conftest.py


def test_create_session(client):
    """Test creating a new session"""
    response = client.post("/sessions")

    assert response.status_code == 201  # HTTP 201 Created for POST

    data = response.json()

    assert "id" in data
    assert "title" in data
    assert data["title"].startswith("New Chat") or data["title"].startswith("Chat")


def test_get_sessions(client, test_session_id):
    """Test retrieving all sessions"""
    # Create a session first
    response = client.get("/sessions")

    assert response.status_code == 200

    data = response.json()

    # Response now includes 'sessions' key and 'count'
    assert "sessions" in data
    assert "count" in data
    assert isinstance(data["sessions"], list)
    assert data["count"] >= 1


def test_rename_session(client, test_session_id):
    """Test renaming a session"""
    response = client.put(
        f"/sessions/{test_session_id}",
        json={"title": "Renamed Chat"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == test_session_id
    assert data["title"] == "Renamed Chat"


def test_delete_session(client, test_session_id):
    """Test deleting a session"""
    response = client.delete(f"/sessions/{test_session_id}")

    assert response.status_code == 204  # No Content

    # Verify session is deleted
    get_response = client.get("/sessions")
    data = get_response.json()
    
    session_ids = [s["id"] for s in data["sessions"]]
    assert test_session_id not in session_ids


def test_get_sessions_empty(client):
    """Test getting sessions when none exist"""
    response = client.get("/sessions")

    assert response.status_code == 200

    data = response.json()

    assert "sessions" in data
    assert isinstance(data["sessions"], list)