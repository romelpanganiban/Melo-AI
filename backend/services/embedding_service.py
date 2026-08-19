"""Embedding Service for Melo-AI - Generates Vector Embeddings"""

from typing import List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

from core.logging import logger
from core.errors import ChatServiceError
from core.settings import settings


class EmbeddingService:
    """Service for generating text embeddings using SentenceTransformers"""
    
    def __init__(
        self,
        model_name: str = None,
        device: str = None
    ):
        """Initialize embedding service
        
        Args:
            model_name: Model name (default: from settings)
            device: Device to run on ('cpu' or 'cuda', default: from settings)
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.device = device or settings.EMBEDDING_DEVICE
        
        try:
            if SentenceTransformer is None:
                raise ChatServiceError(
                    "SentenceTransformers is unavailable; install the embedding dependencies"
                )

            logger.info(
                f"Loading embedding model",
                extra={
                    "model": self.model_name,
                    "device": self.device
                }
            )
            
            # Load model from Hugging Face
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device
            )
            
            # Get embedding dimension
            dummy_embedding = self.model.encode("test")
            self.embedding_dim = len(dummy_embedding)
            
            logger.info(
                f"Embedding model loaded successfully",
                extra={"embedding_dim": self.embedding_dim}
            )
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise ChatServiceError(f"Embedding model loading failed: {str(e)}")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding
            
        Raises:
            ChatServiceError: If embedding generation fails
        """
        try:
            if not text or not text.strip():
                raise ChatServiceError("Cannot embed empty text")
            
            # Generate embedding
            embedding = self.model.encode(text, convert_to_tensor=False)
            
            # Convert to list of floats
            embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
            
            logger.debug(
                f"Text embedded",
                extra={"text_length": len(text), "embedding_dim": len(embedding_list)}
            )
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise ChatServiceError(f"Embedding generation failed: {str(e)}")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embeddings (each is a list of floats)
            
        Raises:
            ChatServiceError: If embedding generation fails
        """
        try:
            if not texts:
                raise ChatServiceError("Cannot embed empty text list")
            
            # Filter out empty texts
            valid_texts = [t for t in texts if t and t.strip()]
            if not valid_texts:
                raise ChatServiceError("All texts are empty")
            
            # Generate embeddings in batch
            embeddings = self.model.encode(valid_texts, convert_to_tensor=False)
            
            # Convert to list of lists
            embeddings_list = [
                emb.tolist() if isinstance(emb, np.ndarray) else emb
                for emb in embeddings
            ]
            
            logger.debug(
                f"Batch embeddings generated",
                extra={
                    "batch_size": len(valid_texts),
                    "embedding_dim": len(embeddings_list[0]) if embeddings_list else 0
                }
            )
            
            return embeddings_list
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            raise ChatServiceError(f"Batch embedding generation failed: {str(e)}")
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query
        
        Uses the same model but can be optimized for query-specific encoding
        
        Args:
            query: Search query text
            
        Returns:
            Query embedding
        """
        try:
            # For SentenceTransformers, encode query the same way as documents
            # Some models might have separate query/doc encoders in future
            embedding = self.model.encode(query, convert_to_tensor=False)
            return embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {str(e)}")
            raise ChatServiceError(f"Query embedding failed: {str(e)}")
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model
        
        Returns:
            Embedding dimension
        """
        return self.embedding_dim
    
    def model_info(self) -> dict:
        """Get information about the current model
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dim,
            "device": self.device,
            "model_config": str(self.model.get_sentence_embedding_dimension())
        }


# Global embedding service instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service singleton
    
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
