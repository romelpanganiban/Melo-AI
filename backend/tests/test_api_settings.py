"""Unit tests for settings API endpoints"""

from fastapi.testclient import TestClient

from main import app
from services.auth_service import create_access_token

# Note: client fixture is provided by conftest.py


def test_settings_requires_workspace_header(test_db, test_user):
    """Workspace-scoped requests must fail closed when no workspace context is supplied."""
    app.dependency_overrides.clear()
    app.dependency_overrides[__import__('database.connection', fromlist=['get_db']).get_db] = lambda: test_db

    with TestClient(
        app,
        headers={
            "Authorization": f"Bearer {create_access_token(test_user.id)}",
        },
    ) as no_workspace_client:
        response = no_workspace_client.get("/settings")

    assert response.status_code == 400
    assert "X-Workspace-ID" in response.json()["detail"]


def test_get_settings(client):
    """Test retrieving current settings"""
    response = client.get("/settings")

    assert response.status_code == 200

    data = response.json()

    # Verify settings structure
    assert "model_name" in data or "model" in data
    assert "provider" in data
    assert "temperature" in data
    assert data["learning_level"] in {"beginner", "intermediate", "advanced"}


def test_update_settings(client):
    """Test updating settings"""
    new_settings = {
        "model": "qwen3:32b",
        "provider": "ollama",
        "temperature": 0.5
        ,"learning_level": "advanced",
        "explanation_style": "detailed",
        "quiz_difficulty": "hard"
    }

    response = client.put(
        "/settings",
        json=new_settings
    )

    assert response.status_code == 200

    data = response.json()

    # Verify settings were updated
    assert data.get("model_name") == new_settings["model"] or \
           data.get("model") == new_settings["model"]
    assert data["temperature"] == new_settings["temperature"]
    assert data["learning_level"] == "advanced"


def test_update_settings_invalid_temperature(client):
    """Test updating settings with invalid temperature"""
    invalid_settings = {
        "model": "qwen3:8b",
        "provider": "ollama",
        "temperature": 10.0  # Out of range
    }

    response = client.put(
        "/settings",
        json=invalid_settings
    )

    # Should return validation error
    assert response.status_code in [400, 422]


def test_update_settings_partial(client):
    """Test updating only some settings"""
    partial_settings = {
        "temperature": 0.8
    }

    response = client.put(
        "/settings",
        json=partial_settings
    )

    assert response.status_code == 200

    data = response.json()

    assert data["temperature"] == 0.8