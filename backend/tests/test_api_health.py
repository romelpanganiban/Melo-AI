from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] in {"healthy", "degraded"}
    assert "ollama" in data["components"]
    assert "qdrant" in data["components"]