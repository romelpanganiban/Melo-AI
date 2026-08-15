"""Unit tests for settings API endpoints"""

from fastapi.testclient import TestClient

from main import app

# Note: client fixture is provided by conftest.py


def test_get_settings(client):
    """Test retrieving current settings"""
    response = client.get("/settings")

    assert response.status_code == 200

    data = response.json()

    # Verify settings structure
    assert "model_name" in data or "model" in data
    assert "provider" in data
    assert "temperature" in data


def test_update_settings(client):
    """Test updating settings"""
    new_settings = {
        "model": "qwen3:32b",
        "provider": "ollama",
        "temperature": 0.5
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