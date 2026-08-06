from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_chat():

    response = client.post(
        "/chat",
        json={
            "session_id": "test-session",
            "message": "Hello Melo"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "response" in data


def test_history():

    response = client.get(
        "/history/test-session"
    )

    assert response.status_code == 200

    assert isinstance(
        response.json(),
        list
    )