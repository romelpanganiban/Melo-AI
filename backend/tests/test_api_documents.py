"""API tests for document endpoints."""

from fastapi.testclient import TestClient


def test_upload_document(client, test_session_id):
    response = client.post(
        "/documents",
        json={
            "filename": "api-note.txt",
            "file_type": "txt",
            "content": "This document is stored through the API and chunked offline.",
            "session_id": test_session_id,
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["filename"] == "api-note.txt"
    assert data["file_type"] == "txt"
    assert data["chunk_count"] >= 1
    assert "id" in data


def test_create_collection_and_associate_document(client, test_session_id):
    collection_response = client.post(
        "/collections",
        json={"name": "Project Notes", "description": "Private project knowledge"},
    )

    assert collection_response.status_code == 201
    collection = collection_response.json()

    list_response = client.get("/collections")
    assert list_response.status_code == 200
    assert any(item["id"] == collection["id"] for item in list_response.json()["collections"])

    document_response = client.post(
        "/documents",
        json={
            "filename": "project.txt",
            "file_type": "txt",
            "content": "Project collection content.",
            "session_id": test_session_id,
            "collection_id": collection["id"],
        },
    )

    assert document_response.status_code == 201
    assert document_response.json()["collection_id"] == collection["id"]


def test_upload_rejects_unknown_collection(client, test_session_id):
    response = client.post(
        "/documents",
        json={
            "filename": "unknown-collection.txt",
            "file_type": "txt",
            "content": "This should not be stored.",
            "session_id": test_session_id,
            "collection_id": "00000000-0000-0000-0000-000000000000",
        },
    )

    assert response.status_code == 422


def test_upload_document_file(client, test_session_id):
    response = client.post(
        "/documents/upload",
        files={"file": ("uploaded.txt", b"Uploaded file content.", "text/plain")},
        data={"session_id": test_session_id},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "uploaded.txt"
    assert data["file_type"] == "txt"
    assert data["chunk_count"] >= 1


def test_get_document_and_chunks(client, test_session_id):
    create_response = client.post(
        "/documents",
        json={
            "filename": "chunked.txt",
            "file_type": "txt",
            "content": "Chunk one. Chunk two. Chunk three. Chunk four.",
            "session_id": test_session_id,
        },
    )

    assert create_response.status_code == 201
    document_id = create_response.json()["id"]

    detail_response = client.get(f"/documents/{document_id}")
    assert detail_response.status_code == 200
    detail_data = detail_response.json()
    assert detail_data["id"] == document_id
    assert detail_data["chunk_count"] >= 1
    assert detail_data["content"]

    chunks_response = client.get(f"/documents/{document_id}/chunks")
    assert chunks_response.status_code == 200
    chunks_data = chunks_response.json()
    assert chunks_data["document_id"] == document_id
    assert chunks_data["count"] >= 1
    assert len(chunks_data["chunks"]) >= 1


def test_get_session_documents(client, test_session_id):
    client.post(
        "/documents",
        json={
            "filename": "session-doc.txt",
            "file_type": "txt",
            "content": "A session document for testing the list endpoint.",
            "session_id": test_session_id,
        },
    )

    response = client.get(f"/sessions/{test_session_id}/documents")
    assert response.status_code == 200

    data = response.json()
    assert data["session_id"] == test_session_id
    assert data["count"] >= 1
    assert data["documents"]


def test_search_documents_rejects_invalid_session(client):
    response = client.post(
        "/documents/search",
        json={"session_id": "not-a-uuid", "query": "deployment"},
    )

    assert response.status_code == 422


def test_delete_document(client, test_session_id):
    create_response = client.post(
        "/documents",
        json={
            "filename": "delete-api.txt",
            "file_type": "txt",
            "content": "Delete this document and its chunks.",
            "session_id": test_session_id,
        },
    )
    document_id = create_response.json()["id"]

    delete_response = client.delete(f"/documents/{document_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/documents/{document_id}")
    assert get_response.status_code != 200


def test_user_cannot_read_another_users_document(client, test_session_id):
    create_response = client.post(
        "/documents",
        json={
            "filename": "private.txt",
            "file_type": "txt",
            "content": "Private document content.",
            "session_id": test_session_id,
        },
    )
    assert create_response.status_code == 201
    document_id = create_response.json()["id"]

    login_response = client.post(
        "/auth/register",
        json={
            "email": "document-reader@example.com",
            "password": "another correct password",
        },
    )
    assert login_response.status_code == 201

    response = client.get(
        f"/documents/{document_id}",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
    )
    assert response.status_code == 404
