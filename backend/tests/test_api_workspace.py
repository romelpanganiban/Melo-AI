import uuid

from core.settings import settings


def test_registration_creates_default_workspace(client):
    response = client.post(
        "/auth/register",
        json={"email": "workspace-owner@example.com", "password": "correct horse battery staple"},
    )
    assert response.status_code == 201
    registration = response.json()
    assert registration["workspace_id"]

    workspaces = client.get(
        "/workspaces",
        headers={
            "Authorization": f"Bearer {registration['access_token']}",
            "X-Workspace-ID": registration["workspace_id"],
        },
    )
    assert workspaces.status_code == 200
    assert workspaces.json()["workspaces"] == [
        {"id": registration["workspace_id"], "name": "workspace-owner's Workspace", "role": "owner"}
    ]


def test_designated_admin_registration_gets_admin_role(client):
    settings.ADMIN_EMAIL = f"admin-{uuid.uuid4()}@example.com"
    response = client.post(
        "/auth/register",
        json={"email": settings.ADMIN_EMAIL, "password": "correct horse battery staple"},
    )
    assert response.status_code == 201
    registration = response.json()

    workspaces = client.get(
        "/workspaces",
        headers={
            "Authorization": f"Bearer {registration['access_token']}",
            "X-Workspace-ID": registration["workspace_id"],
        },
    )
    assert workspaces.status_code == 200
    assert workspaces.json()["workspaces"][0]["role"] == "admin"


def test_admin_can_access_session_routes(client):
    settings.ADMIN_EMAIL = f"admin-{uuid.uuid4()}@example.com"
    response = client.post(
        "/auth/register",
        json={"email": settings.ADMIN_EMAIL, "password": "correct horse battery staple"},
    )
    assert response.status_code == 201
    registration = response.json()

    sessions = client.get(
        "/sessions",
        headers={
            "Authorization": f"Bearer {registration['access_token']}",
            "X-Workspace-ID": registration["workspace_id"],
        },
    )
    assert sessions.status_code == 200
    assert isinstance(sessions.json().get("sessions", []), list)