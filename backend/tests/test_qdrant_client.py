"""Unit tests for Qdrant client"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.qdrant_client import QdrantVectorClient
from core.errors import ChatServiceError


class TestQdrantVectorClient:
    """Test QdrantVectorClient class"""
    
    @pytest.fixture
    def mock_qdrant_client(self):
        """Fixture for mocked Qdrant client"""
        with patch('services.qdrant_client.QdrantClient'):
            from services.qdrant_client import QdrantVectorClient
            client = QdrantVectorClient()
            return client
    
    def test_initialization(self):
        """Test Qdrant client initialization"""
        with patch('services.qdrant_client.QdrantClient'):
            client = QdrantVectorClient(
                url="http://localhost:6333",
                collection_name="test_collection",
                vector_size=384
            )
            
            assert client.url == "http://localhost:6333"
            assert client.collection_name == "test_collection"
            assert client.vector_size == 384
    
    def test_is_available_success(self):
        """Test is_available when server responds"""
        with patch('services.qdrant_client.QdrantClient') as mock_qdrant:
            mock_instance = MagicMock()
            mock_instance.get_collections.return_value = Mock(collections=[])
            mock_qdrant.return_value = mock_instance
            
            client = QdrantVectorClient()
            client.client = mock_instance
            
            assert client.is_available() is True
            mock_instance.get_collections.assert_called_once()
    
    def test_is_available_failure(self):
        """Test is_available when server is down"""
        with patch('services.qdrant_client.QdrantClient') as mock_qdrant:
            mock_instance = MagicMock()
            mock_instance.get_collections.side_effect = Exception("Connection refused")
            mock_qdrant.return_value = mock_instance
            
            client = QdrantVectorClient()
            client.client = mock_instance
            
            assert client.is_available() is False
    
    def test_create_collection_success(self):
        """Test successful collection creation"""
        with patch('services.qdrant_client.QdrantClient') as mock_qdrant:
            mock_instance = MagicMock()
            mock_instance.get_collections.return_value = Mock(collections=[])
            mock_qdrant.return_value = mock_instance
            
            client = QdrantVectorClient()
            client.client = mock_instance
            
            result = client.create_collection()
            
            assert result is True
            mock_instance.create_collection.assert_called_once()
    
    def test_create_collection_already_exists(self):
        """Test collection creation when it already exists"""
        with patch('services.qdrant_client.QdrantClient') as mock_qdrant:
            mock_instance = MagicMock()
            existing_collection = Mock()
            existing_collection.name = "melo_documents"
            mock_instance.get_collections.return_value = Mock(
                collections=[existing_collection]
            )
            mock_qdrant.return_value = mock_instance
            
            client = QdrantVectorClient()
            client.client = mock_instance
            
            result = client.create_collection()
            
            assert result is True
            # create_collection should not be called if collection exists
            mock_instance.create_collection.assert_not_called()
    
    def test_create_collection_error(self):
        """Test collection creation error handling"""
        with patch('services.qdrant_client.QdrantClient') as mock_qdrant:
            mock_instance = MagicMock()
            mock_instance.get_collections.side_effect = Exception("DB error")
            mock_qdrant.return_value = mock_instance
            
            client = QdrantVectorClient()
            client.client = mock_instance
            
            with pytest.raises(ChatServiceError):
                client.create_collection()
    
    def test_upsert_vector_success(self):
        """Test successful vector upsert"""
        with patch('services.qdrant_client.QdrantClient') as mock_qdrant:
            mock_instance = MagicMock()
            mock_qdrant.return_value = mock_instance
            
            client = QdrantVectorClient()
            client.client = mock_instance
            
            embedding = [0.1, 0.2, 0.3, 0.4]
            payload = {"content": "test", "source": "unit_test"}
            
            result = client.upsert_vector(
                document_id="doc-123",
                chunk_index=0,
                embedding=embedding,
                payload=payload
            )
            
            assert result is True
            mock_instance.upsert.assert_called_once()
    
    def test_upsert_vector_error(self):
        """Test vector upsert error handling"""
        with patch('services.qdrant_client.QdrantClient') as mock_qdrant:
            mock_instance = MagicMock()
            mock_instance.upsert.side_effect = Exception("Upsert failed")
            mock_qdrant.return_value = mock_instance
            
            client = QdrantVectorClient()
            client.client = mock_instance
            
            with pytest.raises(ChatServiceError):
                client.upsert_vector(
                    document_id="doc-123",
                    chunk_index=0,
                    embedding=[0.1, 0.2],
                    payload={"content": "test"}
                )
    
    def test_search_success(self):
        """Test successful vector search"""
        with patch('services.qdrant_client.QdrantClient') as mock_qdrant:
            mock_instance = MagicMock()
            
            # Mock search result
            mock_search_result = [
                Mock(
                    score=0.85,
                    payload={
                        "document_id": "doc-123",
                        "chunk_index": 0,
                        "content": "Test content"
                    }
                )
            ]
            mock_instance.query_points.return_value = Mock(points=mock_search_result)
            mock_qdrant.return_value = mock_instance
            
            client = QdrantVectorClient()
            client.client = mock_instance
            
            results = client.search(
                query_embedding=[0.1, 0.2, 0.3],
                limit=5
            )
            
            assert len(results) == 1
            assert results[0]["similarity_score"] == 0.85
            assert results[0]["document_id"] == "doc-123"
    
    def test_search_no_results(self):
        """Test search with no results"""
        with patch('services.qdrant_client.QdrantClient') as mock_qdrant:
            mock_instance = MagicMock()
            mock_instance.query_points.return_value = Mock(points=[])
            mock_qdrant.return_value = mock_instance
            
            client = QdrantVectorClient()
            client.client = mock_instance
            
            results = client.search(
                query_embedding=[0.1, 0.2, 0.3],
                limit=5
            )
            
            assert len(results) == 0
    
    def test_delete_vectors_success(self):
        """Test successful vector deletion"""
        with patch('services.qdrant_client.QdrantClient') as mock_qdrant:
            mock_instance = MagicMock()
            mock_qdrant.return_value = mock_instance
            
            client = QdrantVectorClient()
            client.client = mock_instance
            
            result = client.delete_vectors("doc-123")
            
            assert result is True
            mock_instance.delete.assert_called_once()
    
    def test_get_collection_info(self):
        """Test getting collection info"""
        with patch('services.qdrant_client.QdrantClient') as mock_qdrant:
            mock_instance = MagicMock()
            mock_info = Mock(points_count=100)
            mock_info.name = "melo_documents"
            mock_instance.get_collection.return_value = mock_info
            mock_qdrant.return_value = mock_instance
            
            client = QdrantVectorClient()
            client.client = mock_instance
            
            info = client.get_collection_info()
            
            assert info["name"] == "melo_documents"
            assert info["points_count"] == 100
    
    def test_health_check_healthy(self):
        """Test health check when system is healthy"""
        with patch('services.qdrant_client.QdrantClient') as mock_qdrant:
            mock_instance = MagicMock()
            mock_instance.get_collections.return_value = Mock(collections=[])
            mock_info = Mock(name="melo_documents", points_count=50)
            mock_instance.get_collection.return_value = mock_info
            mock_qdrant.return_value = mock_instance
            
            client = QdrantVectorClient()
            client.client = mock_instance
            
            health = client.health_check()
            
            assert health["status"] == "healthy"
            assert "collection_info" in health
    
    def test_health_check_unavailable(self):
        """Test health check when system is unavailable"""
        with patch('services.qdrant_client.QdrantClient') as mock_qdrant:
            mock_instance = MagicMock()
            mock_instance.get_collections.side_effect = Exception("Connection failed")
            mock_qdrant.return_value = mock_instance
            
            client = QdrantVectorClient()
            client.client = mock_instance
            
            health = client.health_check()
            
            assert health["status"] == "unavailable"
