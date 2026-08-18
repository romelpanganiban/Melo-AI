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
