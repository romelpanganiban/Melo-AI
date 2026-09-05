from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

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


def test_chat_rejects_unknown_mode(client, test_session_id):
    response = client.post(
        "/chat",
        json={
            "session_id": test_session_id,
            "message": "Hello",
            "mode": "unknown",
        },
    )

    assert response.status_code == 422


def test_agent_rejects_missing_read_only_action_input(client):
    response = client.post("/agent/run", json={"actions": [{"action": "read_file"}]})

    assert response.status_code == 422


def test_agent_read_action_uses_workspace_scope(client):
    response = client.post(
        "/agent/run",
        json={"actions": [{"action": "read_file", "path": "backend/services/chat_service.py"}]},
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["result"]["path"] == "backend/services/chat_service.py"


def test_agent_capability_allowlist_can_disable_read_action(client, monkeypatch):
    from core.settings import settings

    monkeypatch.setattr(settings, "AGENT_ALLOWED_CAPABILITIES", {"document:search"})
    response = client.post(
        "/agent/run",
        json={"actions": [{"action": "read_file", "path": "backend/services/chat_service.py"}]},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Agent capability file:read is disabled"


def test_agent_approval_is_bound_to_action_and_target(client):
    response = client.post(
        "/agent/approvals",
        json={"action": "write_file", "target": "notes.md"},
    )

    assert response.status_code == 201
    approval = response.json()
    assert approval["action"] == "write_file"
    assert approval["target"] == "notes.md"


def test_agent_mutation_requires_matching_approval(client, monkeypatch):
    from core.settings import settings

    monkeypatch.setattr(settings, "ENABLE_WORKSPACE_TOOLS", True)
    monkeypatch.setattr(settings, "AGENT_ALLOWED_CAPABILITIES", {"file:write"})
    approval_response = client.post(
        "/agent/approvals",
        json={"action": "write_file", "target": "notes.md"},
    )
    approval_id = approval_response.json()["approval_id"]

    with patch("api.agent.code_service") as code_service:
        response = client.post(
            "/agent/mutate",
            json={
                "action": "write_file",
                "approval_id": approval_id,
                "path": "other.md",
                "content": "blocked",
            },
        )

    assert response.status_code == 403
    code_service.with_workspace.assert_not_called()


def test_agent_mutation_consumes_approval_once(client, monkeypatch):
    from core.settings import settings

    monkeypatch.setattr(settings, "ENABLE_WORKSPACE_TOOLS", True)
    monkeypatch.setattr(settings, "AGENT_ALLOWED_CAPABILITIES", {"file:write"})
    approval_id = client.post(
        "/agent/approvals",
        json={"action": "write_file", "target": "notes.md"},
    ).json()["approval_id"]
    workspace_service = Mock()
    workspace_service.write_file.return_value = {"path": "notes.md", "created": True}

    with patch("api.agent.code_service.with_workspace", return_value=workspace_service):
        request = {
            "action": "write_file",
            "approval_id": approval_id,
            "path": "notes.md",
            "content": "approved",
        }
        first = client.post("/agent/mutate", json=request)
        second = client.post("/agent/mutate", json=request)

    assert first.status_code == 200
    assert second.status_code == 403
    workspace_service.write_file.assert_called_once_with("notes.md", "approved", confirm=True)