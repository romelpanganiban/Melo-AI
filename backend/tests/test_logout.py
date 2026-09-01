def test_logout_without_token_is_rejected(client):
    client.headers.pop("Authorization", None)
    response = client.post("/auth/logout")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_logout_revokes_current_token(client):
    response = client.post(
        "/auth/register",
        json={"email": "logout-owner@example.com", "password": "correct horse battery staple"},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout_response = client.post("/auth/logout", headers=headers)
    assert logout_response.status_code == 200
    assert logout_response.json() == {"logged_out": True}
    assert client.get("/auth/me", headers=headers).status_code == 401