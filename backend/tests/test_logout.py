from services.auth_service import verify_access_token


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


def test_revoked_token_is_rejected_by_database_backed_check(test_db):
    from database.models import User, Workspace, WorkspaceMember
    from services.auth_service import create_access_token, revoke_access_token

    user = User(email="persist-revoked@example.com", password_hash="hash")
    test_db.add(user)
    test_db.flush()
    workspace = Workspace(name="Persistent Revocation Workspace")
    test_db.add(workspace)
    test_db.flush()
    test_db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
    test_db.commit()

    token = create_access_token(user.id)
    assert verify_access_token(token, test_db) == user.id

    revoke_access_token(token, test_db)

    assert verify_access_token(token, test_db) is None