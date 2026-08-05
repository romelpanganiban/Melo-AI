from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_session():

    response = client.post("/sessions")

    assert response.status_code == 200

    data = response.json()

    assert "id" in data
    assert "title" in data


def test_get_sessions():

    response = client.get("/sessions")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)