from qdrant_client import QdrantClient
import pytest


def test_qdrant_connection():
    client = QdrantClient(url="http://localhost:6333")

    try:
        client.get_collections()
    except Exception as exc:
        pytest.skip(f"Qdrant is unavailable: {exc}")