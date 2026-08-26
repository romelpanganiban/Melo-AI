from fastapi.testclient import TestClient


def test_register_login_and_get_current_user(client):
    credentials = {
        "email": "owner@example.com",
        "password": "correct horse battery staple",
    }

    register_response = client.post("/auth/register", json=credentials)
    assert register_response.status_code == 201
    registration = register_response.json()
    assert registration["token_type"] == "bearer"
    assert registration["user_id"]
    assert registration["access_token"]

    login_response = client.post("/auth/login", json=credentials)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    client.headers.update({"Authorization": f"Bearer {token}"})
    me_response = client.get(
        "/auth/me",
    )
    assert me_response.status_code == 200
    assert me_response.json()["user_id"] == registration["user_id"]
    assert me_response.json()["email"] == credentials["email"]
    assert me_response.json()["workspace_id"] == registration["workspace_id"]


def test_duplicate_registration_is_rejected(client):
    credentials = {
        "email": "duplicate@example.com",
        "password": "correct horse battery staple",
    }
    assert client.post("/auth/register", json=credentials).status_code == 201

    response = client.post("/auth/register", json=credentials)
    assert response.status_code == 422
    assert response.json()["error"] == "VALIDATION_ERROR"


def test_invalid_login_is_rejected(client):
    credentials = {
        "email": "missing@example.com",
        "password": "correct horse battery staple",
    }

    response = client.post("/auth/login", json=credentials)
    assert response.status_code == 422
    assert response.json()["error"] == "VALIDATION_ERROR"


def test_me_rejects_missing_or_tampered_token(client):
    client.headers.pop("Authorization")
    assert client.get("/auth/me").status_code == 401
    assert client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid.token"},
    ).status_code == 401


def test_malformed_token_is_rejected_as_unauthorized(client):
    client.headers["Authorization"] = "Bearer %%%%"
    assert client.get("/auth/me").status_code == 401
