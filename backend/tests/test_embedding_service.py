"""Unit tests for Embedding Service"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from services.embedding_service import EmbeddingService
from core.errors import ChatServiceError


class TestEmbeddingService:
    """Test EmbeddingService class"""
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Fixture for mocked embedding service"""
        with patch('services.embedding_service.SentenceTransformer'):
            service = EmbeddingService()
            return service
    
    def test_initialization(self):
        """Test embedding service initialization"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            # Mock the model
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.array([0.1, 0.2] * 192)  # 384 dims
            mock_model.return_value = mock_instance
            
            service = EmbeddingService(
                model_name="test-model",
                device="cpu"
            )
            
            assert service.model_name == "test-model"
            assert service.device == "cpu"
            assert service.embedding_dim == 384
    
    def test_initialization_error(self):
        """Test initialization error handling"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_model.side_effect = Exception("Model not found")
            
            with pytest.raises(ChatServiceError):
                EmbeddingService()
    
    def test_embed_text_success(self):
        """Test successful text embedding"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            embedding_array = np.array([0.1, 0.2, 0.3, 0.4])
            mock_instance.encode.return_value = embedding_array
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.model = mock_instance
            service.embedding_dim = 4
            
            result = service.embed_text("Test text")
            
            assert isinstance(result, list)
            assert len(result) == 4
            assert result == [0.1, 0.2, 0.3, 0.4]
    
    def test_embed_text_empty(self):
        """Test embedding empty text"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.model = mock_instance
            
            with pytest.raises(ChatServiceError):
                service.embed_text("")
    
    def test_embed_text_whitespace_only(self):
        """Test embedding whitespace-only text"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.model = mock_instance
            
            with pytest.raises(ChatServiceError):
                service.embed_text("   \n\t  ")
    
    def test_embed_text_error(self):
        """Test embedding error handling"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_instance.encode.side_effect = Exception("Encoding failed")
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.model = mock_instance
            
            with pytest.raises(ChatServiceError):
                service.embed_text("Test text")
    
    def test_embed_texts_success(self):
        """Test successful batch text embedding"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            embeddings = np.array([
                [0.1, 0.2, 0.3, 0.4],
                [0.5, 0.6, 0.7, 0.8],
                [0.9, 1.0, 1.1, 1.2]
            ])
            mock_instance.encode.return_value = embeddings
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.model = mock_instance
            service.embedding_dim = 4
            
            texts = ["Text 1", "Text 2", "Text 3"]
            results = service.embed_texts(texts)
            
            assert len(results) == 3
            assert all(isinstance(r, list) for r in results)
            assert all(len(r) == 4 for r in results)
    
    def test_embed_texts_empty_list(self):
        """Test embedding empty text list"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.model = mock_instance
            
            with pytest.raises(ChatServiceError):
                service.embed_texts([])
    
    def test_embed_texts_all_empty(self):
        """Test embedding list with all empty texts"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.model = mock_instance
            
            with pytest.raises(ChatServiceError):
                service.embed_texts(["", "   ", "\n"])
    
    def test_embed_texts_mixed_empty(self):
        """Test embedding list with some empty texts"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            embeddings = np.array([
                [0.1, 0.2, 0.3, 0.4],
                [0.5, 0.6, 0.7, 0.8]
            ])
            mock_instance.encode.return_value = embeddings
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.model = mock_instance
            service.embedding_dim = 4
            
            texts = ["Valid text 1", "", "Valid text 2", "   "]
            results = service.embed_texts(texts)
            
            # Should only embed the valid texts
            assert len(results) == 2
    
    def test_embed_texts_error(self):
        """Test batch embedding error handling"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_instance.encode.side_effect = Exception("Batch encoding failed")
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.model = mock_instance
            
            with pytest.raises(ChatServiceError):
                service.embed_texts(["Text 1", "Text 2"])
    
    def test_embed_query(self):
        """Test query embedding"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            embedding_array = np.array([0.1, 0.2, 0.3, 0.4])
            mock_instance.encode.return_value = embedding_array
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.model = mock_instance
            service.embedding_dim = 4
            
            result = service.embed_query("What is AI?")
            
            assert isinstance(result, list)
            assert len(result) == 4
            mock_instance.encode.assert_called()
    
    def test_embed_query_error(self):
        """Test query embedding error handling"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_instance.encode.side_effect = Exception("Query encoding failed")
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.model = mock_instance
            
            with pytest.raises(ChatServiceError):
                service.embed_query("What is AI?")
    
    def test_get_embedding_dimension(self):
        """Test getting embedding dimension"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.array([0.1] * 384)
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.embedding_dim = 384
            
            dim = service.get_embedding_dimension()
            
            assert dim == 384
    
    def test_model_info(self):
        """Test getting model information"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_instance.encode.return_value = np.array([0.1] * 384)
            mock_instance.get_sentence_embedding_dimension.return_value = 384
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.model = mock_instance
            service.model_name = "test-model"
            service.embedding_dim = 384
            service.device = "cpu"
            
            info = service.model_info()
            
            assert info["model_name"] == "test-model"
            assert info["embedding_dimension"] == 384
            assert info["device"] == "cpu"
    
    def test_consistency_of_embeddings(self):
        """Test that same text produces same embedding"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            test_embedding = np.array([0.1, 0.2, 0.3, 0.4])
            mock_instance.encode.return_value = test_embedding
            mock_model.return_value = mock_instance
            
            service = EmbeddingService()
            service.model = mock_instance
            service.embedding_dim = 4
            
            text = "Test consistency"
            embedding1 = service.embed_text(text)
            embedding2 = service.embed_text(text)
            
            assert embedding1 == embedding2
    
    def test_different_texts_different_embeddings(self):
        """Test that different texts produce different embeddings"""
        with patch('services.embedding_service.SentenceTransformer') as mock_model:
            mock_instance = MagicMock()
            mock_model.return_value = mock_instance
            
            # Set up different returns for different calls
            embeddings = [
                np.array([0.1, 0.2, 0.3, 0.4]),
                np.array([0.5, 0.6, 0.7, 0.8])
            ]
            mock_instance.encode.side_effect = embeddings
            
            service = EmbeddingService()
            service.model = mock_instance
            service.embedding_dim = 4
            
            emb1 = service.embed_text("Text 1")
            emb2 = service.embed_text("Text 2")
            
            assert emb1 != emb2
