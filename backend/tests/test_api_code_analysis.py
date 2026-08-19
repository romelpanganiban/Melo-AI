def test_analyze_code_endpoint(client):
    response = client.post(
        "/analysis/code",
        json={"path": "backend/services/code_analysis_service.py"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "python"
    assert "CodeAnalysisService" in data["classes"]


def test_analyze_code_rejects_workspace_escape(client):
    response = client.post(
        "/analysis/code",
        json={"path": "../outside.py"},
    )

    assert response.status_code == 422


def test_read_workspace_file_endpoint(client):
    response = client.post(
        "/files/read",
        json={"path": "backend/services/code_analysis_service.py"},
    )

    assert response.status_code == 200
    assert "class CodeAnalysisService" in response.json()["content"]


def test_write_workspace_file_requires_confirmation(client):
    response = client.post(
        "/files/write",
        json={"path": "backend/tests/write-test.py", "content": "pass\n"},
    )

    assert response.status_code == 422


def test_write_workspace_file_rejects_protected_path(client):
    response = client.post(
        "/files/write",
        json={
            "path": ".env",
            "content": "SECRET=invalid\n",
            "confirm": True,
        },
    )

    assert response.status_code == 422


def test_delete_workspace_file_requires_confirmation(client):
    response = client.request(
        "DELETE",
        "/files",
        json={"path": "backend/tests/write-test.py"},
    )

    assert response.status_code == 422