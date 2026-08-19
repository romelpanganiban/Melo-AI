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