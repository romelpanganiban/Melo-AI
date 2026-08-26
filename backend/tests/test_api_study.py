def test_study_progress_can_be_saved_and_loaded(client, test_session_id):
    response = client.put(
        f"/study/progress/{test_session_id}",
        json={
            "topic": "Qdrant retrieval",
            "completed_cards": 3,
            "quiz_score": 80,
        },
    )

    assert response.status_code == 200
    assert response.json()["completed_cards"] == 3

    loaded = client.get(f"/study/progress/{test_session_id}")
    assert loaded.status_code == 200
    assert loaded.json()["progress"][0]["topic"] == "Qdrant retrieval"


def test_study_progress_rejects_a_session_from_another_workspace(client, test_session_id):
    registration = client.post(
        "/auth/register",
        json={
            "email": "study-owner@example.com",
            "password": "another correct password",
        },
    )
    assert registration.status_code == 201

    response = client.get(
        f"/study/progress/{test_session_id}",
        headers={"Authorization": f"Bearer {registration.json()['access_token']}"},
    )
    assert response.status_code == 422